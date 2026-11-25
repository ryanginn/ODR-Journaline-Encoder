# Security

The security design is the one used by the MPBNL SPI WebFrontend, which this tool is built from, minus the station-owner role.

## Model

| Actor | Trust |
| :-- | :-- |
| **Administrator** | Fully trusted. Can choose output files, browse server directories (names only), read an odr-dabmux config on the server, manage users and allow fetching feeds from private networks. |
| **Editor** | Trusted with all Journaline services, their content and feeds, and can publish. No server filesystem access, users or global settings. |
| **Network** | Untrusted. Anyone who can reach the port must log in, except for first-run setup, which needs the token from the installer. |
| **Feeds** | Untrusted. RSS/Atom content from the internet is only ever turned into plain text. |

## Controls

- **Authentication**: scrypt password hashes (N=2¹⁵, r=8). Minimum 10 characters. An account locks for 15 minutes after 8 failures. Login attempts are rate-limited per IP. Temporary passwords must be changed at first login.
- **Sessions**: 256-bit random tokens, stored server-side only as SHA-256 hashes. The cookie is `HttpOnly` and `SameSite=Strict`, and `Secure` over HTTPS. Sessions expire after an absolute lifetime and after 8 hours idle.
- **CSRF**: every state-changing request needs a custom `X-Requested-With` header and, when logged in, a per-session CSRF token. Cross-origin `Origin`/`Referer` headers are rejected.
- **First-run takeover protection**: the first admin can only be created with a random setup token, written `0600` and removed once setup is done.
- **XSS**: the UI builds its DOM from text nodes only (no `innerHTML` or `eval`). A strict CSP (`script-src 'self'`, `style-src 'self'`, `frame-ancestors 'none'`) is set.
- **Feeds**: XML is parsed with `defusedxml` (no DTDs, so no XXE or entity expansion). HTML in stories is reduced to text, and scripts and styles are dropped. Feeds are size-capped (10 MB), at most 32 stories are kept, and story text is cut to fit Journaline's 4 092-byte object limit.
- **Broadcast content**: control characters in any text are dropped before encoding, so neither editors nor feeds can inject JML codes or escape sequences. Only the editor's documented markup (`**highlight**`, `---`, line breaks) creates them.
- **SSRF**: only `http(s)`. URLs with embedded credentials are refused. Every redirect hop is resolved and checked against private, loopback, link-local and reserved ranges unless an admin allows them. The connection is pinned to the checked address (no DNS rebinding).
- **Filesystem**: output files must be absolute `.dat` paths, each service must use its own file, symlinks are refused and files are opened with `O_NOFOLLOW`. Reading an odr-dabmux config is limited to regular files of at most 2 MB, for admins only.
- **SQL**: every query is parameterised. Column names come only from fixed server-side lists.
- **Service**: runs as an unprivileged user, never root, in a systemd sandbox (`NoNewPrivileges`, `ProtectSystem=full`, `PrivateTmp`, a syscall filter, `MemoryDenyWriteExecute`).
- **One-click updates**: the web service only writes a request file holding `check` or `apply`. A root-owned path unit runs the updater against the git source recorded at install time, so a compromised web service cannot choose what gets installed.
- **Audit log**: logins, failures and every change, with user and IP address.

## Residual risks

- **Use HTTPS.** Plain HTTP exposes passwords and session cookies. Use the built-in TLS or a reverse proxy (see the README).
- Admins can read server directory names. Give the admin role only to people who should have that access.

## Reporting

Please report vulnerabilities privately to the repository owner rather than in a public issue.
