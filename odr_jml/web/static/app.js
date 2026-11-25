// MPBNL Journaline WebFrontend web UI. Plain ES module, no build step.
// All DOM is built with h(), which only ever creates text nodes for content,
// so user-provided strings are never parsed as HTML.

/* ============================== utilities ============================== */

const ICONS = {
  brand: [["path", "M4.9 19.1C1 15.2 1 8.8 4.9 4.9M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5M19.1 4.9C23 8.8 23 15.1 19.1 19"], ["circle", 12, 12, 2]],
  grid: [["path", "M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"]],
  layers: [["path", "M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"]],
  activity: [["path", "M22 12h-4l-3 9L9 3l-3 9H2"]],
  import: [["path", "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"]],
  upload: [["path", "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"]],
  code: [["path", "M16 18l6-6-6-6M8 6l-6 6 6 6"]],
  users: [["path", "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"], ["circle", 9, 7, 4]],
  user: [["path", "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"], ["circle", 12, 7, 4]],
  sliders: [["path", "M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"]],
  audit: [["path", "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8"]],
  logout: [["path", "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"]],
  search: [["circle", 11, 11, 8], ["path", "M21 21l-4.35-4.35"]],
  plus: [["path", "M12 5v14M5 12h14"]],
  x: [["path", "M18 6 6 18M6 6l12 12"]],
  check: [["path", "M20 6 9 17l-5-5"]],
  alert: [["path", "M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01"]],
  link: [["path", "M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"]],
  image: [["rect", 3, 3, 18, 18, 2], ["circle", 8.5, 8.5, 1.5], ["path", "M21 15l-5-5L5 21"]],
  refresh: [["path", "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"]],
  trash: [["path", "M3 6h18M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"]],
  folder: [["path", "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"]],
  folderPlus: [["path", "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2zM12 11v6M9 14h6"]],
  file: [["path", "M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9zM13 2v7h7"]],
  calendar: [["rect", 3, 4, 18, 18, 2], ["path", "M16 2v4M8 2v4M3 10h18"]],
  chevronsLeft: [["path", "M11 17l-5-5 5-5M18 17l-5-5 5-5"]],
  chevronsRight: [["path", "M13 17l5-5-5-5M6 17l5-5-5-5"]],
  arrowLeft: [["path", "M19 12H5M12 19l-7-7 7-7"]],
  arrowUp: [["path", "M12 19V5M5 12l7-7 7 7"]],
  copy: [["rect", 9, 9, 13, 13, 2], ["path", "M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"]],
  edit: [["path", "M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"]],
  zap: [["path", "M13 2 3 14h9l-1 8 10-12h-9l1-8z"]],
  shield: [["path", "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"]],
  globe: [["circle", 12, 12, 10], ["path", "M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"]],
  lock: [["rect", 3, 11, 18, 11, 2], ["path", "M7 11V7a5 5 0 0 1 10 0v4"]],
  info: [["circle", 12, 12, 10], ["path", "M12 16v-4M12 8h.01"]],
  menu: [["path", "M3 12h18M3 6h18M3 18h18"]],
  clock: [["circle", 12, 12, 10], ["path", "M12 6v6l4 2"]],
  radio: [["path", "M4.9 19.1C1 15.2 1 8.8 4.9 4.9M19.1 4.9C23 8.8 23 15.1 19.1 19"], ["circle", 12, 12, 2]],
  sun: [["circle", 12, 12, 4], ["path", "M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"]],
  moon: [["path", "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"]],
  monitor: [["rect", 2, 3, 20, 14, 2], ["path", "M8 21h8M12 17v4"]],
  heart: [["path", "M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"]],
  login: [["path", "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"]],
  braces: [["path", "M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1"]],
  play: [["path", "M5 3l14 9-14 9V3z"]],
  news: [["path", "M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2M18 14h-8M15 18h-5M10 6h8v4h-8z"]],
  list: [["path", "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"]],
  type: [["path", "M4 7V4h16v3M9 20h6M12 4v16"]],
  rss: [["path", "M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16"], ["circle", 5, 19, 1]],
  table: [["rect", 3, 3, 18, 18, 2], ["path", "M3 9h18M3 15h18M9 3v18"]],
  chevronRight: [["path", "M9 18l6-6-6-6"]],
  chevronDown: [["path", "M6 9l6 6 6-6"]],
  chevronUp: [["path", "M18 15l-6-6-6 6"]],
  eye: [["path", "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"], ["circle", 12, 12, 3]],
  download: [["path", "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"]],
  bold: [["path", "M6 4h8a4 4 0 0 1 0 8H6zM6 12h9a4 4 0 0 1 0 8H6z"]],
  minus: [["path", "M5 12h14"]],
  cornerDown: [["path", "M9 10l-5 5 5 5M20 4v7a4 4 0 0 1-4 4H4"]],
  wifiOff: [["path", "M1 1l22 22M16.72 11.06A10.94 10.94 0 0 1 19 12.55M5 12.55a10.94 10.94 0 0 1 5.17-2.39M10.71 5.05A16 16 0 0 1 22.58 9M1.42 9a15.91 15.91 0 0 1 4.7-2.88M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01"]],
};

const SVGNS = "http://www.w3.org/2000/svg";
function icon(name) {
  const svg = document.createElementNS(SVGNS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("width", "16");
  svg.setAttribute("height", "16");
  for (const [kind, ...a] of ICONS[name] || []) {
    const el = document.createElementNS(SVGNS, kind);
    if (kind === "path") el.setAttribute("d", a[0]);
    if (kind === "circle") { el.setAttribute("cx", a[0]); el.setAttribute("cy", a[1]); el.setAttribute("r", a[2]); }
    if (kind === "rect") { el.setAttribute("x", a[0]); el.setAttribute("y", a[1]); el.setAttribute("width", a[2]); el.setAttribute("height", a[3]); el.setAttribute("rx", a[4]); }
    svg.appendChild(el);
  }
  return svg;
}

function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") el.className = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else if (k === "value") el.value = v;
      else if (k === "checked") el.checked = !!v;
      else if (k === "disabled") el.disabled = !!v;
      else if (k === "selected") el.selected = !!v;
      else if (k === "ref") v(el);
      else if (k === "style") {
        // via CSSOM: the CSP forbids style attributes but allows this
        for (const decl of String(v).split(";")) {
          const i = decl.indexOf(":");
          if (i > 0) el.style.setProperty(decl.slice(0, i).trim(), decl.slice(i + 1).trim());
        }
      }
      else el.setAttribute(k, v === true ? "" : v);
    }
  }
  append(el, children);
  return el;
}
function append(el, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.appendChild(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}
const put = (el, ...children) => append(el, children);
function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }
function btn(label, opts = {}) {
  return h("button", { class: "btn " + (opts.cls || ""), type: opts.type || "button", onclick: opts.onclick, disabled: opts.disabled, title: opts.title },
    opts.icon ? icon(opts.icon) : null, label);
}
function iconBtn(name, title, onclick) {
  return h("button", { class: "icon-btn", type: "button", title, "aria-label": title, onclick }, icon(name));
}

class ApiError extends Error { constructor(msg, status) { super(msg); this.status = status; } }

async function api(method, url, body, { form = false, quiet = false } = {}) {
  const headers = { "X-Requested-With": "odr-jml" };
  if (S.csrf) headers["X-CSRF-Token"] = S.csrf;
  const opts = { method, headers, credentials: "same-origin" };
  if (body !== undefined) {
    if (form) opts.body = body;
    else { headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  }
  let r;
  try { r = await fetch(url, opts); } catch (e) {
    if (!quiet) toast("Cannot reach the server.", "error");
    throw new ApiError("network", 0);
  }
  let data = null;
  try { data = await r.json(); } catch (e) { /* empty */ }
  if (!r.ok) {
    const msg = (data && data.error) || `Request failed (${r.status})`;
    if (r.status === 401 && S.user) { S.user = null; boot(); }
    if (!quiet) toast(msg, "error");
    throw new ApiError(msg, r.status);
  }
  return data;
}

function toast(msg, kind = "") {
  const t = h("div", { class: "toast " + kind, role: kind === "error" ? "alert" : "status" }, msg);
  document.getElementById("toasts").appendChild(t);
  setTimeout(() => t.remove(), kind === "error" ? 7000 : 4000);
}

function fmtAgo(ts) {
  if (!ts) return "never";
  const s = Math.round(Date.now() / 1000 - ts);
  if (s < 0) return "in " + fmtDur(-s);
  if (s < 45) return "just now";
  return fmtDur(s) + " ago";
}
function fmtDur(s) {
  if (s < 90) return `${Math.max(1, Math.round(s))}s`;
  if (s < 5400) return `${Math.round(s / 60)}m`;
  if (s < 129600) return `${Math.round(s / 3600)}h`;
  return `${Math.round(s / 86400)}d`;
}
function fmtIn(ts) {
  if (!ts) return "—";
  const s = Math.round(ts - Date.now() / 1000);
  return s <= 0 ? "now" : "in " + fmtDur(s);
}
function fmtDate(ts) { return ts ? new Date(ts * 1000).toLocaleString() : "—"; }
function fmtBytes(n) {
  if (n == null) return "—";
  if (n < 1024) return n + " B";
  if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
  return (n / 1048576).toFixed(2) + " MB";
}
function initials(name) {
  const w = (name || "?").trim().split(/\s+/).filter(Boolean);
  return ((w[0] || "?")[0] + (w[1] ? w[1][0] : (w[0] || "").slice(1, 2))).toUpperCase();
}
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

/* ============================== modal helpers ============================== */

function modal({ title, body, foot, wide = false, onclose }) {
  const back = h("div", { class: "modal-back" });
  const close = () => { back.remove(); document.removeEventListener("keydown", esc); onclose && onclose(); };
  const esc = (e) => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", esc);
  const box = h("div", { class: "modal" + (wide ? " wide" : ""), role: "dialog", "aria-modal": "true" },
    h("div", { class: "modal-head" }, h("h2", null, title), h("span", { class: "spacer" }), iconBtn("x", "Close", close)),
    h("div", { class: "modal-body" }, body),
    foot ? h("div", { class: "modal-foot" }, foot) : null);
  back.addEventListener("mousedown", (e) => { if (e.target === back) close(); });
  back.appendChild(box);
  document.body.appendChild(back);
  const first = box.querySelector("input, select, textarea");
  if (first) setTimeout(() => first.focus(), 30);
  return { close, box };
}

function confirmDialog(text, { okText = "Confirm", danger = false, title = "Are you sure?" } = {}) {
  return new Promise((resolve) => {
    let done = false;
    const m = modal({
      title, body: h("p", null, text),
      foot: [btn("Cancel", { onclick: () => m.close() }),
        btn(okText, { cls: danger ? "danger" : "primary", onclick: () => { done = true; m.close(); resolve(true); } })],
      onclose: () => { if (!done) resolve(false); },
    });
  });
}

function showSecret(title, text, secret) {
  const m = modal({
    title, body: h("div", { class: "stack" }, h("p", null, text), codeBlock(secret)),
    foot: btn("Done", { cls: "primary", onclick: () => m.close() }),
  });
}

function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => toast("Copied to clipboard.", "ok"));
  } else {
    const ta = h("textarea", { class: "hidden-copy" });
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); toast("Copied to clipboard.", "ok"); } catch (e) { toast("Copy failed - select the text manually.", "error"); }
    ta.remove();
  }
}

function codeBlock(text) {
  return h("div", { class: "code" }, text, h("span", { class: "copy" }, iconBtn("copy", "Copy", () => copyText(text))));
}

// Server-side file browser (admin only). mode: "dir" | "file" | "save"
function fileBrowser({ title = "Choose a location", mode = "dir", exts = "", start = "/", filename = "" } = {}) {
  return new Promise((resolve) => {
    let cur = null, selected = null, done = false;
    const pathBar = h("div", { class: "fs-path" });
    const list = h("div", { class: "fs-list" });
    const info = h("div", { class: "small muted" });
    const nameInput = mode === "save" ? h("input", { type: "text", class: "mono", value: filename || "journaline.dat" }) : null;
    const chooseBtn = btn(mode === "dir" ? "Use this folder" : mode === "save" ? "Save here" : "Select file", { cls: "primary", onclick: choose });

    async function load(path) {
      let data;
      try { data = await api("GET", `/api/fs?path=${encodeURIComponent(path)}${exts ? "&files=" + encodeURIComponent(exts) : ""}`); }
      catch (e) { if (cur === null && path !== "/") return load("/"); return; }
      cur = data.path; selected = null;
      clear(pathBar);
      const parts = cur.split("/").filter(Boolean);
      pathBar.appendChild(h("button", { onclick: () => load("/") }, "/"));
      parts.forEach((p, i) => {
        pathBar.appendChild(h("button", { onclick: () => load("/" + parts.slice(0, i + 1).join("/")) }, p));
        if (i < parts.length - 1) pathBar.appendChild(h("span", { class: "muted" }, "/"));
      });
      clear(list);
      if (data.parent) list.appendChild(h("div", { class: "fs-item dir", onclick: () => load(data.parent) }, icon("arrowUp"), ".."));
      if (!data.entries.length) list.appendChild(h("div", { class: "fs-item muted" }, "Empty folder"));
      for (const e of data.entries) {
        const full = (cur === "/" ? "" : cur) + "/" + e.name;
        const item = h("div", { class: "fs-item" + (e.dir ? " dir" : "") }, icon(e.dir ? "folder" : "file"),
          h("span", { class: "grow ellipsis" }, e.name), e.dir ? null : h("span", { class: "small muted" }, fmtBytes(e.size)));
        item.addEventListener("click", () => {
          if (e.dir) return load(full);
          list.querySelectorAll(".sel").forEach((x) => x.classList.remove("sel"));
          item.classList.add("sel");
          selected = full;
          if (nameInput) nameInput.value = e.name;
        });
        if (e.dir) item.addEventListener("dblclick", () => load(full));
        list.appendChild(item);
      }
      put(clear(info), data.writable
        ? h("span", { class: "chip green" }, icon("check"), "Writable by the service")
        : h("span", { class: "chip amber" }, icon("lock"), "Not writable by the service user"));
    }
    async function mkdir() {
      const name = prompt("New folder name");
      if (!name) return;
      try { const r = await api("POST", "/api/fs/mkdir", { path: cur, name }); load(r.path); } catch (e) { /* toasted */ }
    }
    function choose() {
      let result = cur;
      if (mode === "file") { if (!selected) return toast("Select a file.", "error"); result = selected; }
      if (mode === "save") {
        const n = nameInput.value.trim();
        if (!n || n.includes("/")) return toast("Enter a file name.", "error");
        result = (cur === "/" ? "" : cur) + "/" + n;
      }
      done = true; m.close(); resolve(result);
    }
    const m = modal({
      title, wide: true,
      body: h("div", { class: "stack" }, pathBar, list, h("div", { class: "row" }, info, h("span", { class: "spacer" }),
        mode !== "file" ? btn("New folder", { cls: "sm ghost", icon: "folderPlus", onclick: mkdir }) : null),
      nameInput ? h("div", { class: "field" }, h("label", null, "File name"), nameInput) : null),
      foot: [btn("Cancel", { onclick: () => m.close() }), chooseBtn],
      onclose: () => { if (!done) resolve(null); },
    });
    const startDir = mode === "save" ? (start || "/").replace(/\/[^/]*$/, "") : start;
    load(startDir || "/");
  });
}

/* ============================== form helpers ============================== */

function field(label, input, { hint, max } = {}) {
  const lbl = h("div", { class: "label-row" }, h("label", null, label));
  if (max && input.tagName !== "SELECT") {
    const count = h("span", { class: "count" });
    const upd = () => { const n = [...(input.value || "")].length; count.textContent = `${n}/${max}`; count.classList.toggle("over", n > max); };
    input.addEventListener("input", upd); upd();
    lbl.appendChild(count);
  }
  return h("div", { class: "field" }, lbl, input, hint ? h("div", { class: "hint" }, hint) : null);
}
const inp = (value, attrs = {}) => h("input", { type: "text", value: value ?? "", ...attrs });
function sel(value, options, attrs = {}) {
  return h("select", attrs, options.map(([v, l]) => h("option", { value: v, selected: String(v) === String(value) }, l)));
}
function toggle(label, checked, attrs = {}) {
  const box = h("input", { type: "checkbox", checked, ...attrs });
  return { el: h("label", { class: "check" }, box, h("span", null, label)), box };
}

/* ============================== app state ============================== */

const S = { user: null, csrf: null, status: null, version: "", muxName: "", collapsed: false, lastBuildId: null, pollTimer: null };

/* ---------- theme (per browser) ---------- */
const THEMES = [["system", "System", "monitor"], ["light", "Light", "sun"], ["dark", "Dark", "moon"]];
function getTheme() {
  try { const t = localStorage.getItem("odrjml.theme"); return t === "light" || t === "dark" ? t : "system"; } catch (e) { return "system"; }
}
function setTheme(t) {
  try { if (t === "system") localStorage.removeItem("odrjml.theme"); else localStorage.setItem("odrjml.theme", t); } catch (e) { /* ignore */ }
  if (t === "system") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = t;
}
function themeToggle() {
  const b = h("button", { class: "icon-btn", type: "button" });
  const draw = () => {
    const [, label, ic] = THEMES.find((x) => x[0] === getTheme());
    clear(b).appendChild(icon(ic));
    b.title = `Theme: ${label} (click to change)`;
    b.setAttribute("aria-label", b.title);
  };
  b.addEventListener("click", () => {
    const i = THEMES.findIndex((x) => x[0] === getTheme());
    setTheme(THEMES[(i + 1) % THEMES.length][0]);
    draw();
  });
  draw();
  return b;
}

function setTitle() {
  document.title = S.muxName ? `${S.muxName} · MPBNL Journaline WebFrontend` : "MPBNL Journaline WebFrontend";
}
try { S.collapsed = localStorage.getItem("odrjml.collapsed") === "1"; } catch (e) { /* ignore */ }

const ROLE_LABEL = { admin: "Administrator", editor: "Editor" };
const isEditor = () => S.user && (S.user.role === "admin" || S.user.role === "editor");
const isAdmin = () => S.user && S.user.role === "admin";
/* ============================== boot / auth ============================== */

async function boot() {
  stopPolling();
  let st;
  try { st = await api("GET", "/api/state", undefined, { quiet: true }); }
  catch (e) { return renderFatal(); }
  S.version = st.version; S.user = st.user; S.csrf = st.csrf; S.muxName = st.mux_name || "";
  setTitle();
  if (st.setup_required) return renderSetupAccount();
  if (!S.user) return renderLogin();
  if (S.user.must_change_pw) return renderForcedPassword();
  if (!st.setup_complete && isAdmin()) return renderWizard(0);
  renderShell();
}

function renderFatal() {
  const cmds = "sudo systemctl status odr-journaline-encoder --no-pager\n" +
    "sudo journalctl -u odr-journaline-encoder -n 50 --no-pager\n" +
    "sudo journalctl -u odr-journaline-encoder-update -n 50 --no-pager";
  authCard(h("div", { class: "stack" }, h("h1", null, "Cannot reach the server"),
    h("p", { class: "lead" }, "The MPBNL Journaline WebFrontend service isn't responding. If an update is installing, give it a minute and retry. Otherwise, check the service on the server:"),
    codeBlock(cmds),
    h("p", { class: "small muted" }, "To start it again: sudo systemctl start odr-journaline-encoder. The Journaline output files keep broadcasting either way."),
    btn("Retry", { cls: "primary block", icon: "refresh", onclick: boot })), true);
}

function brand() {
  return h("div", { class: "brand" },
    h("img", { class: "brand-logo logo-dark", src: "/static/logo-dark.svg", alt: "MPBNL Journaline WebFrontend" }),
    h("img", { class: "brand-logo logo-light", src: "/static/logo-light.svg", alt: "MPBNL Journaline WebFrontend" }),
    S.muxName ? h("div", { class: "mux-name", title: "Multiplex" }, icon("radio"), h("span", { class: "ellipsis" }, S.muxName)) : null);
}

function authCard(children, wide = false) {
  const app = clear(document.getElementById("app"));
  const card = h("div", { class: "auth-card" + (wide ? " wide" : "") }, children);
  app.appendChild(h("div", { class: "auth" }, h("div", { class: "auth-wrap" }, brand(), card,
    h("div", { class: "auth-foot" }, `MPBNL © ${new Date().getFullYear()}`))));
  return card;
}

function renderLogin() {
  const u = inp("", { autocomplete: "username", required: true });
  const p = h("input", { type: "password", autocomplete: "current-password", required: true });
  const err = h("div", { class: "banner red hidden" });
  const submit = btn("Sign in", { cls: "primary lg block", type: "submit", icon: "login" });
  const form = h("form", { class: "stack" }, h("h1", null, "Sign in to the panel"),
    h("p", { class: "lead" }, "Manage your Journaline news services, menus, tickers and feeds."),
    err, field("Username", u), field("Password", p), submit,
    h("p", { class: "auth-help" }, "Forgot your password? Ask an administrator to reset it."));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    submit.disabled = true;
    try { await api("POST", "/api/login", { username: u.value, password: p.value }, { quiet: true }); boot(); }
    catch (ex) { put(clear(err), icon("alert"), ex.message); err.classList.remove("hidden"); p.value = ""; p.focus(); }
    finally { submit.disabled = false; }
  });
  authCard(form);
  u.focus();
}

function renderSetupAccount() {
  const token = inp(new URLSearchParams(location.search).get("token") || "", { class: "mono", autocomplete: "off" });
  const u = inp("admin", { autocomplete: "username" });
  const dn = inp("");
  const p = h("input", { type: "password", autocomplete: "new-password" });
  const p2 = h("input", { type: "password", autocomplete: "new-password" });
  const submit = btn("Create administrator", { cls: "primary lg", type: "submit" });
  const form = h("form", { class: "stack" },
    h("div", { class: "steps" }, h("i", { class: "on" }), h("i"), h("i"), h("i")),
    h("h1", null, "Welcome"), h("p", { class: "muted" }, "Create the first administrator account. The setup token was printed by the installer - you can show it again with ",
      h("code", null, "sudo odr-journaline-encoder setup-token"), "."),
    field("Setup token", token), h("div", { class: "grid-2" }, field("Username", u), field("Display name", dn)),
    h("div", { class: "grid-2" }, field("Password", p, { hint: "At least 10 characters." }), field("Confirm password", p2)), submit);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (p.value !== p2.value) return toast("Passwords do not match.", "error");
    submit.disabled = true;
    try {
      await api("POST", "/api/setup", { token: token.value, username: u.value, display_name: dn.value, password: p.value });
      history.replaceState(null, "", location.pathname);
      boot();
    } catch (ex) { submit.disabled = false; }
  });
  authCard(form, true);
}

function renderForcedPassword() {
  const cur = h("input", { type: "password", autocomplete: "current-password" });
  const p = h("input", { type: "password", autocomplete: "new-password" });
  const p2 = h("input", { type: "password", autocomplete: "new-password" });
  const form = h("form", { class: "stack" }, h("h1", null, "Choose a new password"),
    h("p", { class: "muted" }, "Your password was set by an administrator. Choose your own before continuing."),
    field("Current (temporary) password", cur), field("New password", p, { hint: "At least 10 characters." }), field("Confirm", p2),
    h("div", { class: "row" }, btn("Sign out", { cls: "ghost", onclick: logout }), h("span", { class: "spacer" }), btn("Save password", { cls: "primary", type: "submit" })));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (p.value !== p2.value) return toast("Passwords do not match.", "error");
    try { await api("POST", "/api/account/password", { current: cur.value, new: p.value }); toast("Password changed.", "ok"); boot(); } catch (ex) { /* toasted */ }
  });
  authCard(form);
}

async function logout() {
  try { await api("POST", "/api/logout", {}); } catch (e) { /* ignore */ }
  S.user = null; S.csrf = null;
  location.hash = "";
  boot();
}

/* ============================== shared Journaline helpers ============================== */

const hex4 = (n) => "0x" + Number(n).toString(16).toUpperCase().padStart(4, "0");
const parseJid = (v) => {
  const s = String(v ?? "").trim().toLowerCase();
  if (!s) return null;
  const n = s.startsWith("0x") ? parseInt(s.slice(2), 16) : /[a-f]/.test(s) ? parseInt(s, 16) : parseInt(s, 10);
  return Number.isFinite(n) ? n : NaN;
};
const TYPE_META = {
  menu: { label: "Menu", icon: "menu", cls: "accent", help: "A list of links to other objects - sub-menus and messages." },
  text: { label: "Text message", icon: "file", cls: "blue", help: "A title and a longer text, e.g. a news story." },
  title: { label: "Ticker", icon: "zap", cls: "amber", help: "A single headline that updates on screen at once, e.g. a news ticker." },
  list: { label: "List", icon: "table", cls: "green", help: "Rows with optional columns, e.g. results, prices or a timetable." },
  feed: { label: "RSS feed", icon: "rss", cls: "", help: "Filled automatically from an RSS or Atom feed." },
};
const FEED_MODES = [["menu", "Menu of headlines, each opening the full story"], ["ticker", "Ticker with the latest headline"], ["list", "List of headlines"]];
const MAX_OBJECT = 4092;
const utf8len = (s) => new TextEncoder().encode(s || "").length;

function typeBadge(type, extra = "") {
  const m = TYPE_META[type] || TYPE_META.text;
  return h("span", { class: `type-badge ${m.cls} ${extra}`, title: m.label }, icon(m.icon));
}

function bitrateHint(kbps) {
  const ps = packetSize(kbps);
  return `${kbps} kbps · ${ps}-byte packets`;
}

async function readMuxConfig({ saveEnsemble = false } = {}) {
  // returns the summary of an odr-dabmux config chosen by the user, or null
  return new Promise((resolve) => {
    const file = h("input", { type: "file", accept: ".mux,.info,.conf,.ini,.cfg,.json,text/plain,application/json" });
    let done = false;
    const send = async (fd) => {
      if (saveEnsemble) fd.append("save_ensemble", "1");
      try { const r = await api("POST", "/api/mux/read", fd, { form: true }); done = true; m.close(); resolve(r); } catch (e) { /* toasted */ }
    };
    const m = modal({
      title: "Read your odr-dabmux configuration",
      body: h("div", { class: "stack" }, h("p", { class: "muted" }, "Classic .mux (INFO) or .json configs both work. Nothing is changed in the file - it is only read to fill in your ensemble ids and suggest a free subchannel id."),
        field("Config file", file)),
      foot: [isAdmin() ? btn("Choose on server…", { icon: "folder", onclick: async () => {
        const p = await fileBrowser({ title: "Select odr-dabmux config", mode: "file", exts: "mux,info,conf,ini,cfg,json", start: "/home" });
        if (!p) return;
        const fd = new FormData(); fd.append("path", p); send(fd);
      } }) : null, h("span", { class: "spacer" }), btn("Cancel", { onclick: () => m.close() }),
      btn("Read file", { cls: "primary", icon: "upload", onclick: () => {
        if (!file.files[0]) return toast("Choose a config file.", "error");
        const fd = new FormData(); fd.append("file", file.files[0]); send(fd);
      } })],
      onclose: () => { if (!done) resolve(null); },
    });
  });
}

function muxSnippet(sn, fmt) {
  if (fmt === "json") {
    const text = JSON.stringify(sn.json, null, 4);
    return h("div", { class: "stack tight" }, h("div", { class: "small muted" }, "Merge these into the matching ", h("code", null, "services"), ", ",
      h("code", null, "subchannels"), " and ", h("code", null, "components"), " objects of your .json config:"), codeBlock(text));
  }
  const all = Object.entries(sn.info).map(([sec, b]) => `${sec} {\n${b.split("\n").map((l) => "    " + l).join("\n")}\n}`).join("\n\n");
  return h("div", { class: "stack" },
    Object.entries(sn.info).map(([sec, b]) => h("div", { class: "stack tight" }, h("div", { class: "small muted" }, "Inside the ", h("code", null, sec + " { … }"), " section:"), codeBlock(b))),
    h("details", null, h("summary", { class: "small muted" }, "All three as one block"), h("div", { class: "section-gap" }), codeBlock(all)));
}

function formatSwitch(onchange, initial = "info") {
  let cur = initial;
  try { cur = localStorage.getItem("odrjml.muxfmt") || initial; } catch (e) { /* ignore */ }
  const seg = h("div", { class: "segmented" });
  const draw = () => {
    clear(seg);
    for (const [k, l] of [["info", "Classic .mux"], ["json", "JSON"]]) {
      seg.appendChild(h("button", { type: "button", class: cur === k ? "on" : "", onclick: () => {
        cur = k; try { localStorage.setItem("odrjml.muxfmt", k); } catch (e) { /* ignore */ }
        draw(); onchange(k);
      } }, l));
    }
  };
  draw();
  return { el: seg, get: () => cur };
}

/* ============================== first-run wizard ============================== */

async function renderWizard(step) {
  const steps = h("div", { class: "steps" }, [0, 1, 2, 3].map((i) => h("i", { class: i <= step + 1 ? "on" : "" })));
  if (step === 0) {
    const s = await api("GET", "/api/settings");
    const name = inp(s.mux_name, { maxlength: 64, placeholder: "e.g. North Region DAB" });
    const ecc = inp(s.ensemble.ecc, { class: "mono", placeholder: "e1", maxlength: 2 });
    const eid = inp(s.ensemble.eid, { class: "mono", placeholder: "c185", maxlength: 4 });
    const readBtn = btn("Read from odr-dabmux config…", { cls: "sm", icon: "import", onclick: async () => {
      const r = await readMuxConfig();
      if (!r) return;
      ecc.value = r.ensemble.ecc; eid.value = r.ensemble.eid; if (!name.value) name.value = r.ensemble.label;
      S.muxInfo = r;
      toast(`Found ensemble ${r.ensemble.ecc}.${r.ensemble.eid}; subchannel id ${r.free_subchannel_id} is free.`, "ok");
    } });
    const form = h("form", { class: "stack" }, steps, h("h1", null, "Your multiplex"),
      h("p", { class: "muted" }, "Used to label this panel and to suggest the data service ids for your Journaline services. You can change these later in Settings."),
      h("div", { class: "row" }, readBtn),
      field("Multiplex name", name, { hint: "Shown on the login screen, sidebar and browser tab." }),
      h("div", { class: "grid-2" }, field("ECC", ecc, { hint: "2 hex digits, e.g. e3 for Ireland, e1 for the UK" }), field("EId (ensemble id)", eid, { hint: "4 hex digits" })),
      h("div", { class: "row" }, h("span", { class: "spacer" }), btn("Continue", { cls: "primary", type: "submit" })));
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      try { await api("PUT", "/api/settings", { mux_name: name.value, ensemble: { ecc: ecc.value, eid: eid.value } }); S.muxName = name.value; setTitle(); renderWizard(1); } catch (ex) { /* toasted */ }
    });
    authCard(form, true);
  } else if (step === 1) {
    const existing = await api("GET", "/api/services");
    if (existing.length) { S.wizardService = existing[0].id; return renderWizard(2); }
    const name = inp("", { maxlength: 64, placeholder: "e.g. MPBNL News" });
    const provider = inp("", { maxlength: 64, placeholder: "Optional - who runs it" });
    const path = inp("", { class: "mono", placeholder: "/home/odr/ODR-mmbTools/config/journaline.dat" });
    const bitrate = bitrateSelect(8);
    const addr = h("input", { type: "number", min: 1, max: 1023, value: 1 });
    const form = h("form", { class: "stack" }, steps, h("h1", null, "Your first Journaline service"),
      h("p", { class: "muted" }, "Each service is one packet-mode data service on the multiplex, with its own output file. If two providers share the mux, add a second service later."),
      h("div", { class: "grid-2" }, field("Service name", name, { max: 64 }), field("Provider", provider)),
      field("Output file", h("div", { class: "row" }, path, btn("Browse…", { icon: "folder", onclick: async () => {
        const p = await fileBrowser({ title: "Where to write the Journaline stream", mode: "save", exts: "dat", start: path.value || "/home", filename: path.value.split("/").pop() || "journaline.dat" });
        if (p) path.value = p;
      } })), { hint: "odr-dabmux reads this file (inputuri). The service user needs write access to the folder." }),
      h("div", { class: "grid-2" }, field("Subchannel bitrate", bitrate, { hint: "8 kbps is plenty for a text service with a few dozen messages." }),
        field("Packet address", addr, { hint: "Matches 'address' in the odr-dabmux component (1 = 0x1)." })),
      h("div", { class: "row" }, btn("Back", { cls: "ghost", onclick: () => renderWizard(0) }), h("span", { class: "spacer" }), btn("Create service", { cls: "primary", type: "submit" })));
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const body = { name: name.value, provider: provider.value, output_path: path.value, bitrate: +bitrate.value, packet_address: +addr.value };
        const r = await api("POST", "/api/services", body);
        if (S.muxInfo && S.muxInfo.free_subchannel_id !== null) {
          const sv = await api("GET", `/api/services/${r.id}`);
          await api("PATCH", `/api/services/${r.id}`, { mux: { ...sv.mux, subchannel_id: S.muxInfo.free_subchannel_id } });
        }
        S.wizardService = r.id; renderWizard(2);
      } catch (ex) { /* toasted */ }
    });
    authCard(form, true);
  } else if (step === 2) {
    const sn = await api("GET", `/api/services/${S.wizardService}/mux`);
    const box = h("div");
    const fmt = formatSwitch((f) => put(clear(box), muxSnippet(sn, f)));
    put(box, muxSnippet(sn, fmt.get()));
    authCard(h("div", { class: "stack" }, steps, h("h1", null, "Add Journaline to your multiplex"),
      h("p", { class: "muted" }, "Add these entries to your odr-dabmux configuration and restart the multiplexer. ids, labels and protection can be changed later on the service's Mux config tab."),
      sn.warnings.map((w) => h("div", { class: "banner amber" }, icon("alert"), w)),
      h("div", { class: "row" }, fmt.el, h("span", { class: "spacer" }), h("span", { class: "small muted" }, `Packet size ${sn.packet_size} bytes`)), box,
      h("div", { class: "row" }, h("span", { class: "spacer" }), btn("Continue", { cls: "primary", onclick: () => renderWizard(3) }))), true);
  } else {
    const finish = async (hash) => {
      await api("PUT", "/api/settings", { setup_complete: true });
      location.hash = hash; renderShell();
    };
    authCard(h("div", { class: "stack" }, steps, h("h1", null, "You're set up"),
      h("p", { class: "muted" }, "Your service starts with a main menu and a welcome message. Next, build out the menu tree: add text messages, tickers, lists and RSS feeds, check them in the receiver preview, then click Apply to put them on air."),
      h("div", { class: "row" }, btn("Back", { cls: "ghost", onclick: () => renderWizard(2) }), h("span", { class: "spacer" }),
        btn("Open the service", { cls: "primary", onclick: () => finish(`#/services/${S.wizardService || ""}`) }))), true);
  }
}
/* ============================== shell ============================== */

const NAV = [
  ["MONITOR", [
    ["services", "Services", "grid", () => true],
    ["activity", "Activity", "activity", () => true],
  ]],
  ["MANAGE", [
    ["mux", "Mux config", "code", isEditor],
    ["users", "Users", "users", isAdmin],
    ["settings", "Settings", "sliders", isAdmin],
    ["audit", "Audit log", "audit", isAdmin],
  ]],
];

let shellEls = null;

function renderShell() {
  const app = clear(document.getElementById("app"));
  const nav = h("nav", { class: "nav", "aria-label": "Main" });
  for (const [section, items] of NAV) {
    const visible = items.filter((i) => i[3]());
    if (!visible.length) continue;
    nav.appendChild(h("div", { class: "nav-section" }, section));
    for (const [key, label, ic] of visible) {
      nav.appendChild(h("a", { href: "#/" + key, "data-key": key }, icon(ic), h("span", null, label)));
    }
  }
  const monitor = h("div", { class: "monitor" });
  const shell = h("div", { class: "shell" + (S.collapsed ? " collapsed" : "") });
  const side = h("aside", { class: "side" }, brand(), nav,
    h("div", { class: "side-foot" }, monitor,
      h("div", { class: "user-card" },
        h("a", { class: "avatar", href: "#/account", title: "Account" }, initials(S.user.display_name || S.user.username)),
        h("div", { class: "who" }, h("b", { class: "ellipsis" }, S.user.display_name || S.user.username), h("span", null, ROLE_LABEL[S.user.role])),
        themeToggle(), iconBtn("logout", "Sign out", logout)),
      h("button", { class: "collapse-btn", onclick: () => {
        S.collapsed = !S.collapsed; shell.classList.toggle("collapsed", S.collapsed);
        try { localStorage.setItem("odrjml.collapsed", S.collapsed ? "1" : "0"); } catch (e) { /* ignore */ }
      } }, icon("chevronsLeft"), h("span", null, "Collapse"))));
  const crumbs = h("div", { class: "crumbs" });
  const pending = h("div", { class: "row" });
  const content = h("div", { class: "content" });
  const main = h("main", { class: "main" },
    h("div", { class: "topbar" }, h("span", { class: "mobile-only" }, iconBtn("menu", "Menu", () => shell.classList.toggle("mobile-nav"))), crumbs, h("span", { class: "spacer" }), pending),
    content);
  put(shell, side, main);
  app.appendChild(shell);
  shellEls = { nav, monitor, crumbs, pending, content, shell };
  side.addEventListener("click", (e) => { if (e.target.closest("a")) shell.classList.remove("mobile-nav"); });
  window.onhashchange = route;
  route();
  refreshStatus();
}

function setCrumbs(...parts) {
  const c = clear(shellEls.crumbs);
  parts.forEach((p, i) => {
    if (i) c.appendChild(h("span", null, "/"));
    c.appendChild(i === parts.length - 1 ? h("b", null, p.label || p) : h("a", { href: p.href }, p.label));
  });
}

function route() {
  if (!shellEls) return;
  const parts = (location.hash.replace(/^#\/?/, "") || "services").split("/");
  const key = parts[0];
  shellEls.nav.querySelectorAll("a").forEach((a) => a.classList.toggle("active", a.dataset.key === key));
  // each navigation renders into its own container, so a slower earlier
  // render can never append into the page that replaced it
  const content = h("div");
  clear(shellEls.content).appendChild(content);
  const pages = { services: pageServices, activity: pageActivity, mux: pageMux,
    users: pageUsers, settings: pageSettings, audit: pageAudit, account: pageAccount };
  const fn = pages[key] || pageServices;
  Promise.resolve(fn(content, parts.slice(1))).catch((e) => {
    if (!(e instanceof ApiError)) { console.error(e); toast("Something went wrong rendering this page.", "error"); }
  });
  shellEls.content.parentElement.scrollTop = 0;
}

/* ---------- status polling & apply ---------- */

function stopPolling() { if (S.pollTimer) clearTimeout(S.pollTimer); S.pollTimer = null; }

async function refreshStatus() {
  stopPolling();
  if (!S.user || !shellEls) return;
  try {
    const st = await api("GET", "/api/status", undefined, { quiet: true });
    const prev = S.status;
    S.status = st;
    if (prev && prev.running && !st.running && st.build) {
      const b = st.build;
      if (b.status === "error") toast("Build failed: " + b.message, "error");
      else toast((b.status === "warning" ? "Published with warnings: " : "Published: ") + b.message, b.status === "warning" ? "" : "ok");
      if ((location.hash || "").startsWith("#/activity")) route();
    }
    renderStatus();
  } catch (e) { /* offline - retry */ }
  S.pollTimer = setTimeout(refreshStatus, S.status && S.status.running ? 1500 : 10000);
}

function renderStatus() {
  const st = S.status;
  if (!st || !shellEls) return;
  const b = st.build;
  let dot = "dot", text;
  if (st.running) { dot = "dot amber pulse"; text = "Building carousel…"; }
  else if (!b) { dot = "dot"; text = "Not published yet"; }
  else if (b.status === "error") { dot = "dot red"; text = "Last build failed · " + fmtAgo(b.finished_at); }
  else { dot = b.status === "warning" ? "dot amber" : "dot green"; text = "Carousel live · " + fmtAgo(b.finished_at); }
  put(clear(shellEls.monitor), h("i", { class: dot }), h("span", { class: "ellipsis" }, text));

  const p = clear(shellEls.pending);
  if (st.running) {
    p.appendChild(h("div", { class: "pending" }, h("span", { class: "spin" }), "Publishing…"));
  } else if (st.dirty_since || !st.published) {
    const label = st.published ? "Unpublished changes" : "Not published yet";
    p.appendChild(h("div", { class: "pending" }, icon("alert"), h("span", null, label),
      st.can_apply ? btn("Apply", { cls: "primary sm", icon: "zap", onclick: applyChanges }) : h("span", { class: "small" }, "· an editor must apply")));
  } else if (b && b.status !== "error") {
    p.appendChild(h("div", { class: "pending ok" }, icon("check"), "All changes live"));
  }
}

async function applyChanges() {
  try {
    await api("POST", "/api/apply", {});
    toast("Fetching feeds and building the carousels…");
    S.status.running = true;
    renderStatus();
    setTimeout(refreshStatus, 800);
  } catch (e) { /* toasted */ }
}

/* ============================== services ============================== */

function pageServices(root, parts) {
  if (parts && parts[0]) return pageServiceDetail(root, parseInt(parts[0], 10), parts[1], parts[2]);
  return pageServiceList(root);
}

function serviceTile(name) {
  return h("div", { class: "logo-tile" }, initials(name));
}

async function pageServiceList(root) {
  setCrumbs("Services");
  const services = await api("GET", "/api/services");
  const grid = h("div", { class: "station-grid" });
  if (!services.length) {
    grid.appendChild(h("div", { class: "empty span-all" }, h("h3", null, "No Journaline services yet"),
      h("p", null, "A service is one packet-mode data service on your multiplex. Add one per provider."),
      isEditor() ? h("div", { class: "row" }, h("span", { class: "spacer" }), btn("Add service", { cls: "primary", icon: "plus", onclick: addService }), h("span", { class: "spacer" })) : null));
  }
  for (const s of services) grid.appendChild(serviceCard(s));
  put(root,
    h("div", { class: "page-head" }, h("div", null, h("h1", null, "Services"),
      h("p", null, `${services.length} Journaline service${services.length === 1 ? "" : "s"} on this multiplex`)),
      h("span", { class: "spacer" }), isEditor() ? btn("Add service", { cls: "primary", icon: "plus", onclick: addService }) : null),
    grid);
}

function serviceCard(s) {
  const st = s.last_stats;
  let pill;
  if (!s.enabled) pill = h("span", { class: "pill muted" }, "Disabled");
  else if (s.errors.length) pill = h("span", { class: "pill red" }, icon("alert"), "Needs fixing");
  else pill = h("span", { class: "pill green" }, h("i", { class: "dot green" }), "On air");
  const card = h("button", { class: "station-card" + (s.errors.length && s.enabled ? " problem" : "") + (s.enabled ? "" : " off"), type: "button",
    onclick: () => { location.hash = `#/services/${s.id}`; } },
    h("div", { class: "sc-head" }, serviceTile(s.name),
      h("div", { class: "titles" }, h("h3", { class: "ellipsis" }, s.name), h("div", { class: "sub ellipsis" }, s.provider || `Packet address ${s.packet_address}`)), pill),
    h("div", { class: "sc-inset" }, h("div", { class: "jl-counts" },
      h("div", null, h("b", null, s.objects), h("span", null, "objects")),
      h("div", null, h("b", null, s.feeds), h("span", null, "RSS feeds")),
      h("div", null, h("b", null, s.broadcast_objects), h("span", null, "on air")),
      h("div", null, h("b", null, st ? fmtMinSec(st.cycle_seconds) : "—"), h("span", null, "cycle")))),
    h("div", { class: "stack tight" }, h("div", { class: "row" }, h("div", { class: "stat-line" }, h("b", null, s.bitrate), "kbps"),
      h("span", { class: "spacer" }), h("span", { class: "small muted" }, st ? `${fmtBytes(st.stream_bytes)} per pass` : "Not published yet"))),
    h("div", { class: "sc-foot" },
      h("span", { class: "chip mono" }, `addr 0x${s.packet_address.toString(16)}`),
      s.errors.length ? h("span", { class: "chip red" }, icon("alert"), `${s.errors.length} problem${s.errors.length > 1 ? "s" : ""}`) : null,
      s.feed_errors.length ? h("span", { class: "chip red" }, icon("rss"), "Feed failing") : null,
      s.warnings.length ? h("span", { class: "chip amber" }, `${s.warnings.length} warning${s.warnings.length > 1 ? "s" : ""}`) : null,
      h("span", { class: "when" }, "Updated " + fmtAgo(s.updated_at))));
  return card;
}

function addService() {
  const name = inp("", { maxlength: 64 }), provider = inp("", { maxlength: 64, placeholder: "Optional" });
  const m = modal({
    title: "Add Journaline service",
    body: h("div", { class: "stack" }, field("Name", name, { max: 64 }), field("Provider", provider, { hint: "Who supplies the content, e.g. when two providers share the mux." }),
      h("div", { class: "small muted" }, "It starts with a main menu and a welcome message. Set its output file and bitrate on the Settings tab.")),
    foot: [btn("Cancel", { onclick: () => m.close() }), btn("Create", { cls: "primary", onclick: async () => {
      try { const r = await api("POST", "/api/services", { name: name.value, provider: provider.value }); m.close(); refreshStatus(); location.hash = `#/services/${r.id}/settings`; } catch (e) { /* toasted */ }
    } })],
  });
}

/* ---------- service detail ---------- */

async function pageServiceDetail(root, id, tab, sel) {
  const s = await api("GET", `/api/services/${id}`);
  setCrumbs({ href: "#/services", label: "Services" }, s.name);
  const tabsDef = [["content", "Content", "list"], ["preview", "Receiver preview", "eye"], ["settings", "Settings", "sliders"], ["mux", "Mux config", "code"]];
  tab = tabsDef.some((t) => t[0] === tab) ? tab : "content";
  const body = h("div");
  const tabs = h("div", { class: "tabs", role: "tablist" }, tabsDef.map(([k, l, ic]) =>
    h("button", { class: k === tab ? "on" : "", role: "tab", onclick: () => { location.hash = `#/services/${id}/${k}`; } }, icon(ic), l)));
  put(root,
    h("div", { class: "page-head" }, iconBtn("arrowLeft", "Back to services", () => { location.hash = "#/services"; }), serviceTile(s.name),
      h("div", { class: "grow" }, h("h1", null, s.name),
        h("p", null, [s.provider, `${s.bitrate} kbps`, `packet address ${s.packet_address}`, s.output_path || "no output file set"].filter(Boolean).join(" · "))),
      s.enabled ? h("span", { class: "pill green" }, "Enabled") : h("span", { class: "pill muted" }, "Disabled")),
    tabs, body);
  if (tab === "content") serviceContent(body, s, sel);
  if (tab === "preview") servicePreview(body, s, sel);
  if (tab === "settings") serviceSettings(body, s);
  if (tab === "mux") serviceMux(body, s);
}

/* ---------- content: tree + editors ---------- */

function buildNodes(s) {
  const nodes = new Map();
  for (const o of s.object_list) nodes.set(o.jid, { kind: "object", jid: o.jid, type: o.type, title: o.title, data: o });
  for (const f of s.feed_list) nodes.set(f.jid, { kind: "feed", jid: f.jid, type: "feed", title: f.title || f.name || f.url, data: f });
  return nodes;
}

function childrenOf(node) {
  if (node.kind === "object" && node.type === "menu") return node.data.items.map((i) => ({ target: i.target, label: i.label }));
  return [];
}

function issuesById(s) {
  const map = new Map();
  for (const [kind, list] of [["error", s.errors], ["warning", s.warnings]]) {
    for (const it of list) {
      if (it.id === null || it.id === undefined) continue;
      if (!map.has(it.id) || kind === "error") map.set(it.id, kind);
    }
  }
  return map;
}

function serviceContent(root, s, selParam) {
  const nodes = buildNodes(s);
  const issues = issuesById(s);
  let selected = parseJid(selParam);
  if (selected === null || Number.isNaN(selected) || !nodes.has(selected)) selected = 0;
  let collapsed = new Set();
  try { collapsed = new Set(JSON.parse(sessionStorage.getItem(`odrjml.collapsed.${s.id}`) || "[]")); } catch (e) { /* ignore */ }
  const tree = h("div", { class: "jl-tree" });
  const editor = h("div", { class: "jl-editor" });
  const reload = async (jid) => {
    const fresh = await api("GET", `/api/services/${s.id}`);
    refreshStatus();
    clear(root);
    serviceContent(root, fresh, jid === undefined ? hex4(selected) : hex4(jid));
  };
  const select = (jid) => {
    selected = jid;
    history.replaceState(null, "", `#/services/${s.id}/content/${hex4(jid)}`);
    drawTree(); drawEditor();
  };
  // ---- drag and drop: move links between menus, reorder them, or (Alt/Ctrl) add another link ----
  let drag = null;
  const isManualMenu = (jid) => { const n = nodes.get(jid); return !!n && n.kind === "object" && n.type === "menu"; };
  const clearMarks = () => tree.querySelectorAll(".drop-into, .drop-before, .drop-after, .drop-out").forEach((el) => el.classList.remove("drop-into", "drop-before", "drop-after", "drop-out"));
  const wantsCopy = (e) => e.altKey || e.ctrlKey || e.metaKey;
  const dropMode = (e, el, ctx) => {
    if (ctx.unlink) return drag.from !== null && drag.from !== undefined ? "out" : null;
    const r = el.getBoundingClientRect();
    const y = (e.clientY - r.top) / r.height;
    const canInto = ctx.into !== undefined && isManualMenu(ctx.into) && ctx.into !== drag.target;
    const canSibling = ctx.parent !== null && ctx.parent !== undefined && isManualMenu(ctx.parent) && ctx.parent !== drag.target;
    if (canInto && (!canSibling || (y > 0.25 && y < 0.75))) return "into";
    if (canSibling) return y < 0.5 ? "before" : "after";
    return null;
  };
  const dnd = (el, ctx) => {
    if (!isEditor()) return el;
    if (ctx.draggable) {
      el.draggable = true;
      el.addEventListener("dragstart", (e) => {
        drag = { target: ctx.target, from: ctx.parent ?? null, fromIndex: ctx.index ?? null };
        e.dataTransfer.effectAllowed = "copyMove";
        e.dataTransfer.setData("text/plain", hex4(ctx.target));
        el.classList.add("dragging"); tree.classList.add("dragging-on");
      });
      el.addEventListener("dragend", () => { drag = null; el.classList.remove("dragging"); tree.classList.remove("dragging-on"); clearMarks(); });
    }
    el.addEventListener("dragover", (e) => {
      if (!drag) return;
      const m = dropMode(e, el, ctx);
      clearMarks();
      if (!m) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = wantsCopy(e) && m !== "out" ? "copy" : "move";
      el.classList.add("drop-" + m);
    });
    el.addEventListener("dragleave", (e) => { if (!el.contains(e.relatedTarget)) el.classList.remove("drop-into", "drop-before", "drop-after", "drop-out"); });
    el.addEventListener("drop", async (e) => {
      if (!drag) return;
      const m = dropMode(e, el, ctx);
      clearMarks();
      if (!m) return;
      e.preventDefault();
      const d = drag; drag = null;
      const copy = wantsCopy(e) && m !== "out";
      const body = { target: d.target, from: d.from, from_index: d.fromIndex, copy };
      if (m === "out") body.to = null;
      else if (m === "into") { body.to = ctx.into; body.index = null; }
      else { body.to = ctx.parent; body.index = ctx.index + (m === "after" ? 1 : 0); }
      try {
        await api("POST", `/api/services/${s.id}/move`, body);
        toast(m === "out" ? "Link removed - click Apply to publish." : copy ? "Link added - click Apply to publish." : "Moved - click Apply to publish.", "ok");
        if (body.to !== null && body.to !== undefined) collapsed.delete(body.to);
        reload(d.target);
      } catch (ex) { /* toasted */ }
    });
    return el;
  };

  const row = (node, depth, label, seen, path, parent = null, index = null) => {
    const kids = childrenOf(node);
    const isOpen = !collapsed.has(node.jid);
    const issue = issues.get(node.jid);
    const r = h("div", { class: "jl-node" + (node.jid === selected ? " sel" : ""), style: `--depth:${depth}`, role: "treeitem", tabindex: 0,
      onclick: () => select(node.jid), onkeydown: (e) => { if (e.key === "Enter") select(node.jid); } },
      kids.length ? h("button", { class: "jl-twist", type: "button", "aria-label": isOpen ? "Collapse" : "Expand", onclick: (e) => {
        e.stopPropagation();
        if (isOpen) collapsed.add(node.jid); else collapsed.delete(node.jid);
        try { sessionStorage.setItem(`odrjml.collapsed.${s.id}`, JSON.stringify([...collapsed])); } catch (ex) { /* ignore */ }
        drawTree();
      } }, icon(isOpen ? "chevronDown" : "chevronRight")) : h("span", { class: "jl-twist" }),
      typeBadge(node.type),
      h("span", { class: "jl-title ellipsis", title: label && label !== node.title ? `Title: ${node.title}\nShown in the menu as: ${label}` : node.title },
        node.title || "(no title)", label && label !== node.title ? h("span", { class: "muted" }, `  · menu shows “${label}”`) : null),
      issue ? h("i", { class: "dot " + (issue === "error" ? "red" : "amber"), title: issue === "error" ? "Has errors" : "Has warnings" }) : null,
      h("span", { class: "jl-id mono" }, hex4(node.jid)));
    tree.appendChild(dnd(r, { target: node.jid, into: node.jid, parent, index, draggable: node.jid !== 0 }));
    if (!kids.length || !isOpen) return;
    kids.forEach((k, i) => {
      const child = nodes.get(k.target);
      if (!child) {
        tree.appendChild(dnd(h("div", { class: "jl-node missing", style: `--depth:${depth + 1}` }, h("span", { class: "jl-twist" }), h("span", { class: "type-badge red" }, icon("alert")),
          h("span", { class: "jl-title" }, k.label, h("span", { class: "muted" }, " → missing object")), h("span", { class: "jl-id mono" }, hex4(k.target))),
          { target: k.target, parent: node.jid, index: i, draggable: false }));
      } else if (path.has(k.target) || seen.has(k.target)) {
        tree.appendChild(dnd(h("div", { class: "jl-node ref", style: `--depth:${depth + 1}`, onclick: () => select(k.target), title: "Also linked from here - the object is shown in full where it first appears" },
          h("span", { class: "jl-twist" }), h("span", { class: "type-badge" }, icon("cornerDown")), h("span", { class: "jl-title ellipsis" }, child.title,
            k.label !== child.title ? h("span", { class: "muted" }, `  · menu shows “${k.label}”`) : null),
          h("span", { class: "jl-id mono" }, hex4(k.target))), { target: k.target, into: k.target, parent: node.jid, index: i, draggable: k.target !== 0 }));
      } else {
        seen.add(k.target);
        row(child, depth + 1, k.label, seen, new Set([...path, k.target]), node.jid, i);
      }
    });
  };
  const drawTree = () => {
    clear(tree);
    const seen = new Set([0]);
    if (nodes.has(0)) row(nodes.get(0), 0, null, seen, new Set([0]));
    else tree.appendChild(h("div", { class: "banner red" }, icon("alert"), "There is no root object (0x0000). Receivers start there - add a menu with ID 0x0000."));
    const orphans = [...nodes.values()].filter((n) => !seen.has(n.jid)).sort((a, b) => a.jid - b.jid);
    tree.appendChild(dnd(h("div", { class: "jl-sep jl-unlink small muted" }, "Not linked from any menu",
      isEditor() ? h("span", { class: "jl-unlink-hint" }, " · drop a link here to remove it from its menu") : null), { unlink: true }));
    for (const n of orphans) { seen.add(n.jid); row(n, 0, null, seen, new Set([n.jid])); }
    if (!orphans.length) tree.appendChild(h("div", { class: "jl-empty small muted" }, "Everything is linked."));
  };
  const drawEditor = () => {
    clear(editor);
    const n = nodes.get(selected);
    if (!n) return;
    if (n.kind === "feed") feedEditor(editor, s, n.data, nodes, reload);
    else objectEditor(editor, s, n.data, nodes, reload);
  };
  const problems = s.errors.filter((e) => e.id === null || !nodes.has(e.id));
  put(root,
    s.errors.length ? h("div", { class: "banner red" }, icon("alert"), h("div", { class: "grow" }, h("b", null, `${s.errors.length} problem${s.errors.length > 1 ? "s" : ""} - this service can't be published until they're fixed`),
      h("ul", { class: "warn-list" }, s.errors.slice(0, 8).map((e) => h("li", null, h("span", null, e.message)))))) : null,
    problems.length || s.errors.length ? h("div", { class: "section-gap" }) : null,
    h("div", { class: "jl-split" },
      h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", { class: "grow" }, h("h2", null, "Menu tree"), h("p", null, isEditor() ? "Drag to move or reorder - onto a menu to put it inside. Hold Alt (Option) to add another link instead." : "What listeners can navigate, starting at the root menu.")),
        isEditor() ? btn("Object", { cls: "sm", icon: "plus", onclick: () => addObject(s, nodes, selected, reload) }) : null,
        isEditor() ? btn("RSS feed", { cls: "sm", icon: "rss", onclick: () => addFeed(s, nodes, selected, reload) }) : null),
        h("div", { class: "card-body" }, tree)),
      editor));
  drawTree(); drawEditor();
}

function menuOptions(nodes, current) {
  const menus = [...nodes.values()].filter((n) => n.kind === "object" && n.type === "menu").sort((a, b) => a.jid - b.jid);
  const sel0 = menus.some((m) => m.jid === current) ? current : (menus[0] ? menus[0].jid : "");
  return sel(sel0, [["", "Not linked (add a link later)"], ...menus.map((m) => [m.jid, `${hex4(m.jid)} · ${m.title}`])]);
}

function addObject(s, nodes, selected, reload, presetParent) {
  let type = "text";
  const seg = h("div", { class: "segmented" });
  const help = h("div", { class: "small muted" });
  const drawSeg = () => {
    clear(seg);
    for (const t of ["menu", "text", "title", "list"]) seg.appendChild(h("button", { type: "button", class: type === t ? "on" : "", onclick: () => { type = t; drawSeg(); } }, h("span", { class: "row" }, icon(TYPE_META[t].icon), TYPE_META[t].label)));
    help.textContent = TYPE_META[type].help;
  };
  drawSeg();
  const title = inp("", { maxlength: 1000 });
  const parent = menuOptions(nodes, presetParent ?? selected);
  const label = inp("", { maxlength: 300, placeholder: "Defaults to the title" });
  const jid = inp("", { class: "mono", placeholder: "auto" });
  const m = modal({
    title: "Add object", wide: true,
    body: h("div", { class: "stack" }, field("Type", seg), help, field("Title", title, { hint: "Headline or menu title - the first line receivers show." }),
      h("div", { class: "grid-2" }, field("Link from menu", parent), field("Link text in that menu", label)),
      h("details", null, h("summary", { class: "small muted" }, "Object ID"), h("div", { class: "section-gap" }), field("Object ID", jid, { hint: "Leave empty to pick the next free one. 0x0001-0x7FFF; feed stories use 0x8000 and up." }))),
    foot: [btn("Cancel", { onclick: () => m.close() }), btn("Create", { cls: "primary", onclick: async () => {
      const body = { type, title: title.value, parent: parent.value === "" ? null : +parent.value, label: label.value };
      if (jid.value.trim()) body.jid = parseJid(jid.value);
      try { const r = await api("POST", `/api/services/${s.id}/objects`, body); m.close(); toast("Created - click Apply to publish.", "ok"); reload(r.jid); } catch (e) { /* toasted */ }
    } })],
  });
}

function addFeed(s, nodes, selected, reload) {
  const url = inp("", { type: "url", placeholder: "https://example.com/news/rss.xml" });
  const mode = sel("menu", FEED_MODES);
  const title = inp("", { maxlength: 200, placeholder: "Taken from the feed if empty" });
  const max = h("input", { type: "number", min: 1, max: 32, value: 10 });
  const parent = menuOptions(nodes, selected);
  const label = inp("", { maxlength: 300, placeholder: "Defaults to the title" });
  const result = h("div");
  const test = async () => {
    put(clear(result), h("div", { class: "row muted" }, h("span", { class: "spin" }), "Fetching…"));
    try {
      const r = await api("POST", "/api/feeds/test", { url: url.value }, { quiet: true });
      if (!title.value) title.value = r.title;
      put(clear(result), h("div", { class: "banner green" }, icon("check"), h("div", null, h("b", null, `${r.title || "Feed"}: ${r.count} item(s)`),
        h("ul", null, r.items.slice(0, 5).map((i) => h("li", null, i.title))))));
    } catch (e) { put(clear(result), h("div", { class: "banner red" }, icon("alert"), e.message)); }
  };
  const m = modal({
    title: "Add RSS feed", wide: true,
    body: h("div", { class: "stack" }, field("Feed URL", h("div", { class: "row" }, url, btn("Test", { icon: "play", onclick: test }))), result,
      h("div", { class: "grid-2" }, field("Show as", mode), field("Stories", max, { hint: "Newest first, at most 32." })),
      field("Title", title),
      h("div", { class: "grid-2" }, field("Link from menu", parent), field("Link text in that menu", label)),
      h("div", { class: "small muted" }, "Feeds are re-read on every Apply and on the refresh schedule (Settings). Story messages get stable object IDs from 0x8000 up.")),
    foot: [btn("Cancel", { onclick: () => m.close() }), btn("Add feed", { cls: "primary", onclick: async () => {
      const body = { url: url.value, mode: mode.value, title: title.value, max_items: +max.value, parent: parent.value === "" ? null : +parent.value, label: label.value };
      try {
        const r = await api("POST", `/api/services/${s.id}/feeds`, body);
        m.close();
        if (r.error) toast("Feed added, but it couldn't be read yet: " + r.error, "error"); else toast("Feed added - click Apply to publish.", "ok");
        reload(r.jid);
      } catch (e) { /* toasted */ }
    } })],
  });
}

function menusBox(s, jid, nodes, reload) {
  // where this object is linked from, with remove buttons and an "add to menu" picker
  const parents = [];
  for (const n of nodes.values()) {
    if (n.kind !== "object" || n.type !== "menu") continue;
    n.data.items.forEach((it, i) => { if (it.target === jid) parents.push({ menu: n, index: i, label: it.label }); });
  }
  const ed = isEditor();
  const move = async (body, msg) => {
    try { await api("POST", `/api/services/${s.id}/move`, { target: jid, ...body }); toast(msg + " - click Apply to publish.", "ok"); reload(jid); } catch (e) { /* toasted */ }
  };
  const options = [...nodes.values()].filter((n) => n.kind === "object" && n.type === "menu" && n.jid !== jid && !parents.some((p) => p.menu.jid === n.jid))
    .sort((a, b) => a.jid - b.jid);
  const pick = sel("", [["", "Add to menu…"], ...options.map((m) => [m.jid, `${hex4(m.jid)} · ${m.title}`])], { "aria-label": "Add to menu" });
  pick.addEventListener("change", () => { if (pick.value !== "") move({ to: +pick.value }, "Added to the menu"); });
  const title = (nodes.get(jid) || {}).title || "";
  const linkText = (p) => {
    // the text receivers show in that menu; it follows the title unless it was changed here
    if (!ed) return h("span", { class: "grow muted ellipsis" }, `shows “${p.label}”`);
    const input = inp(p.label, { maxlength: 300, class: "jl-linktext", "aria-label": `Text shown in ${p.menu.title}`, title: "The text this menu shows for the link" });
    const save = async (v) => {
      v = v.trim();
      if (!v || v === p.label) { input.value = p.label; return; }
      try { await api("POST", `/api/services/${s.id}/link-text`, { menu: p.menu.jid, index: p.index, target: jid, label: v }); toast("Link text saved - click Apply to publish.", "ok"); reload(jid); } catch (e) { input.value = p.label; }
    };
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); save(input.value); } if (e.key === "Escape") input.value = p.label; });
    input.addEventListener("change", () => save(input.value));
    return h("div", { class: "jl-linktext-wrap" }, input,
      title && p.label !== title ? btn("Use title", { cls: "sm ghost", title: `Show “${title}” in this menu`, onclick: () => save(title) }) : null);
  };
  const moveTo = (p) => sel("", [["", "Move to…"], ...options.map((m) => [m.jid, `${hex4(m.jid)} · ${m.title}`])], { "aria-label": "Move to another menu",
    onchange: (e) => { if (e.target.value !== "") move({ from: p.menu.jid, from_index: p.index, to: +e.target.value }, "Moved"); } });
  return h("div", { class: "field" }, h("div", { class: "label-row" }, h("label", null, "In menus")),
    parents.length ? h("div", { class: "hint jl-menus-hint" }, "Each menu shows its own text for the link - the box next to the menu name. It follows the title unless you change it here.") : null,
    h("div", { class: "stack tight" },
      jid === 0 ? h("div", { class: "small muted" }, "The root object - receivers start here.") : null,
      !parents.length && jid !== 0 ? h("div", { class: "small muted" }, "Not linked from any menu yet, so listeners can't reach it.") : null,
      parents.map((p) => h("div", { class: "jl-parent-row wrap" }, typeBadge("menu"),
        h("span", { class: "jl-parent-name ellipsis" }, h("b", null, p.menu.title), h("span", { class: "muted mono" }, `  ${hex4(p.menu.jid)}`)),
        linkText(p),
        ed && options.length ? moveTo(p) : null,
        ed ? iconBtn("x", "Remove from this menu", () => move({ from: p.menu.jid, from_index: p.index, to: null }, "Removed from the menu")) : null)),
      ed && options.length ? h("div", { class: "jl-add-menu" }, pick) : null));
}

function byteMeter(n, max = MAX_OBJECT) {
  const pct = Math.min(100, Math.round((n / max) * 100));
  return h("div", { class: "jl-meter" + (n > max ? " over" : pct > 85 ? " warn" : ""), title: `${n} of ${max} bytes` },
    h("i", { style: `width:${pct}%` }), h("span", null, `${fmtBytes(n)} of 4 KB`));
}

function objectEditor(root, s, o, nodes, reload) {
  const ed = isEditor();
  const title = h("textarea", { rows: o.type === "title" ? 3 : 1, class: "jl-title-input", disabled: !ed }, o.title);
  const jid = inp(hex4(o.jid), { class: "mono", disabled: !ed || o.jid === 0, maxlength: 6 });
  const statik = toggle("Listeners may save this as a favourite (the content type stays the same)", !!o.static, { disabled: !ed });
  const body = { el: null, get: () => ({}) };
  const sizeBox = h("div");
  const approx = () => 3 + utf8len(title.value) + JSON.stringify(body.get()).length;
  const updSize = () => put(clear(sizeBox), byteMeter(approx()));

  if (o.type === "menu") Object.assign(body, menuItemsEditor(o.items, nodes, ed, () => addObject(s, nodes, o.jid, reload, o.jid)));
  if (o.type === "text") Object.assign(body, textBodyEditor(o.body, ed));
  if (o.type === "list") Object.assign(body, listRowsEditor(o.rows, ed));
  const adv = advancedEditor(o, nodes, ed);
  root.addEventListener("input", debounce(updSize, 200));

  const save = async () => {
    const payload = { title: title.value, static: statik.box.checked, ...body.get(), ...adv.get() };
    const newJid = parseJid(jid.value);
    if (newJid !== o.jid) payload.jid = newJid;
    try { await api("PUT", `/api/objects/${o.id}`, payload); toast("Saved - click Apply to publish.", "ok"); reload(newJid ?? o.jid); } catch (e) { /* toasted */ }
  };
  put(root, h("div", { class: "card" },
    h("div", { class: "card-head" }, typeBadge(o.type, "lg"), h("div", { class: "grow" }, h("h2", null, TYPE_META[o.type].label), h("p", null, TYPE_META[o.type].help)),
      iconBtn("eye", "Show in the receiver preview", () => { location.hash = `#/services/${s.id}/preview/${hex4(o.jid)}`; })),
    h("div", { class: "card-body stack" },
      h("div", { class: "jl-head-grid" }, field(o.type === "title" ? "Ticker text" : "Title", title, { max: o.type === "title" ? 1000 : 200 }), field("Object ID", jid)),
      body.el, menusBox(s, o.jid, nodes, reload), adv.el, ed ? statik.el : null, sizeBox,
      o.note ? h("div", { class: "small muted" }, "Note: ", o.note) : null),
    ed ? h("div", { class: "card-foot" }, o.jid === 0 ? h("span", { class: "small muted" }, "The root object is where receivers start.") : btn("Delete", { cls: "danger", icon: "trash", onclick: async () => {
      if (!(await confirmDialog(`Delete "${o.title}" (${hex4(o.jid)})? Links to it are removed from menus.`, { danger: true, okText: "Delete" }))) return;
      try { await api("DELETE", `/api/objects/${o.id}`); toast("Deleted.", "ok"); reload(0); } catch (e) { /* toasted */ }
    } }), h("span", { class: "spacer" }), btn("Save", { cls: "primary", icon: "check", onclick: save })) : null));
  updSize();
}

function targetSelect(value, nodes, disabled) {
  const opts = [...nodes.values()].sort((a, b) => a.jid - b.jid).map((n) => [n.jid, `${hex4(n.jid)} · ${TYPE_META[n.type].label} · ${n.title}`]);
  if (!nodes.has(value)) opts.unshift([value, `${hex4(value)} · missing`]);
  return sel(value, opts, { disabled, "aria-label": "Link target" });
}

function menuItemsEditor(items, nodes, ed, onNew) {
  const list = h("div", { class: "stack tight" });
  const rows = [];
  const count = h("span", { class: "count" });
  const updCount = () => { count.textContent = `${rows.length} of 32 links`; };
  const add = (it) => {
    const r = { target: targetSelect(it.target, nodes, !ed), label: inp(it.label, { maxlength: 300, disabled: !ed, placeholder: "Link text" }) };
    r.el = h("div", { class: "jl-link-row" }, r.label, r.target, ed ? h("div", { class: "row tight-row" },
      iconBtn("chevronUp", "Move up", () => { const i = rows.indexOf(r); if (i > 0) { rows.splice(i, 1); rows.splice(i - 1, 0, r); redraw(); } }),
      iconBtn("chevronDown", "Move down", () => { const i = rows.indexOf(r); if (i < rows.length - 1) { rows.splice(i, 1); rows.splice(i + 1, 0, r); redraw(); } }),
      iconBtn("trash", "Remove link", () => { rows.splice(rows.indexOf(r), 1); redraw(); })) : null);
    rows.push(r);
  };
  const redraw = () => { clear(list); rows.forEach((r) => list.appendChild(r.el)); updCount(); };
  items.forEach(add); redraw();
  const el = h("div", { class: "field" }, h("div", { class: "label-row" }, h("label", null, "Links"), count), list,
    ed ? h("div", { class: "row" }, btn("Add link", { cls: "sm ghost", icon: "plus", onclick: () => {
      if (rows.length >= 32) return toast("A menu can hold at most 32 links.", "error");
      const first = [...nodes.keys()].find((k) => k !== 0) ?? 0;
      add({ target: first, label: "" }); redraw();
    } }), btn("New object in this menu…", { cls: "sm ghost", icon: "plus", onclick: onNew })) : null);
  return { el, get: () => ({ items: rows.map((r) => ({ target: +r.target.value, label: r.label.value || (nodes.get(+r.target.value) || {}).title || "" })) }) };
}

function textBodyEditor(text, ed) {
  const ta = h("textarea", { rows: 12, disabled: !ed, class: "jl-body" }, text);
  const wrapSel = (pre, post) => {
    const a = ta.selectionStart, b = ta.selectionEnd, v = ta.value;
    ta.value = v.slice(0, a) + pre + v.slice(a, b) + post + v.slice(b);
    ta.focus(); ta.selectionStart = a + pre.length; ta.selectionEnd = b + pre.length;
    ta.dispatchEvent(new Event("input", { bubbles: true }));
  };
  const bar = ed ? h("div", { class: "jl-toolbar" },
    btn("Highlight", { cls: "sm ghost", icon: "bold", title: "Wrap the selection in ** ** - shown highlighted where receivers can", onclick: () => wrapSel("**", "**") }),
    btn("End of intro", { cls: "sm ghost", icon: "minus", title: "Receivers (and text-to-speech) may stop here until the listener asks for more", onclick: () => wrapSel("\n---\n", "") })) : null;
  const el = h("div", { class: "field" }, h("div", { class: "label-row" }, h("label", null, "Message text")), bar, ta,
    h("div", { class: "hint" }, "New lines become preferred line breaks. **text** is highlighted. A line with only --- ends the introduction. Receivers wrap the text themselves."));
  return { el, get: () => ({ body: ta.value }) };
}

function parseTable(text) {
  const lines = text.replace(/\r/g, "").split("\n").filter((l) => l.trim());
  const sep = lines.some((l) => l.includes("\t")) ? "\t" : lines.some((l) => l.includes(";")) ? ";" : lines.some((l) => l.includes("|")) ? "|" : ",";
  return lines.map((l) => l.split(sep).map((c) => c.trim().replace(/^"(.*)"$/, "$1")));
}

function listRowsEditor(rows, ed) {
  let data = rows.length ? rows.map((r) => [...r]) : [[""]];
  const table = h("div", { class: "jl-grid-wrap" });
  const draw = () => {
    const cols = Math.max(1, ...data.map((r) => r.length));
    data = data.map((r) => [...r, ...Array(cols - r.length).fill("")]);
    clear(table).appendChild(h("table", { class: "jl-grid" }, h("tbody", null, data.map((r, ri) => h("tr", null,
      r.map((c, ci) => h("td", null, h("input", { type: "text", value: c, disabled: !ed, "aria-label": `Row ${ri + 1} column ${ci + 1}`, oninput: (e) => { data[ri][ci] = e.target.value; } }))),
      ed ? h("td", { class: "nowrap" }, iconBtn("chevronUp", "Move up", () => { if (ri) { [data[ri - 1], data[ri]] = [data[ri], data[ri - 1]]; draw(); } }),
        iconBtn("trash", "Remove row", () => { data.splice(ri, 1); if (!data.length) data.push([""]); draw(); })) : null)))));
  };
  draw();
  const paste = () => {
    const ta = h("textarea", { rows: 10, class: "mono", placeholder: "TSV 1860 - Cottbus\t3:0\nDortmund - Nürnberg\t4:1" });
    const m = modal({ title: "Paste a table", wide: true,
      body: h("div", { class: "stack" }, h("p", { class: "muted" }, "Paste from a spreadsheet, or CSV with , ; or | between columns. This replaces the rows below."), ta),
      foot: [btn("Cancel", { onclick: () => m.close() }), btn("Use these rows", { cls: "primary", onclick: () => { const t = parseTable(ta.value); if (!t.length) return; data = t; draw(); m.close(); } })] });
  };
  const el = h("div", { class: "field" }, h("div", { class: "label-row" }, h("label", null, "Rows")), table,
    ed ? h("div", { class: "row wrap" }, btn("Add row", { cls: "sm ghost", icon: "plus", onclick: () => { data.push([]); draw(); } }),
      btn("Add column", { cls: "sm ghost", icon: "plus", onclick: () => { data = data.map((r) => [...r, ""]); draw(); } }),
      btn("Remove last column", { cls: "sm ghost", icon: "minus", onclick: () => { data = data.map((r) => r.slice(0, Math.max(1, r.length - 1))); draw(); } }),
      btn("Paste table…", { cls: "sm ghost", icon: "copy", onclick: paste })) : null,
    h("div", { class: "hint" }, "Receivers line columns up in a monospace font. Empty rows are left out."));
  return { el, get: () => ({ rows: data.filter((r) => r.some((c) => c.trim())) }) };
}

function linksEditor(links, nodes, ed) {
  const wrap = h("div", { class: "stack tight" });
  const rows = [];
  const add = (l) => {
    const type = sel(l.type, [["url", "Web link"], ["phone", "Phone"], ["sms", "SMS"], ["dab", "DAB/DRM URI"], ["jml", "Journaline object"]], { disabled: !ed });
    const addr = inp(l.type === "jml" ? hex4(l.address) : l.address, { disabled: !ed, placeholder: "https://… or +353…" });
    const label = inp(l.label, { disabled: !ed, placeholder: "Label, e.g. Call the hotline" });
    const r = { type, addr, label };
    r.el = h("div", { class: "jl-link-row" }, type, addr, label, ed ? iconBtn("trash", "Remove", () => { rows.splice(rows.indexOf(r), 1); r.el.remove(); }) : null);
    rows.push(r); wrap.appendChild(r.el);
  };
  links.forEach(add);
  return { el: h("div", { class: "stack tight" }, wrap, ed ? h("div", null, btn("Add button link", { cls: "sm ghost", icon: "link", onclick: () => add({ type: "url", address: "", label: "" }) })) : null),
    get: () => rows.map((r) => ({ type: r.type.value, address: r.type.value === "jml" ? parseJid(r.addr.value) : r.addr.value.trim(), label: r.label.value })).filter((l) => l.address !== "" && l.address !== null) };
}

function toLocalInput(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

function advancedEditor(o, nodes, ed) {
  const expires = h("input", { type: "datetime-local", value: toLocalInput(o.expires), disabled: !ed });
  const lifetime = h("input", { type: "number", min: 0, max: 65535, value: o.lifetime || "", placeholder: "minutes", disabled: !ed });
  const lang = inp(o.language, { maxlength: 3, placeholder: "e.g. eng, gle", disabled: !ed, class: "mono" });
  const repeat = sel(o.repeat || 0, [[0, "Service default for this type"], ...[1, 2, 3, 4, 5, 6, 8, 10].map((n) => [n, `${n}× per cycle`])], { disabled: !ed });
  const comp = sel(o.compression || "", [["", "Service default"], ["off", "Never compress"]], { disabled: !ed });
  const note = inp(o.note, { maxlength: 200, disabled: !ed, placeholder: "Only shown here" });
  const links = linksEditor(o.links || [], nodes, ed);
  const used = o.expires || o.lifetime || o.language || o.repeat || o.compression || (o.links && o.links.length) || o.note;
  const el = h("details", { class: "jl-adv", open: used ? true : null }, h("summary", null, "Advanced: expiry, button links, speech and carousel"),
    h("div", { class: "stack" },
      h("div", { class: "grid-2" }, field("Expires at", expires, { hint: "Taken off air after this time (receivers hide it too)." }),
        field("Lifetime after reception (minutes)", lifetime, { hint: "Receivers hide it this long after they last received it. Empty = no limit." })),
      field("Button links (\"hot button\")", links.el, { hint: "Extra targets receivers may offer, e.g. a phone number or web page." }),
      h("div", { class: "grid-3" }, field("Language (text-to-speech)", lang), field("Repeats", repeat), field("Compression", comp)),
      field("Internal note", note)));
  return { el, get: () => ({ expires: expires.value ? new Date(expires.value).toISOString() : "", lifetime: +lifetime.value || 0, language: lang.value.trim(),
    repeat: +repeat.value, compression: comp.value, note: note.value, links: links.get() }) };
}

function feedEditor(root, s, f, nodes, reload) {
  const ed = isEditor();
  const url = inp(f.url, { type: "url", disabled: !ed });
  const mode = sel(f.mode, FEED_MODES, { disabled: !ed });
  const title = inp(f.title, { maxlength: 200, disabled: !ed, placeholder: "Taken from the feed name if empty" });
  const name = inp(f.name, { maxlength: 64, disabled: !ed, placeholder: "Only shown here" });
  const max = h("input", { type: "number", min: 1, max: 32, value: f.max_items, disabled: !ed });
  const itemText = sel(f.item_text, [["description", "Story text from the feed"], ["title", "Headline only"]], { disabled: !ed });
  const showTime = toggle("Show the publication time with each headline", !!f.show_time, { disabled: !ed });
  const statik = toggle("Listeners may save this as a favourite", !!f.static, { disabled: !ed });
  const enabled = toggle("Broadcast this feed", !!f.enabled, { disabled: !ed });
  const jid = inp(hex4(f.jid), { class: "mono", disabled: !ed, maxlength: 6 });
  const ok = f.status.startsWith("ok");
  put(root, h("div", { class: "card" },
    h("div", { class: "card-head" }, typeBadge("feed", "lg"), h("div", { class: "grow" }, h("h2", null, "RSS feed"), h("p", null, "The content below comes from the feed and updates on every refresh.")),
      iconBtn("eye", "Show in the receiver preview", () => { location.hash = `#/services/${s.id}/preview/${hex4(f.jid)}`; })),
    h("div", { class: "card-body stack" },
      h("div", { class: ok ? "banner green" : f.status ? "banner red" : "banner blue" }, icon(ok ? "check" : f.status ? "alert" : "info"),
        h("div", { class: "grow" }, f.status ? `${ok ? "Working" : "Failing"} · ${f.status.replace(/^(ok|error): /, "")}` : "Not fetched yet", f.checked_at ? h("span", { class: "muted" }, ` · checked ${fmtAgo(f.checked_at)}`) : null),
        ed ? btn("Refresh now", { cls: "sm", icon: "refresh", onclick: async () => {
          try { await api("POST", `/api/feeds/${f.id}/refresh`, {}); toast("Feed refreshed.", "ok"); reload(f.jid); } catch (e) { /* toasted */ }
        } }) : null),
      f.headlines.length ? h("div", { class: "jl-headlines" }, h("div", { class: "small muted" }, "Current headlines"), h("ol", null, f.headlines.map((t) => h("li", null, t)))) : null,
      menusBox(s, f.jid, nodes, reload),
      h("div", { class: "jl-head-grid" }, field("Feed URL", url), field("Object ID", jid)),
      h("div", { class: "grid-2" }, field("Show as", mode), field("Title", title)),
      h("div", { class: "grid-3" }, field("Stories", max), field("Story text", itemText), field("Name", name)),
      showTime.el, statik.el, enabled.el,
      f.mode === "menu" && f.story_ids.length ? h("div", { class: "small muted" }, `Stories use object IDs ${f.story_ids.map(hex4).join(", ")}.`) : null),
    ed ? h("div", { class: "card-foot" }, btn("Delete feed", { cls: "danger", icon: "trash", onclick: async () => {
      if (!(await confirmDialog("Delete this feed? Links to it are removed from menus.", { danger: true, okText: "Delete" }))) return;
      try { await api("DELETE", `/api/feeds/${f.id}`); toast("Deleted.", "ok"); reload(0); } catch (e) { /* toasted */ }
    } }), h("span", { class: "spacer" }), btn("Save", { cls: "primary", icon: "check", onclick: async () => {
      const body = { url: url.value, mode: mode.value, title: title.value, name: name.value, max_items: +max.value, item_text: itemText.value,
        show_time: showTime.box.checked, static: statik.box.checked, enabled: enabled.box.checked };
      const nj = parseJid(jid.value);
      if (nj !== f.jid) body.jid = nj;
      try { const r = await api("PUT", `/api/feeds/${f.id}`, body); if (r.error) toast("Saved, but the feed couldn't be read: " + r.error, "error"); else toast("Saved - click Apply to publish.", "ok"); reload(nj ?? f.jid); } catch (e) { /* toasted */ }
    } })) : null));
}

/* ---------- receiver preview ---------- */

function renderSegs(segs, { intro = true } = {}) {
  const out = [];
  let hl = false;
  for (const sg of segs || []) {
    if (sg[0] === "t") out.push(hl ? h("mark", null, sg[1]) : sg[1]);
    else if (sg[0] === "br") out.push(h("br"));
    else if (sg[0] === "hl") hl = sg[1];
    else if (sg[0] === "intro" && intro) out.push(h("span", { class: "jl-intro", title: "End of introduction" }));
  }
  return out;
}

async function servicePreview(root, s, selParam) {
  const p = await api("GET", `/api/services/${s.id}/preview`);
  const objs = p.objects;
  let start = parseJid(selParam);
  if (start === null || Number.isNaN(start) || !objs[start]) start = 0;
  const history_ = start === 0 ? [0] : [0, start];
  let cursor = 0;
  const screen = h("div", { class: "lcd", tabindex: 0, "aria-label": "Receiver screen" });
  const info = h("div", { class: "stack" });
  const crumbs = h("div", { class: "small muted mono" });
  const cur = () => history_[history_.length - 1];
  const open = (jid) => { history_.push(jid); cursor = 0; draw(); };
  const back = () => { if (history_.length > 1) { history_.pop(); cursor = 0; draw(); } };
  const draw = () => {
    clear(screen);
    const o = objs[cur()];
    crumbs.textContent = history_.map(hex4).join(" › ");
    history.replaceState(null, "", `#/services/${s.id}/preview/${hex4(cur())}`);
    if (!o) {
      put(screen, h("div", { class: "lcd-title" }, "Receiving - please wait"), h("div", { class: "lcd-body muted" }, `Object ${hex4(cur())} is not in the carousel.`));
    } else if (o.type === "menu") {
      put(screen, h("div", { class: "lcd-title" }, o.title));
      const list = h("div", { class: "lcd-items" });
      o.items.forEach((it, i) => {
        const avail = !!objs[it.target];
        list.appendChild(h("div", { class: "lcd-item" + (i === cursor ? " on" : "") + (avail ? "" : " na"), onclick: () => { cursor = i; if (avail) open(it.target); else draw(); } },
          avail ? it.label : `[${it.label}]`));
      });
      screen.appendChild(list);
    } else if (o.type === "text") {
      put(screen, h("div", { class: "lcd-scroll" }, h("div", { class: "lcd-title" }, o.title), h("div", { class: "lcd-body" }, renderSegs(o.body_segs))));
    } else if (o.type === "title") {
      put(screen, h("div", { class: "lcd-ticker" }, renderSegs(o.title_segs)));
    } else if (o.type === "list") {
      const cols = Math.max(...o.rows.map((r) => r.length));
      put(screen, h("div", { class: "lcd-title" }, o.title), h("div", { class: "lcd-scroll" }, h("table", { class: "lcd-table" }, h("tbody", null,
        o.rows.map((r) => h("tr", null, [...r, ...Array(cols - r.length).fill("")].map((c) => h("td", null, c))))))));
    }
    clear(info);
    if (o) {
      const kv = (k, v) => [h("dt", null, k), h("dd", null, v)];
      put(info, h("dl", { class: "kv" },
        kv("Object", `${hex4(o.id)} · ${TYPE_META[o.type].label}`),
        kv("On air size", `${fmtBytes(o.size)}${o.compressed ? ` (deflated from ${fmtBytes(o.plain_bytes)})` : ""}`),
        kv("Hierarchy level", p.depth[String(o.id)] ?? "not reachable"),
        kv("Revision", o.revision), kv("Favourite allowed", o.static ? "yes" : "no"),
        o.expires ? kv("Expires", fmtDate(Date.parse(o.expires) / 1000)) : null,
        o.lifetime ? kv("Lifetime", `${o.lifetime} min after reception`) : null,
        o.language ? kv("Language", o.language) : null),
      o.links ? h("div", { class: "stack tight" }, h("div", { class: "small muted" }, "Button links"), o.links.map((l) => h("div", { class: "chip" }, icon("link"),
        `${l.label || l.type}: ${l.type === "jml" ? hex4(l.address) : l.address}`))) : null,
      isEditor() ? btn("Edit this object", { cls: "sm", icon: "edit", onclick: () => { location.hash = `#/services/${s.id}/content/${hex4(o.id)}`; } }) : null);
    }
  };
  screen.addEventListener("keydown", (e) => {
    const o = objs[cur()];
    if (e.key === "ArrowUp") { if (o && o.type === "menu") { cursor = Math.max(0, cursor - 1); draw(); } else screen.querySelector(".lcd-scroll")?.scrollBy(0, -40); e.preventDefault(); }
    if (e.key === "ArrowDown") { if (o && o.type === "menu") { cursor = Math.min(o.items.length - 1, cursor + 1); draw(); } else screen.querySelector(".lcd-scroll")?.scrollBy(0, 40); e.preventDefault(); }
    if (e.key === "Enter" && o && o.type === "menu" && o.items[cursor] && objs[o.items[cursor].target]) open(o.items[cursor].target);
    if (e.key === "Backspace" || e.key === "Escape" || e.key === "ArrowLeft") { back(); e.preventDefault(); }
  });
  const pad = h("div", { class: "lcd-pad" },
    iconBtn("arrowLeft", "Back", back),
    iconBtn("chevronUp", "Up", () => screen.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }))),
    iconBtn("chevronDown", "Down", () => screen.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }))),
    btn("OK", { cls: "sm", onclick: () => screen.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter" })) }),
    btn("Home", { cls: "sm ghost", onclick: () => { history_.splice(1); cursor = 0; draw(); } }));
  put(root,
    p.errors.length ? h("div", { class: "banner red" }, icon("alert"), h("div", null, h("b", null, "Not publishable yet"), h("ul", null, p.errors.slice(0, 10).map((e) => h("li", null, e.message))))) : null,
    p.warnings.length ? h("div", { class: "banner amber" }, icon("alert"), h("div", null, h("b", null, "Warnings"), h("ul", null, p.warnings.slice(0, 10).map((e) => h("li", null, e.message))))) : null,
    (p.errors.length || p.warnings.length) ? h("div", { class: "section-gap" }) : null,
    h("div", { class: "jl-preview" },
      h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", { class: "grow" }, h("h2", null, "Receiver"), h("p", null, "Your current edits, encoded and decoded again as a receiver sees them. Bracketed links aren't in the carousel."))),
        h("div", { class: "card-body stack" }, crumbs, screen, pad, h("div", { class: "small muted" }, "Keyboard: ↑ ↓ to move or scroll, Enter to open, Esc or ← to go back."))),
      h("div", { class: "card" }, h("div", { class: "card-head" }, h("h2", null, "This object")), h("div", { class: "card-body" }, info),
        p.estimate ? h("div", { class: "card-foot small muted" }, `Whole carousel: ${fmtBytes(p.estimate.stream_bytes)} · one pass takes ${fmtMinSec(p.estimate.cycle_seconds)} at ${s.bitrate} kbps`) : null)));
  draw();
  screen.focus();
}

/* ---------- service settings ---------- */

function serviceSettings(root, s) {
  const ed = isEditor();
  const name = inp(s.name, { maxlength: 64, disabled: !ed }), provider = inp(s.provider, { maxlength: 64, disabled: !ed });
  const enabled = toggle("Broadcast this service", !!s.enabled, { disabled: !ed });
  const path = inp(s.output_path, { class: "mono", disabled: !ed, placeholder: "/home/odr/ODR-mmbTools/config/journaline.dat" });
  const writeMode = sel(s.write_mode, [["inplace", "Overwrite in place (recommended - odr-dabmux keeps the file open)"], ["atomic", "Atomic replace (write temp file + rename)"]], { disabled: !ed });
  const bitrate = bitrateSelect(s.bitrate); bitrate.disabled = !ed;
  const addr = h("input", { type: "number", min: 1, max: 1023, value: s.packet_address, disabled: !ed });
  const toc = toggle("Send a table of contents (TOC) so receivers can drop removed objects from their cache", !!s.toc_enabled, { disabled: !ed });
  const tocTimeout = h("input", { type: "number", min: 0, max: 65535, value: s.toc_timeout, disabled: !ed });
  const comp = sel(s.compression, [["auto", "Deflate when it makes an object smaller (recommended)"], ["off", "Never compress"]], { disabled: !ed });
  const dg = toggle("Raw datagroup output (advanced - not readable by ODR-DabMux's packet input)", !!s.datagroup_mode, { disabled: !ed });
  const w = s.weights;
  const weight = (k) => h("input", { type: "number", min: k === "root_bonus" ? 0 : 1, max: 20, value: w[k], disabled: !ed });
  const wf = { menu: weight("menu"), title: weight("title"), list: weight("list"), text: weight("text"), toc: weight("toc"), root_bonus: weight("root_bonus") };
  const card = (title, sub, ...body) => h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", null, h("h2", null, title), h("p", null, sub))), h("div", { class: "card-body stack" }, body));
  const save = async () => {
    const body = { name: name.value, provider: provider.value, enabled: enabled.box.checked, output_path: path.value, write_mode: writeMode.value,
      bitrate: +bitrate.value, packet_address: +addr.value, toc_enabled: toc.box.checked, toc_timeout: +tocTimeout.value, compression: comp.value,
      datagroup_mode: dg.box.checked, weights: Object.fromEntries(Object.entries(wf).map(([k, el]) => [k, +el.value])) };
    try { await api("PATCH", `/api/services/${s.id}`, body); toast("Saved - click Apply to publish.", "ok"); refreshStatus(); route(); } catch (e) { /* toasted */ }
  };
  put(root, h("div", { class: "stack" },
    h("div", { class: "grid-2" },
      card("Service", "Shown in this panel. Receivers show the service label from the mux configuration.", field("Name", name, { max: 64 }), field("Provider", provider), enabled.el),
      card("Output", "The packet stream file odr-dabmux reads (its inputuri). Each service needs its own file.",
        field("Output file", h("div", { class: "row" }, path, isAdmin() ? btn("Browse…", { icon: "folder", onclick: async () => {
          const p = await fileBrowser({ title: "Where to write the Journaline stream", mode: "save", exts: "dat", start: path.value || "/home", filename: path.value.split("/").pop() || "journaline.dat" });
          if (p) path.value = p;
        } }) : null)), field("Write mode", writeMode))),
    h("div", { class: "grid-2" },
      card("Carousel", "Must match this service's subchannel and component in odr-dabmux.", field("Subchannel bitrate", bitrate), field("Packet address", addr), field("Compression", comp), dg.el),
      card("Repeats per cycle", "How often each kind of object is sent in one pass. Menus and tickers repeat more so navigation feels quick.",
        h("div", { class: "grid-3" }, field("Menus", wf.menu), field("Tickers", wf.title), field("Lists", wf.list)),
        h("div", { class: "grid-3" }, field("Text messages", wf.text), field("TOC", wf.toc), field("Extra for root menu", wf.root_bonus)))),
    card("Table of contents", "Management data that lists every object, so receivers can tidy their cache.", toc.el,
      field("Service timeout (minutes)", tocTimeout, { hint: "Receivers stop showing the service this long after losing reception. 0 = never." })),
    ed ? h("div", { class: "row" }, btn("Export JSON", { icon: "download", onclick: () => { location.href = `/api/services/${s.id}/export`; } }),
      btn("Import JSON…", { icon: "upload", onclick: () => importService(s) }),
      btn("Delete service", { cls: "danger", icon: "trash", onclick: async () => {
        if (!(await confirmDialog(`Delete "${s.name}" with all its objects and feeds? Its output file is left as it is - remove it from odr-dabmux too.`, { danger: true, okText: "Delete" }))) return;
        try { await api("DELETE", `/api/services/${s.id}`); toast("Service deleted.", "ok"); refreshStatus(); location.hash = "#/services"; } catch (e) { /* toasted */ }
      } }), h("span", { class: "spacer" }), btn("Save settings", { cls: "primary", icon: "check", onclick: save })) : null));
}

function importService(s) {
  const file = h("input", { type: "file", accept: ".json,application/json" });
  const m = modal({ title: `Import into ${s.name}`,
    body: h("div", { class: "stack" }, h("p", { class: "muted" }, "Load a JSON export of a Journaline service. This replaces every object and feed in this service; its settings are kept."), field("Export file", file)),
    foot: [btn("Cancel", { onclick: () => m.close() }), btn("Replace content", { cls: "danger", onclick: async () => {
      if (!file.files[0]) return toast("Choose a file.", "error");
      let data;
      try { data = JSON.parse(await file.files[0].text()); } catch (e) { return toast("That isn't valid JSON.", "error"); }
      try { const r = await api("POST", `/api/services/${s.id}/import`, { data }); m.close(); toast(`Imported ${r.objects} objects and ${r.feeds} feeds.`, "ok"); refreshStatus(); location.hash = `#/services/${s.id}/content`; } catch (e) { /* toasted */ }
    } })] });
}

/* ---------- per-service mux config ---------- */

async function serviceMux(root, s) {
  const sn = await api("GET", `/api/services/${s.id}/mux`);
  const m = s.mux;
  const ed = isEditor();
  const f = {
    service_uid: inp(m.service_uid, { class: "mono", disabled: !ed }), service_id: inp(m.service_id, { class: "mono", placeholder: "auto: ECC+EId+xx", disabled: !ed }),
    label: inp(m.label, { maxlength: 16, disabled: !ed }), short_label: inp(m.short_label, { maxlength: 8, disabled: !ed }),
    subchannel_uid: inp(m.subchannel_uid, { class: "mono", disabled: !ed }), subchannel_id: h("input", { type: "number", min: 0, max: 63, value: m.subchannel_id, disabled: !ed }),
    protection_profile: sel(m.protection_profile, [["EEP_A", "EEP_A"], ["EEP_B", "EEP_B (bitrate multiple of 32)"]], { disabled: !ed }),
    protection: sel(m.protection, [[1, "1 (strongest)"], [2, "2"], [3, "3"], [4, "4 (weakest)"]], { disabled: !ed }),
    component_uid: inp(m.component_uid, { class: "mono", disabled: !ed }),
    dscty: sel(m.dscty, [[5, "5 - Transparent data channel (most receivers)"], [44, "44 - Journaline (newer receivers only)"]], { disabled: !ed }),
  };
  const box = h("div");
  const fmt = formatSwitch((k) => put(clear(box), muxSnippet(sn, k)));
  put(box, muxSnippet(sn, fmt.get()));
  put(root, await stationLinksCard(s, m, ed), h("div", { class: "section-gap" }),
    h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", { class: "grow" }, h("h2", null, "Mux settings"), h("p", null, "Used only to build the example below - this tool never edits your odr-dabmux config.")),
      ed ? btn("Read my config…", { cls: "sm", icon: "import", onclick: async () => {
        const r = await readMuxConfig({ saveEnsemble: true });
        if (!r) return;
        if (r.free_subchannel_id !== null) f.subchannel_id.value = r.free_subchannel_id;
        toast(`Ensemble ${r.ensemble.ecc}.${r.ensemble.eid} saved; subchannel ids in use: ${r.subchannel_ids.join(", ") || "none"}. Save to use id ${f.subchannel_id.value}.`, "ok");
      } }) : null),
      h("div", { class: "card-body stack" },
        h("div", { class: "grid-4" }, field("Service uid", f.service_uid), field("Service id (32-bit)", f.service_id), field("Label", f.label, { max: 16 }), field("Short label", f.short_label, { max: 8 })),
        h("div", { class: "grid-4" }, field("Subchannel uid", f.subchannel_uid), field("Subchannel id", f.subchannel_id, { hint: "Must be unused in your mux" }), field("Protection profile", f.protection_profile), field("Protection level", f.protection)),
        h("div", { class: "grid-2" }, field("Component uid", f.component_uid), field("Component type (DSCTy)", f.dscty))),
      ed ? h("div", { class: "card-foot" }, h("span", { class: "spacer" }), btn("Save", { cls: "primary", onclick: async () => {
        const mux = { standalone: m.standalone, linked: m.linked }; for (const [k, el] of Object.entries(f)) mux[k] = el.value;
        mux.subchannel_id = +mux.subchannel_id; mux.protection = +mux.protection; mux.dscty = +mux.dscty;
        try { await api("PATCH", `/api/services/${s.id}`, { mux }); toast("Saved.", "ok"); route(); } catch (e) { /* toasted */ }
      } })) : null),
    h("div", { class: "section-gap" }),
    h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", { class: "grow" }, h("h2", null, "Example entries"), h("p", null, `Packet size ${sn.packet_size} bytes at ${s.bitrate} kbps.`)), fmt.el),
      h("div", { class: "card-body stack" }, sn.warnings.map((w) => h("div", { class: "banner amber" }, icon("alert"), w)), box)));
}

async function stationLinksCard(s, m, ed) {
  // where listeners find this Journaline service: its own data service, and/or attached to audio stations
  const settings = await api("GET", "/api/settings");
  let linked = (m.linked || []).map((l) => ({ ...l }));
  const standalone = toggle("Separate data service - its own entry in receivers' station lists", m.standalone !== false, { disabled: !ed });
  const list = h("div", { class: "stack tight" });
  const known = settings.mux_services || [];
  const picker = h("div", { class: "row wrap jl-station-picker" });
  const draw = () => {
    clear(list);
    if (!linked.length) list.appendChild(h("div", { class: "small muted" }, "Not attached to any station."));
    linked.forEach((l, i) => list.appendChild(h("div", { class: "jl-parent-row" }, icon("radio"),
      h("span", { class: "grow ellipsis" }, h("b", null, l.label || l.uid), h("span", { class: "muted mono" }, `  ${l.uid}`)),
      ed ? iconBtn("x", "Detach from this station", () => { linked.splice(i, 1); draw(); }) : null)));
    clear(picker);
    if (!ed) return;
    const avail = known.filter((k) => !linked.some((l) => l.uid === k.uid) && k.uid !== m.service_uid);
    if (avail.length) {
      const pick = sel("", [["", "Attach to a station from your config…"], ...avail.map((k) => [k.uid, `${k.label || k.uid}  (${k.uid}${k.id ? ", " + k.id : ""})`])]);
      pick.addEventListener("change", () => { const k = avail.find((x) => x.uid === pick.value); if (k) { linked.push({ uid: k.uid, label: k.label }); draw(); } });
      picker.appendChild(pick);
    }
    const uid = inp("", { class: "mono", placeholder: "or type a service uid, e.g. srv-radio1", maxlength: 64 });
    picker.append(uid, btn("Attach", { cls: "sm ghost", icon: "plus", onclick: () => {
      const v = uid.value.trim();
      if (!v) return;
      if (!linked.some((l) => l.uid === v)) linked.push({ uid: v, label: (known.find((k) => k.uid === v) || {}).label || "" });
      draw();
    } }));
  };
  draw();
  return h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", { class: "grow" }, h("h2", null, "Where listeners find it"),
    h("p", null, "Attach Journaline to your audio stations and receivers offer it while someone listens to them (usually as a \"Journaline\" or info button). It can also be its own data service, or both.")),
    ed ? btn("Read my config…", { cls: "sm", icon: "import", onclick: async () => {
      const r = await readMuxConfig({ saveEnsemble: true });
      if (r) { toast(`Found ${r.service_list.length} services in your config.`, "ok"); route(); }
    } }) : null),
    h("div", { class: "card-body stack" }, standalone.el,
      field("Attached to stations", list, { hint: known.length ? "Stations come from the last odr-dabmux config you read." : "Read your odr-dabmux config to pick stations from a list, or type their service uid." }),
      picker,
      h("div", { class: "small muted" }, "All attached stations share the same Journaline subchannel, so the content is only sent once.")),
    ed ? h("div", { class: "card-foot" }, h("span", { class: "spacer" }), btn("Save", { cls: "primary", onclick: async () => {
      try { await api("PATCH", `/api/services/${s.id}`, { mux: { ...m, standalone: standalone.box.checked, linked } }); toast("Saved - update your odr-dabmux config with the entries below.", "ok"); route(); } catch (e) { /* toasted */ }
    } })) : null);
}

/* ============================== activity ============================== */

async function pageActivity(root) {
  setCrumbs("Activity");
  const [builds, st] = await Promise.all([api("GET", "/api/builds"), api("GET", "/api/status")]);
  const last = builds[0];
  const statusPill = (b) => b.status === "ok" ? h("span", { class: "pill green" }, "OK") : b.status === "warning" ? h("span", { class: "pill amber" }, "Warnings")
    : b.status === "running" ? h("span", { class: "pill muted" }, "Running") : h("span", { class: "pill red" }, "Failed");
  put(root, h("div", { class: "page-head" }, h("div", null, h("h1", null, "Activity"), h("p", null, "Carousel builds - on Apply, on the feed refresh schedule, and at start-up.")),
    h("span", { class: "spacer" }), st.can_apply ? btn("Apply now", { cls: "primary", icon: "zap", onclick: applyChanges }) : null));
  if (last) {
    const s = last.stats || {};
    const svcs = s.services || [];
    put(root, h("div", { class: "card" },
      h("div", { class: "card-head" }, h("div", { class: "grow" }, h("h2", null, "Latest build"), h("p", null, `${fmtDate(last.started_at)} · ${last.trigger}${last.username ? " by " + last.username : ""}`)), statusPill(last)),
      h("div", { class: "card-body stack" },
        last.message ? h("div", { class: "mono small" }, last.message) : null,
        svcs.length ? h("div", { class: "table-wrap" }, h("table", null,
          h("thead", null, h("tr", null, h("th", null, "Service"), h("th", null, "Objects"), h("th", null, "Per pass"), h("th", null, "Cycle"), h("th", null, "Worst wait"), h("th", null, "TOC rev."))),
          h("tbody", null, svcs.map((x) => h("tr", { class: "click", onclick: () => { location.hash = `#/services/${x.id}`; } },
            h("td", null, h("b", null, x.name), h("div", { class: "small muted mono" }, x.output_path)),
            h("td", null, x.objects, h("div", { class: "small muted" }, Object.entries(x.by_type).map(([t, v]) => `${v.count} ${TYPE_META[t].label.toLowerCase()}${v.count > 1 ? "s" : ""}`).join(" · "))),
            h("td", { class: "nowrap" }, fmtBytes(x.stream_bytes), h("div", { class: "small muted" }, `${x.bitrate} kbps`)),
            h("td", { class: "nowrap" }, fmtMinSec(x.cycle_seconds)),
            h("td", { class: "small" }, Object.entries(x.wait).map(([t, v]) => h("div", { class: "nowrap" }, `${TYPE_META[t].label}: ${fmtMinSec(v)}`))),
            h("td", { class: "mono" }, x.toc_revision)))))) : null,
        last.warnings && last.warnings.length ? h("div", { class: "banner amber" }, icon("alert"), h("div", { class: "grow" },
          h("div", { class: "row" }, h("b", null, `${last.warnings.length} warning(s)`), h("span", { class: "spacer" }),
            isEditor() && last.warnings.length > 1 ? btn("Dismiss all", { cls: "sm", onclick: () => dismissWarning(last.id, null) }) : null),
          h("ul", { class: "warn-list" }, last.warnings.map((w) => h("li", null, h("span", null, w),
            isEditor() ? btn("Dismiss", { cls: "sm", title: "Hide this warning on future builds too", onclick: () => dismissWarning(last.id, w) }) : null))))) : null,
        s.dismissed_warnings && isEditor() ? h("div", { class: "small muted row" }, `${s.dismissed_warnings} dismissed warning(s) hidden.`,
          btn("Show them again", { cls: "sm ghost", onclick: async () => {
            try { await api("POST", "/api/warnings/restore", {}); toast("Dismissed warnings will show again from the next build.", "ok"); } catch (e) { /* toasted */ }
          } })) : null,
        h("div", { class: "small muted" }, "Next feed refresh: ", st.next_refresh ? `${fmtDate(st.next_refresh)} (${fmtIn(st.next_refresh)})` : "—"))));
    put(root, h("div", { class: "section-gap" }));
  }
  put(root, h("div", { class: "card" }, h("div", { class: "card-head" }, h("h2", null, "History")),
    builds.length ? h("div", { class: "table-wrap" }, h("table", null, h("thead", null, h("tr", null, h("th", null, "When"), h("th", null, "Trigger"), h("th", null, "Status"), h("th", null, "Size"), h("th", null, "Details"))),
      h("tbody", null, builds.map((b) => h("tr", null, h("td", { class: "nowrap" }, fmtDate(b.started_at)), h("td", null, b.trigger, b.username ? h("span", { class: "muted" }, " · " + b.username) : null),
        h("td", null, statusPill(b)), h("td", { class: "nowrap" }, b.stats && b.stats.stream_bytes ? fmtBytes(b.stats.stream_bytes) : "—"),
        h("td", { class: "small" }, b.message, b.warnings && b.warnings.length ? h("span", { class: "muted" }, ` · ${b.warnings.length} warning(s)`) : null))))))
      : h("div", { class: "card-body muted" }, "Nothing published yet - make your changes and click Apply.")));
}

/* ============================== mux config (all services) ============================== */

async function pageMux(root) {
  setCrumbs("Mux config");
  const [services, settings] = await Promise.all([api("GET", "/api/services"), api("GET", "/api/settings")]);
  const snippets = await Promise.all(services.map((s) => api("GET", `/api/services/${s.id}/mux`)));
  const ens = settings.ensemble || {};
  const box = h("div");
  const merged = { info: {}, json: { services: {}, subchannels: {}, components: {} }, warnings: [] };
  for (const sn of snippets) {
    for (const sec of ["services", "subchannels", "components"]) {
      if (sn.info[sec]) merged.info[sec] = (merged.info[sec] ? merged.info[sec] + "\n" : "") + sn.info[sec];
      Object.assign(merged.json[sec], sn.json[sec] || {});
    }
  }
  for (const sec of ["services", "subchannels", "components"]) if (!Object.keys(merged.json[sec]).length) delete merged.json[sec];
  const draw = (fmt) => {
    clear(box);
    if (!services.length) return put(box, h("div", { class: "muted" }, "Add a Journaline service first."));
    put(box, muxSnippet(merged, fmt));
  };
  const fmt = formatSwitch(draw);
  draw(fmt.get());
  const clashes = [];
  const seen = {};
  for (const s of services) {
    const k = s.mux.subchannel_id;
    if (seen[k]) clashes.push(`${s.name} and ${seen[k]} both use subchannel id ${k}.`);
    seen[k] = s.name;
  }
  put(root,
    h("div", { class: "page-head" }, h("div", null, h("h1", null, "Multiplexer configuration"),
      h("p", null, "Entries for every Journaline service, ready for your odr-dabmux config. Each service has its own subchannel, packet address and output file.")),
      h("span", { class: "spacer" }), isEditor() ? btn("Read my config…", { icon: "import", onclick: async () => {
        const r = await readMuxConfig({ saveEnsemble: true });
        if (r) { toast(`Ensemble ${r.ensemble.ecc}.${r.ensemble.eid} saved. Subchannel ids in use: ${r.subchannel_ids.join(", ") || "none"}; ${r.free_subchannel_id} is free.`, "ok"); route(); }
      } }) : null),
    h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", null, h("h2", null, "Ensemble"), h("p", null, "Used to suggest each service's 32-bit data service id."))),
      h("div", { class: "card-body" }, h("dl", { class: "kv" }, h("dt", null, "ECC"), h("dd", { class: "mono" }, ens.ecc || "not set"), h("dt", null, "EId"), h("dd", { class: "mono" }, ens.eid || "not set")))),
    h("div", { class: "section-gap" }),
    clashes.map((c) => h("div", { class: "banner red" }, icon("alert"), c)),
    h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", { class: "grow" }, h("h2", null, "All services"),
      h("p", null, services.map((s) => `${s.name}: subchannel ${s.mux.subchannel_id}, address 0x${s.packet_address.toString(16)}, ${s.bitrate} kbps`).join(" · "))), fmt.el),
      h("div", { class: "card-body stack" }, snippets.flatMap((sn) => sn.warnings).map((w) => h("div", { class: "banner amber" }, icon("alert"), w)), box)));
}

/* ============================== users ============================== */

async function pageUsers(root) {
  setCrumbs("Users");
  const users = await api("GET", "/api/users");
  put(root, h("div", { class: "page-head" }, h("div", null, h("h1", null, "Users"),
    h("p", null, "Administrators manage everything. Editors manage the services, their content and feeds, and can publish.")),
    h("span", { class: "spacer" }), btn("Add user", { cls: "primary", icon: "plus", onclick: () => userEditor(null) })),
  h("div", { class: "card" }, h("div", { class: "table-wrap" }, h("table", null,
    h("thead", null, h("tr", null, h("th", null, "User"), h("th", null, "Role"), h("th", null, "Status"), h("th", null, "Last login"))),
    h("tbody", null, users.map((u) => h("tr", { class: "click", onclick: () => userEditor(u) },
      h("td", null, h("div", { class: "row" }, h("span", { class: "avatar" }, initials(u.display_name || u.username)), h("div", null, h("b", null, u.display_name || u.username), h("div", { class: "small muted" }, u.username)))),
      h("td", null, h("span", { class: "chip " + (u.role === "admin" ? "accent" : "blue") }, ROLE_LABEL[u.role])),
      h("td", null, u.disabled ? h("span", { class: "chip red" }, "Disabled") : u.locked ? h("span", { class: "chip amber" }, "Locked") : u.must_change_pw ? h("span", { class: "chip" }, "Temp. password") : h("span", { class: "chip green" }, "Active")),
      h("td", { class: "small muted nowrap" }, fmtAgo(u.last_login)))))))));
}

function userEditor(u) {
  const isNew = !u;
  u = u || { username: "", display_name: "", role: "editor", disabled: 0 };
  const username = inp(u.username, { disabled: !isNew, autocomplete: "off" });
  const dn = inp(u.display_name);
  const role = sel(u.role, [["editor", "Editor"], ["admin", "Administrator"]]);
  const pw = h("input", { type: "password", autocomplete: "new-password", placeholder: "Leave empty to generate one" });
  const disabled = toggle("Account disabled", !!u.disabled);
  const m = modal({
    title: isNew ? "Add user" : `Edit ${u.username}`, wide: true,
    body: h("div", { class: "stack" }, h("div", { class: "grid-2" }, field("Username", username), field("Display name", dn)),
      h("div", { class: "grid-2" }, field("Role", role), isNew ? field("Initial password", pw, { hint: "They must change it at first login." }) : h("div")),
      isNew ? null : disabled.el,
      isNew ? null : h("div", { class: "row wrap" },
        btn("Reset password", { cls: "sm", icon: "lock", onclick: async () => {
          if (!(await confirmDialog(`Generate a new temporary password for ${u.username}? Their sessions are signed out.`, { okText: "Reset" }))) return;
          try { const r = await api("POST", `/api/users/${u.id}/reset-password`, {}); showSecret("Temporary password", `Give this to ${u.username}. They must change it at next login.`, r.password); } catch (e) { /* toasted */ }
        } }),
        u.locked ? btn("Unlock", { cls: "sm", onclick: async () => { try { await api("PATCH", `/api/users/${u.id}`, { unlock: true }); toast("Unlocked.", "ok"); m.close(); route(); } catch (e) { /* toasted */ } } }) : null)),
    foot: [isNew ? null : btn("Delete", { cls: "danger", icon: "trash", onclick: async () => {
      if (!(await confirmDialog(`Delete user ${u.username}?`, { danger: true, okText: "Delete" }))) return;
      try { await api("DELETE", `/api/users/${u.id}`); m.close(); route(); } catch (e) { /* toasted */ }
    } }), h("span", { class: "spacer" }), btn("Cancel", { onclick: () => m.close() }), btn(isNew ? "Create user" : "Save", { cls: "primary", onclick: async () => {
      const body = { display_name: dn.value, role: role.value };
      try {
        if (isNew) {
          const r = await api("POST", "/api/users", { ...body, username: username.value, password: pw.value });
          m.close();
          if (r.password) showSecret("User created", `Give this temporary password to ${username.value}. They must change it at first login.`, r.password);
          else toast("User created.", "ok");
        } else {
          await api("PATCH", `/api/users/${u.id}`, { ...body, disabled: disabled.box.checked });
          m.close(); toast("Saved.", "ok");
        }
        route();
      } catch (e) { /* toasted */ }
    } })],
  });
}

/* ============================== settings ============================== */

async function pageSettings(root) {
  setCrumbs("Settings");
  const s = await api("GET", "/api/settings");
  const muxName = inp(s.mux_name, { maxlength: 64, placeholder: "e.g. North Region DAB" });
  const ecc = inp(s.ensemble.ecc, { class: "mono", maxlength: 2, placeholder: "e1" });
  const eid = inp(s.ensemble.eid, { class: "mono", maxlength: 4, placeholder: "c185" });
  const rmin = h("input", { type: "number", min: 5, max: 1440, value: s.refresh_minutes });
  const tzList = h("datalist", { id: "tzlist" }, (Intl.supportedValuesOf ? Intl.supportedValuesOf("timeZone") : []).map((z) => h("option", { value: z })));
  const tz = inp(s.timezone, { list: "tzlist", placeholder: "Server default (" + Intl.DateTimeFormat().resolvedOptions().timeZone + ")" });
  const priv = toggle("Allow feed URLs on private networks (localhost, 10.x, 192.168.x …)", s.allow_private_urls);
  const sess = h("input", { type: "number", min: 1, max: 168, value: s.session_hours });
  const save = async () => {
    try {
      await api("PUT", "/api/settings", { mux_name: muxName.value, ensemble: { ecc: ecc.value, eid: eid.value }, refresh_minutes: +rmin.value,
        timezone: tz.value.trim(), allow_private_urls: priv.box.checked, session_hours: +sess.value });
      toast("Settings saved.", "ok"); refreshStatus();
      if (muxName.value !== S.muxName) { S.muxName = muxName.value; setTitle(); renderShell(); }
    } catch (e) { /* toasted */ }
  };
  const card = (title, sub, ...body) => h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", null, h("h2", null, title), h("p", null, sub))), h("div", { class: "card-body stack" }, body));
  put(root, h("div", { class: "page-head" }, h("div", null, h("h1", null, "Settings")), h("span", { class: "spacer" }), btn("Save settings", { cls: "primary", icon: "check", onclick: save })),
    h("div", { class: "stack" },
      h("div", { class: "grid-2" },
        card("General", "Shown on the login screen, in the browser tab and under the logo, so you can see at a glance which multiplex you're editing.", field("Multiplex name", muxName)),
        card("Ensemble", "Used to suggest each service's data service id in the mux config. Read them from your config on the Mux config page.",
          h("div", { class: "grid-2" }, field("ECC", ecc), field("EId", eid)))),
      h("div", { class: "grid-2" },
        card("Feeds and refresh", "Every interval, RSS feeds are re-read and every carousel is rebuilt from the last applied state - so feed stories and expiries go on air without an Apply.",
          field("Refresh every (minutes)", rmin), field("Timezone", tz, { hint: "Used for feed times and for expiry times you enter." }), tzList),
        card("Security", "Network access and sessions.", priv.el, h("div", { class: "small muted" }, "Leave off unless your feeds are served from your own LAN - it stops users probing internal services through URL fetching."),
          field("Session length (hours)", sess))),
      updatesCard(), creditsCard()));
}
// Packet size for a bitrate: the largest DAB packet that fits a whole number of
// times into one 24 ms frame (bitrate x 3 bytes). Mirrors build.packet_size_for.
const packetSize = (kbps) => [96, 72, 48, 24].find((s) => (kbps * 3) % s === 0);

function bitrateSelect(value) {
  const opts = [];
  for (let k = 8; k <= 96; k += 8) {
    const ps = packetSize(k);
    opts.push([k, `${k} kbps · ${ps}-byte packets${ps === 24 && k > 8 ? " (less efficient)" : ""}`]);
  }
  return sel(value, opts);
}
const CREDITS = [
  ["Fraunhofer IIS", "Journaline®, specified in ETSI TS 102 979; their decoder was used to verify the output", "https://www.iis.fraunhofer.de/journaline"],
  ["Opendigitalradio", "ODR-mmbTools and ODR-DabMux, which carries the Journaline packet stream", "https://github.com/Opendigitalradio"],
  ["Jan van Katwijk", "Qt-DAB, whose copy of the Fraunhofer decoder is used by the test tool", "https://github.com/JvanKatwijk/qt-dab"],
  ["Rían Mac Fhionnghaile", "MPBNL Journaline WebFrontend and the MPBNL SPI WebFrontend it is built from", "https://github.com/ryanginn/ODR-Journaline-Encoder"],
]

function creditsCard() {
  return h("div", { class: "card" }, h("div", { class: "card-head" }, icon("heart"), h("div", null, h("h2", null, "Credits"),
    h("p", null, `MPBNL Journaline WebFrontend ${S.version} is free software (GPLv3), built on the work of:`))),
  h("div", { class: "table-wrap" }, h("table", null, h("tbody", null, CREDITS.map(([who, what, url]) => h("tr", null,
    h("td", { class: "nowrap" }, h("b", null, who)), h("td", { class: "small" }, what),
    h("td", { class: "nowrap" }, h("a", { href: url, target: "_blank", rel: "noopener noreferrer" }, url.replace("https://", "")))))))));
}

function fmtMinSec(sec) {
  if (sec == null) return "—";
  const t = Math.round(sec), m = Math.floor(t / 60), s = t % 60;
  return m ? `${m} min ${s} s` : `${s} s`;
}

async function dismissWarning(buildId, warning) {
  try {
    await api("POST", `/api/builds/${buildId}/dismiss`, { warning });
    toast(warning === null ? "Warnings dismissed." : "Warning dismissed - it won't flag the status on future builds.", "ok");
    refreshStatus(); route();
  } catch (e) { /* toasted */ }
}

function updatesCard() {
  const body = h("div", { class: "card-body stack" }, h("span", { class: "muted" }, "Loading…"));
  const foot = h("div", { class: "card-foot" });
  const card = h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", null, h("h2", null, "Updates"),
    h("p", null, "Update the generator from its git source in one click. Configuration and data are kept."))), body, foot);
  let timer = null, startCommit = null, wasRunning = false;
  const short = (c) => (c && c !== "unknown" ? c.slice(0, 7) : "unknown");
  const request = async (action) => {
    if (action === "apply" && !(await confirmDialog("Download and install the latest version now? The service restarts and this page reconnects automatically; the Journaline output files are not interrupted.", { okText: "Update now" }))) return;
    try { await api("POST", "/api/update", { action }); toast(action === "apply" ? "Update started…" : "Checking for updates…"); poll(1000); } catch (e) { /* toasted */ }
  };
  const draw = (u) => {
    const st = u.status || {};
    const busy = u.pending || st.state === "running";
    if (startCommit === null) startCommit = u.current_commit;
    clear(body); clear(foot);
    foot.classList.toggle("hidden", !u.enabled);
    if (!u.enabled) {
      put(body, h("div", { class: "banner amber" }, icon("info"), "One-click updates need the generator to be installed from a git checkout with install.sh."),
        h("dl", { class: "kv" }, h("dt", null, "Version"), h("dd", null, u.version)));
      return busy;
    }
    put(body,
      h("dl", { class: "kv" },
        h("dt", null, "Installed"), h("dd", { class: "mono" }, `${u.version} · ${short(u.current_commit)}`),
        h("dt", null, "Source"), h("dd", { class: "mono small" }, `${u.source} (${u.branch})`),
        h("dt", null, "Last check"), h("dd", null, st.checked_at ? fmtAgo(st.checked_at) : "never")),
      busy ? h("div", { class: "banner blue" }, h("span", { class: "spin" }), st.message || "Starting…")
        : st.state === "error" ? h("div", { class: "banner red" }, icon("alert"), st.message)
        : st.available ? h("div", { class: "banner green" }, icon("arrowUp"), `Update available: ${short(st.remote_commit)}`)
        : st.message ? h("div", { class: "small muted" }, st.message) : null);
    put(foot, btn("Check for updates", { icon: "refresh", disabled: busy, onclick: () => request("check") }),
      btn("Update now", { cls: "primary", icon: "zap", disabled: busy, onclick: () => request("apply") }));
    return busy;
  };
  const poll = async (delay = 0) => {
    clearTimeout(timer);
    if (delay) { timer = setTimeout(() => poll(), delay); return; }
    if (!card.isConnected && startCommit !== null) return;
    let u;
    try { u = await api("GET", "/api/update", undefined, { quiet: true }); }
    catch (e) { if (wasRunning) timer = setTimeout(() => poll(), 2000); return; } // service restarting
    const busy = draw(u);
    if (wasRunning && !busy && u.current_commit !== startCommit) {
      toast(`Updated to ${short(u.current_commit)} - reloading.`, "ok");
      setTimeout(() => location.reload(), 1500);
      return;
    }
    wasRunning = busy;
    if (busy) timer = setTimeout(() => poll(), 2000);
  };
  poll();
  return card;
}

/* ============================== audit / account ============================== */

async function pageAudit(root, _parts, offset = 0) {
  setCrumbs("Audit log");
  const rows = await api("GET", `/api/audit?offset=${offset}`);
  const more = btn("Load more", { onclick: async () => {
    const next = await api("GET", `/api/audit?offset=${offset + rows.length}`);
    next.forEach((r) => tbody.appendChild(auditRow(r))); rows.push(...next);
    if (next.length < 100) more.remove();
  } });
  const tbody = h("tbody", null, rows.map(auditRow));
  put(root, h("div", { class: "page-head" }, h("div", null, h("h1", null, "Audit log"), h("p", null, "Every sign-in and change, with user and address."))),
    h("div", { class: "card" }, h("div", { class: "table-wrap" }, h("table", null, h("thead", null, h("tr", null, h("th", null, "Time"), h("th", null, "User"), h("th", null, "Address"), h("th", null, "Action"), h("th", null, "Target"), h("th", null, "Details"))), tbody)),
      rows.length >= 100 ? h("div", { class: "card-foot" }, more) : null));
}
function auditRow(r) {
  const d = Object.keys(r.details || {}).length ? JSON.stringify(r.details) : "";
  return h("tr", null, h("td", { class: "nowrap small" }, fmtDate(r.ts)), h("td", null, r.username || h("span", { class: "muted" }, "—")), h("td", { class: "mono small" }, r.ip),
    h("td", null, h("span", { class: "chip" + (r.action.includes("failed") || r.action.includes("bad") ? " red" : "") }, r.action)), h("td", { class: "small" }, r.target),
    h("td", { class: "mono small muted ellipsis", title: d }, d.length > 120 ? d.slice(0, 120) + "…" : d));
}

function pageAccount(root) {
  setCrumbs("Account");
  const dn = inp(S.user.display_name);
  const cur = h("input", { type: "password", autocomplete: "current-password" });
  const p = h("input", { type: "password", autocomplete: "new-password" });
  const p2 = h("input", { type: "password", autocomplete: "new-password" });
  put(root, h("div", { class: "page-head" }, h("div", null, h("h1", null, "Your account"), h("p", null, `${S.user.username} · ${ROLE_LABEL[S.user.role]}`))),
    h("div", { class: "grid-2" },
      h("div", { class: "card" }, h("div", { class: "card-head" }, h("h2", null, "Profile")), h("div", { class: "card-body" }, field("Display name", dn)),
        h("div", { class: "card-foot" }, btn("Save", { cls: "primary", onclick: async () => {
          try { await api("PATCH", "/api/account", { display_name: dn.value }); S.user.display_name = dn.value; toast("Saved.", "ok"); renderShell(); } catch (e) { /* toasted */ }
        } }))),
      h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", null, h("h2", null, "Password"), h("p", null, "Other sessions are signed out when you change it."))),
        h("div", { class: "card-body stack" }, field("Current password", cur), field("New password", p, { hint: "At least 10 characters." }), field("Confirm new password", p2)),
        h("div", { class: "card-foot" }, btn("Change password", { cls: "primary", onclick: async () => {
          if (p.value !== p2.value) return toast("Passwords do not match.", "error");
          try { await api("POST", "/api/account/password", { current: cur.value, new: p.value }); toast("Password changed.", "ok"); cur.value = p.value = p2.value = ""; } catch (e) { /* toasted */ }
        } })))),
    h("div", { class: "section-gap" }), appearanceCard(),
    h("div", { class: "section-gap" }), h("div", { class: "small muted" }, `MPBNL Journaline WebFrontend ${S.version}`));
}

function appearanceCard() {
  const seg = h("div", { class: "segmented" });
  const draw = () => {
    clear(seg);
    for (const [k, label, ic] of THEMES) {
      seg.appendChild(h("button", { type: "button", class: getTheme() === k ? "on" : "", onclick: () => { setTheme(k); draw(); renderShell(); } },
        h("span", { class: "row" }, icon(ic), label)));
    }
  };
  draw();
  return h("div", { class: "card" }, h("div", { class: "card-head" }, h("div", null, h("h2", null, "Appearance"),
    h("p", null, "Saved in this browser. System follows your device's light/dark setting."))), h("div", { class: "card-body" }, seg));
}

boot();
