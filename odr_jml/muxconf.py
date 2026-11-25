"""ODR-DabMux configuration helper: example entries for a Journaline service in
both of the formats ODR-DabMux reads (the boost INFO '.mux' format and JSON),
and a reader for existing configs to suggest free ids."""

import json
import re

from .encoder import msc

DEFAULT_MUX = {
    "service_uid": "srv-journaline", "service_id": "", "label": "Journaline", "short_label": "News",
    "subchannel_uid": "sub-journaline", "subchannel_id": 30, "protection_profile": "EEP_A", "protection": 3,
    "component_uid": "comp-journaline", "dscty": 5,
    # standalone: Journaline is its own data service (its own entry in receivers' station lists)
    # linked: audio services (by uid in the mux config) that also carry it as a secondary component
    "standalone": True, "linked": [],
}


def mux_settings(service):
    m = dict(DEFAULT_MUX)
    m.update(service.get("mux") or {})
    sid = (service.get("id") or 1)
    m["service_uid"] = m["service_uid"] or f"srv-journaline-{sid}"
    return m


def linked_component_uid(m, service_uid):
    return f"{m['component_uid']}-{service_uid}"[:64]


def service_id(m, ensemble):
    if m.get("service_id"):
        return m["service_id"]
    ecc = (ensemble or {}).get("ecc") or "e1"
    eid = (ensemble or {}).get("eid") or "0000"
    return f"{ecc}{eid}{0xA0 + int(m.get('subchannel_id', 0)) % 0x60:02x}"


def snippet(service, ensemble=None):
    """Returns {"info": {section: text}, "json": {section: {uid: {...}}}, "warnings": [...]}"""
    m = mux_settings(service)
    sid = service_id(m, ensemble)
    path = (service.get("output_path") or "/path/to/journaline.dat").replace('"', "")
    warnings = []
    if m["protection_profile"] == "EEP_B" and int(service["bitrate"]) % 32:
        warnings.append(f"EEP_B protection needs a bitrate that is a multiple of 32 kbps - use EEP_A for "
                        f"{service['bitrate']} kbps.")
    if service.get("datagroup_mode"):
        warnings.append("Raw datagroup output is enabled: the file contains MSC data groups, not packets, and "
                        "ODR-DabMux's 'type packet' subchannel cannot read it. Turn it off for normal use.")
    if not service.get("output_path"):
        warnings.append("Set this service's output file first.")
    if not m.get("service_id") and not (ensemble or {}).get("ecc"):
        warnings.append("The service id is a placeholder - set it (32-bit, e.g. e1c185a1) under the mux settings, "
                        "or read your ensemble from your odr-dabmux config.")
    dscty = int(m["dscty"])
    addr = f"0x{int(service['packet_address']):x}"
    linked = [l for l in m.get("linked") or [] if l.get("uid")]
    if not m.get("standalone", True) and not linked:
        warnings.append("This service is neither a separate data service nor attached to an audio station, so "
                        "receivers can't find it. Turn on the separate service or attach it to a station.")
    if linked:
        warnings.append("Put each attached component after that station's audio component in the components "
                        "section, so the audio stays the station's primary component.")

    def comp_json(service_uid, label=None):
        c = {"type": dscty, "service": service_uid, "subchannel": m["subchannel_uid"]}
        if label:
            c["label"] = label
        c.update({"user-applications": {"userapp": "journaline"}, "address": addr, "datagroup": True})
        return c

    def comp_info(uid, service_uid, label=None, note=None):
        lines = [f"{uid} {{"]
        if note:
            lines.append(f"    ; {note}")
        lines.append(f"    ; {'5 = transparent data channel, as used by Journaline receivers' if dscty == 5 else 'data service component type'}")
        lines += [f"    type {dscty}", f"    service {service_uid}", f"    subchannel {m['subchannel_uid']}"]
        if label:
            lines.append(f'    label "{label}"')
        lines += ["    user-applications {", '        userapp "journaline"', "    }", f"    address {addr}",
                  "    datagroup true", "}"]
        return "\n".join(lines)

    js = {"services": {}, "subchannels": {m["subchannel_uid"]: {
        "type": "packet", "bitrate": int(service["bitrate"]), "id": int(m["subchannel_id"]),
        "protection-profile": m["protection_profile"], "protection": int(m["protection"]),
        "inputproto": "file", "inputuri": path}}, "components": {}}
    info_services, info_components = [], []
    if m.get("standalone", True):
        js["services"][m["service_uid"]] = {"id": f"0x{sid}", "label": m["label"], "shortlabel": m["short_label"]}
        js["components"][m["component_uid"]] = comp_json(m["service_uid"])
        info_services.append(f'''{m["service_uid"]} {{
    id 0x{sid}
    label "{m["label"]}"
    shortlabel "{m["short_label"]}"
}}''')
        info_components.append(comp_info(m["component_uid"], m["service_uid"]))
    for l in linked:
        uid = linked_component_uid(m, l["uid"])
        js["components"][uid] = comp_json(l["uid"], m["label"])
        info_components.append(comp_info(uid, l["uid"], m["label"],
                                         f"Journaline for {l.get('label') or l['uid']}: after its audio component"))
    if not js["services"]:
        del js["services"]
    info = {}
    if info_services:
        info["services"] = "\n".join(info_services)
    info["subchannels"] = f'''{m["subchannel_uid"]} {{
    type packet
    bitrate {int(service["bitrate"])}
    id {int(m["subchannel_id"])}
    protection-profile {m["protection_profile"]}
    protection {int(m["protection"])}
    inputproto file
    inputuri "{path}"
}}'''
    if info_components:
        info["components"] = "\n".join(info_components)
    return {"info": info, "json": js, "warnings": warnings,
            "packet_size": msc.packet_size_for(int(service["bitrate"]))}


# --- reading existing configs -----------------------------------------------------------

_TOKEN = re.compile(r'"((?:[^"\\]|\\.)*)"|([{}])|([^\s{};"]+)|(;[^\n]*)|(\n)')


def parse_info(text):
    """Minimal parser for the boost::property_tree INFO format used by .mux files."""
    root = {}
    stack = [root]
    key = None
    line_has_key = False
    for m in _TOKEN.finditer(text):
        quoted, brace, word, comment, nl = m.groups()
        if comment is not None:
            continue
        if nl is not None:
            if key is not None and line_has_key:
                stack[-1].setdefault(key, "")
            key, line_has_key = None, False
            continue
        if brace == "{":
            node = {}
            if key is None:
                raise ValueError("unexpected {")
            stack[-1][key] = node
            stack.append(node)
            key, line_has_key = None, False
        elif brace == "}":
            if key is not None and line_has_key:
                stack[-1].setdefault(key, "")
            if len(stack) == 1:
                raise ValueError("unbalanced }")
            stack.pop()
            key, line_has_key = None, False
        else:
            val = quoted if quoted is not None else word
            if key is None:
                key, line_has_key = val, True
            else:
                stack[-1][key] = val
                key, line_has_key = None, False
    if len(stack) != 1:
        raise ValueError("unbalanced braces")
    return root


def read_config(text):
    """Summarise an ODR-DabMux config (INFO or JSON): ensemble ids, used
    subchannel ids, service ids and packet addresses per subchannel."""
    text = text if isinstance(text, str) else text.decode("utf-8", "replace")
    stripped = text.lstrip()
    if stripped.startswith("{") and stripped.rstrip().endswith("}"):
        try:
            cfg = json.loads(text)
        except ValueError:
            cfg = parse_info(text)
    else:
        cfg = parse_info(text)
    if not isinstance(cfg, dict) or not any(k in cfg for k in ("ensemble", "subchannels", "services")):
        raise ValueError("this does not look like an ODR-DabMux configuration")
    ens = cfg.get("ensemble") or {}

    def hx(v, digits):
        v = str(v or "").strip().lower()
        v = v[2:] if v.startswith("0x") else v
        return v.zfill(digits)[-digits:] if re.fullmatch(r"[0-9a-f]+", v) else ""

    subs = cfg.get("subchannels") or {}
    used_ids = sorted({int(s.get("id")) for s in subs.values() if isinstance(s, dict) and str(s.get("id", "")).isdigit()})
    comps = cfg.get("components") or {}
    addresses = {}
    for c in comps.values():
        if isinstance(c, dict) and c.get("address") not in (None, ""):
            try:
                addresses.setdefault(c.get("subchannel"), []).append(int(str(c["address"]), 0))
            except ValueError:
                pass
    free = None
    if len(used_ids) < 64:
        free = used_ids[-1] + 1 if used_ids and used_ids[-1] < 63 else next(i for i in range(64) if i not in used_ids)
    return {
        "ensemble": {"ecc": hx(ens.get("ecc"), 2), "eid": hx(ens.get("id"), 4), "label": str(ens.get("label", ""))},
        "subchannel_ids": used_ids, "free_subchannel_id": free,
        "services": sorted(str(s.get("id", "")) for s in (cfg.get("services") or {}).values() if isinstance(s, dict)),
        "service_list": [{"uid": k, "id": str(v.get("id", "")), "label": str(v.get("label", ""))}
                         for k, v in (cfg.get("services") or {}).items() if isinstance(v, dict)][:200],
        "packet_subchannels": sorted(k for k, s in subs.items() if isinstance(s, dict) and s.get("type") == "packet"),
        "packet_addresses": addresses,
    }
