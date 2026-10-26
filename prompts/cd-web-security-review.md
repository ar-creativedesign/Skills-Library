---
title: Live-browser web security review prompt (OWASP Top 10:2025)
version: 1.1
updated: 2026-10-26
works_with: Claude (Claude in Chrome, Claude desktop built-in browser, Claude Code + Playwright) and Google Antigravity (browser subagent + terminal)
tags: [security, owasp, audit, prompt]
---

# Live-browser web security review (OWASP Top 10:2025)

Copy everything below the line into a new agent session and fill in **Inputs**. Nothing else needs attaching.

This is a **non-destructive, defensive review**: configuration, transport, headers, client-side exposure, third-party risk and visible behaviour. It is **not a penetration test**. It does not try to exploit anything, and it lists what still needs an authorised pen test.

---

## Inputs

```yaml
TARGET_URL: https://example.com/
AUTHORISATION: "I own this site / I have written permission from <owner> to test it on <date>"   # REQUIRED
SCOPE: https://example.com and https://www.example.com only     # hosts you may send requests to
EXCLUDE: []                                  # paths not to touch, e.g. /admin, /checkout
TEST_LEVEL: passive                          # passive | light-active (see "Test levels")
LOGIN: none                                  # or "test account; I will sign in for you in the browser"
MAX_REQUEST_RATE: 1 per second
REPORT_FILE: reports/cd-web-security-review/report.md
EVIDENCE_DIR: reports/cd-web-security-review/evidence/
```

## Your role

You are a senior application security reviewer. Assess `TARGET_URL` against the **OWASP Top 10:2025** and the general hardening checks below. Use a **real browser** (load pages, watch network requests, inspect cookies and storage, run the Security Kit) plus **safe terminal commands** (`curl`, `openssl`, `dig`). Then write a prioritised report a development team can act on.

## Non-negotiable rules

1. **Authorisation first.** If `AUTHORISATION` is empty or vague, stop and ask. Only send requests to hosts in `SCOPE`, and never to other customers, subdomains or IP ranges you discover.
2. **No exploitation.** Never:
   - send attack payloads (script tags, SQL syntax, template expressions, path traversal, command injection)
   - fuzz, brute-force or guess credentials or IDs
   - bypass authentication, a WAF or a CAPTCHA
   - load-test, or run vulnerability scanners like sqlmap, nikto or Burp active scan
   - access, change or delete other users' data

   If you suspect a vulnerability, record it as **"Suspected – needs authorised pen test"** with the evidence that led you there.
3. **Live browser plus real responses.** Findings must come from what the running site actually returns: headers, cookies, rendered DOM, network traffic, served JavaScript. Source code in a repo is not evidence of what is deployed. If you have no browser or terminal, or the site blocks you, **stop and say so**. Do not report from memory.
4. **Evidence for every finding.** Each finding needs at least one of: the exact command and the relevant response lines, a screenshot path, or a measured value. Mark confidence as **Confirmed**, **Likely** or **Suspected**.
5. **Protect what you find.**
   - Never paste full secrets, tokens, keys, session IDs or personal data into the report. Show at most the first 6 characters plus the length.
   - If you find live credentials or personal data exposed, stop accessing that resource and alert the user at once. Do not use the credentials.
6. **Do no harm.**
   - Use GET/HEAD/OPTIONS only. No POST/PUT/DELETE except a form the user names.
   - No account creation, purchases or messages.
   - Stay at or below `MAX_REQUEST_RATE`.
   - Cookie banners: choose "Reject all / necessary only" or hide the banner with CSS. Never accept on the user's behalf.
7. **Bot protection.** On a 403, CAPTCHA or challenge page, **do not evade** it: no user-agent spoofing, proxies or stealth plugins. Use a browser the user controls, or stop and report it. A WAF block is itself a (positive) finding.
8. **Be honest about coverage.** State clearly what this review cannot establish, for example server-side injection, access control between users, business logic or logging.

## Test levels

| Level | What it adds | Requests |
| --- | --- | --- |
| `passive` (default) | Browse as a normal user. Read headers, cookies, storage, served JavaScript, DNS and TLS. Look at public files (`robots.txt`, `sitemap.xml`, `/.well-known/security.txt`). | Only what a normal visitor's browser would send, plus `curl -I`, `openssl`, `dig` |
| `light-active` | Everything in passive, plus: <br>• one GET each to the fixed list of common exposure paths below (no wordlists) <br>• one malformed-URL request and one 404 to see error handling <br>• `OPTIONS` to list allowed methods <br>• one request with a harmless foreign `Origin` header to test CORS <br>• one harmless marker string (`zxq7test<>"'`) in a search/query parameter to see whether it comes back unencoded <br>• one off-site value in an obvious redirect parameter (`?next=`, `?returnUrl=`) to `https://example.org` <br>• fetching source maps the scripts point to | About 30 extra requests in total, rate-limited |

The fixed exposure list for `light-active` (GET once each, stop on the first 429/403 pattern):

```
/.git/HEAD  /.git/config  /.env  /.env.production  /.DS_Store  /config.json  /appsettings.json
/server-status  /phpinfo.php  /backup.zip  /db.sql  /wp-config.php.bak  /.svn/entries
/swagger.json  /openapi.json  /api-docs  /graphql (GET only, no introspection query)
/actuator  /actuator/health  /admin  /.well-known/security.txt  /robots.txt  /sitemap.xml
```

A `200` with real content (not the SPA's index page served for every path) is a finding. **Compare the response body** with the 404/SPA fallback before reporting it.

## Use your tools (Claude or Antigravity)

| Action | Claude in Chrome / Claude desktop built-in browser | Claude Code (terminal) | Antigravity |
| --- | --- | --- | --- |
| Open page | `navigate` | Playwright MCP `browser_navigate` or a headed Playwright script | `browser_navigate` / `open_browser_url` |
| Run page JavaScript (Security Kit) | `javascript_tool` | `browser_evaluate` / `page.evaluate` | `execute_browser_javascript` |
| Network requests / console | `read_network_requests`, `read_console_messages` | `browser_network_requests`, `browser_console_messages` | the JavaScript Performance API (`performance.getEntriesByType('resource')`) via `execute_browser_javascript`; console via its page tools |
| Screenshot | `computer` → screenshot | `browser_take_screenshot` | `capture_browser_screenshot` (interactions are also recorded) |
| Headers, TLS, DNS | Ask the user to run the commands if you have no terminal, or use the Kit's `__sec.headers()` | `curl`, `openssl`, `dig` in the shell | the agent's terminal |

**Antigravity:** the browser subagent may not see this prompt. Pass it the exact steps and the **full Security Kit script** in each delegated task, and ask it to return the JSON. Run `curl`, `openssl` and `dig` in the main agent's terminal.

**No terminal (for example a browser-only Claude session):** use `__sec.headers()` for response headers. Tell the user which TLS and DNS checks were skipped, or give them the commands to run and paste back.

## Procedure

### Phase 1: Discover (passive)

1. Load `TARGET_URL`. Record:
   - the final URL after redirects, the protocol and the framework, if visible
   - whether it is an SPA
   - every host the page talks to (Kit `requestOrigins`, plus network requests)
2. List the pages to review: home, login/registration, any form, search, account area (if `LOGIN`), API endpoints seen in network traffic, error pages, `robots.txt`, `sitemap.xml`, `/.well-known/security.txt`.
3. Inventory third parties: analytics, tag managers, CDNs, CMS/API hosts, embeds and fonts. Note which load **before** cookie consent.

### Phase 2: Transport, TLS and DNS

Run these, replacing `example.com` with the target:

```bash
curl -sSI http://example.com/                           # plain HTTP should 301/308 to HTTPS
curl -sSI https://example.com/                          # response headers (security headers, cookies, server banners)
curl -sSI -H "Origin: https://evil.example" https://example.com/   # light-active: CORS reflection?
curl -sSI -X OPTIONS https://example.com/ | grep -iE "^(HTTP|allow|access-control-allow-methods)"   # light-active: allowed methods
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
for v in tls1 tls1_1 tls1_2 tls1_3; do echo -n "$v: "; openssl s_client -$v -connect example.com:443 -servername example.com </dev/null >/dev/null 2>&1 && echo accepted || echo refused; done
dig +short TXT example.com            # SPF
dig +short TXT _dmarc.example.com     # DMARC
dig +short CAA example.com            # CAA
dig +short DS example.com             # DNSSEC (if supported by the registrar)
```

Some `openssl` builds can't offer TLS 1.0/1.1. "Refused" for those can mean "not tested". Say which.

### Phase 3: In-browser review (every page type)

1. Inject the **Security Kit** (bottom of this prompt) with your JavaScript tool.
2. Run `await __sec.headers()`. Compare it with curl, and with each page type (the home page and API responses often differ).
3. Run `__sec.csp("<CSP header value>")` with the header from curl. With no argument it reads a `<meta>` CSP.
4. Run `await __sec.scan()` and keep the JSON. It covers:
   - inline scripts and event handlers
   - third-party scripts and styles without SRI
   - request origins and mixed content
   - cookies readable by JavaScript and session-like names
   - web storage tokens
   - forms: HTTP actions, password over GET, CSRF-like fields, password autocomplete
   - `target=_blank` without `noopener`
   - iframes and sandboxing
   - library versions
   - endpoints and possible secrets in served bundles and page state (redacted)
   - source map references
5. `light-active` only: run `await __sec.sourceMapsExposed(<sourceMapReferences>)`. A `200` with JSON content means the original source is public.
6. Use the browser's cookie view (DevTools Application tab, or `curl -I` `Set-Cookie` lines) to record the `Secure`, `HttpOnly`, `SameSite`, `Domain`, `Path` and expiry flags of every cookie. Repeat after login if `LOGIN` is set.
7. Look up every detected library version and every third-party script's library (from its URL) for known CVEs, using web search or the vendor advisories. Cite the advisory URL.
8. Watch the network tab while you use search, filters, forms and navigation. Note:
   - API calls carrying tokens in URLs
   - verbose error bodies
   - GraphQL or CMS endpoints called from the browser, and whether they need an auth token. A **read** token for published content is normal. Write or management tokens are not.
   - analytics or third-party requests that fire **before consent**

### Phase 4: Behaviour checks (by level)

- **Errors and exceptional conditions (A10).** `light-active`: request a non-existent path, and one malformed URL (for example `/%`). Look for stack traces, framework or version banners, debug pages, or a `200` returned for errors.
- **Reflection (A05, indicator only).** `light-active`: put `zxq7test<>"'` into one search or query parameter. Does it come back in the page or DOM **unencoded**? If so, record "Suspected – needs authorised pen test". Do not try script payloads.
- **Open redirect (A01).** `light-active`: for visible redirect parameters only, try `https://example.org` once and see whether the site redirects off-domain.
- **Authentication (A07)**, if `LOGIN` is set and the user signs in:
  - Is the login page HTTPS, with no credentials in URLs?
  - Does the session cookie have `Secure`, `HttpOnly` and `SameSite`?
  - Does the session ID change after login (compare the cookie name and length, not the value)?
  - Does logout invalidate the session (back button, then reload an account page)?
  - Is there an idle timeout?
  - Is there MFA?
  - Are password rules and lockout messaging sensible?
  - Are error messages generic? Test with **one** fake username, only if the user names the login form in Inputs.
- **Access control (A01)**, if `LOGIN` is set: copy two or three authenticated page and API URLs. Open them in a fresh logged-out context and check you get 401/403 or a redirect, not data. **Do not** change IDs to reach other users' records. List that as needing a pen test.
- **Clickjacking (A02).** Check `X-Frame-Options` or CSP `frame-ancestors` in the **header** (frame-ancestors is ignored in a meta tag).

### Phase 5: General protection checks

- **security.txt (RFC 9116):** present, with `Contact` and a future `Expires`.
- **Privacy and consent:** do analytics, tag managers or ad pixels load or set cookies before consent? Does the banner offer reject as easily as accept? (UK GDPR / PECR.)
- **Email spoofing protection:** SPF ends `-all` or `~all`; DMARC has `p=quarantine` or `p=reject`.
- **CAA records** restrict which CAs can issue certificates. **DNSSEC** is enabled where the registrar supports it.
- **Certificate:** valid chain, matches the host, at least 14 days to expiry, modern key. HSTS has `max-age` of at least 31536000 (preload if appropriate).
- **Information disclosure:**
  - `Server`, `X-Powered-By` or version banners
  - comments in HTML
  - source maps
  - internal hostnames, staging or `localhost` URLs in bundles or the CSP
  - `robots.txt` revealing admin paths
  - directory listing
- **Caching:** authenticated or personal pages send `Cache-Control: no-store`.
- **Subresource integrity:** third-party scripts and styles pinned with `integrity` and `crossorigin`, or self-hosted.
- **Embedded content:** third-party iframes are sandboxed where possible, and `postMessage` usage is reviewed if visible.

### Phase 6: Triage

Merge duplicates: one header missing on every page is **one** site-wide finding. Assign:

| Severity | Use when |
| --- | --- |
| Critical | Directly exploitable exposure seen with no further steps. Examples: live secret or private key in served JavaScript, `.git` or `.env` downloadable, database dump public, admin panel open without auth, credentials sent over HTTP. |
| High | Serious weakness likely to be exploitable or to remove a key protection. Examples: no HTTPS redirect or HSTS on a site with logins, session cookie without `HttpOnly`/`Secure`, CORS reflecting any origin with credentials, unencoded reflection of input (suspected XSS), known exploitable CVE in a loaded library, source maps exposing proprietary code with secrets. |
| Medium | Missing defence-in-depth that would limit impact. Examples: CSP with `'unsafe-inline'`/`'unsafe-eval'` or wildcards, no clickjacking protection, third-party scripts without SRI, outdated library with moderate CVEs, verbose errors, tracking before consent, no DMARC enforcement. |
| Low | Hardening and hygiene. Examples: version banners, missing Referrer-/Permissions-Policy, no `security.txt`, `target=_blank` without `noopener` on old-browser audiences, missing CAA. |
| Info | Observations with no direct risk, or positive notes. |

Give each finding an ID (`SEC-01`…), an **OWASP 2025 category**, and a **confidence** (Confirmed / Likely / Suspected).

### Phase 7: Verify

Re-test every finding once with a fresh request or page load. Drop anything you cannot reproduce. For "exposed file" findings, compare the body with the site's normal 404/SPA fallback. Re-check that no unredacted secret made it into your notes or the report.

### Phase 8: Report

Before writing, empty `reports/cd-web-security-review/` (that folder only) so nothing from an earlier run is left; old reports aren't kept. If `REPORT_FILE` was changed to another location, don't delete anything. Then write `REPORT_FILE` in Markdown and save screenshots and command output in `EVIDENCE_DIR`, using the template below. Build the action plan last and also write it as `actions.json` next to `REPORT_FILE`.

## OWASP Top 10:2025: what this review can and can't establish

| OWASP 2025 | What to check here | Outside this review (pen test) |
| --- | --- | --- |
| A01 Broken Access Control | Logged-out access to authenticated URLs/APIs; CORS policy; open redirects; directory listing; exposed admin paths | Horizontal/vertical privilege escalation, IDOR, forced browsing with wordlists |
| A02 Security Misconfiguration | Security headers, CSP quality, clickjacking, default/debug pages, exposed config files, HTTP methods, verbose errors, cloud/CMS endpoints exposed | Server/OS hardening, internal services |
| A03 Software Supply Chain Failures | Third-party script inventory, SRI, library versions vs CVEs, scripts from broad or unmaintained CDNs, tag managers | Build pipeline, dependency manifests, SBOM |
| A04 Cryptographic Failures | HTTPS everywhere, HSTS, TLS versions, certificate, mixed content, sensitive data in URLs, cookies without `Secure`, tokens in web storage | Data-at-rest encryption, key management |
| A05 Injection | Unencoded reflection of a harmless marker (indicator only), CSP strength, `unsafe-eval`, risky DOM patterns visible in served JS | Actual XSS/SQLi/command/template injection testing |
| A06 Insecure Design | Obvious design gaps seen while using the site: no rate-limit messaging on login, sensitive actions without confirmation, secrets in the client by design | Threat modelling, business logic abuse |
| A07 Authentication Failures | Login over HTTPS, cookie flags, session rotation, logout, timeout, MFA availability, generic errors | Credential stuffing resistance, brute-force lockout testing |
| A08 Software or Data Integrity Failures | SRI on third-party code, unsigned auto-update or config fetched over HTTP, CSP `script-src` breadth | Deserialisation, CI/CD integrity |
| A09 Security Logging & Alerting Failures | `security.txt` and a visible vulnerability-disclosure route; whether a WAF or monitoring is evident | Whether attacks are logged and alerted on (needs owner input) |
| A10 Mishandling of Exceptional Conditions | Error pages, stack traces, malformed-input handling, fail-open behaviour seen in responses | Fault injection, resource exhaustion |

## Report template

```markdown
# {Site name} – Security Review

{date} · OWASP Top 10:2025 · test level: {passive|light-active} · {agent/model}

> Authorisation: {as given}. Non-destructive review. Not a penetration test.

## Summary
{One-sentence verdict.} {N} findings: {c} critical, {h} high, {m} medium, {l} low, {i} info.
Start with: {the top 3 actions from the action plan, one line each}
{If any critical exposure was found: say so first, and that the user was alerted.}

## Scope and method
Hosts in scope, pages reviewed, date and time, tools (browser, curl/openssl/dig), test level, requests sent.

## Findings
| ID | Finding | Severity | Confidence | OWASP 2025 | Affected | Evidence | Fix (one line) |

## Security headers scorecard
| Header | Value seen | Verdict | Recommended value |
(HSTS, CSP, X-Content-Type-Options, X-Frame-Options / frame-ancestors, Referrer-Policy, Permissions-Policy, COOP, CORP, Cache-Control, Server / X-Powered-By)

## Cookies
| Name (no values) | Secure | HttpOnly | SameSite | Domain/Path | Expiry | Purpose | Set before consent? |

## Third-party and supply chain
| Origin | What loads | SRI | Before consent? | Version / known CVEs (with advisory link) |

## TLS, DNS and email
| Check | Result | Verdict |

## What passed
{Positive controls observed}

## Needs an authorised penetration test
{Suspected items, plus the OWASP areas this review cannot cover}

## Not covered
{Limits: no terminal, login not provided, WAF blocked, etc.}

## Action plan
| # | Priority | Action | Resolves | Owner | Effort | Agent-ready | Verify by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | P1 | {what to change and where} | SEC-03, SEC-07 | {owner} | S | Yes | {concrete check} |

**Effort:** S ≤ 2h · M ≤ 1 day · L ≤ 3 days · XL needs scoping. **Agent-ready:** Yes / Partial / No.
**Totals:** {n} actions resolve {N} findings · P1: {a} · P2: {b} · P3: {c} · P4: {d} · Agent-ready: {y} yes, {p} partial, {x} no
```

**How to write each finding:**
- **Finding:** what and where, with the measured value. Example: "CSP `connect-src` includes `http://localhost:8080` (development leftover)".
- **Evidence:** the command plus 1–3 response lines, a screenshot, or Kit output, with secrets redacted.
- **Fix (one line):** the change in a few words, for example "Add HSTS at the CDN". The detail goes in the action plan.
- Keep sentences short, use specifics rather than adjectives, use UK English, no padding, and never include full secrets.

**How to write the action plan** (the last section; build it from the triaged findings):
- **Group** findings that share a fix (same CSS rule, config file, component or import preset) into one action, and list every ID in **Resolves**. One finding can appear in more than one action if it needs several changes.
- **Every finding is covered.** Before finishing, check that each finding ID appears in at least one action. Info-only findings may be left out; say so under the table.
- **Priority:**
  - **P1:** any Critical, or a High with effort S
  - **P2:** the other Highs
  - **P3:** Medium
  - **P4:** Low, Info and tooling/process improvements

  An action takes the highest priority any of its findings would get. Within a priority, order by reach (how many pages, users or assets), then cheapest first.
- **Action:** imperative and specific: what to change, where (file, rule, setting or layer) and to what. Example: "Add `Strict-Transport-Security: max-age=31536000; includeSubDomains` at the CDN". Name the layer to change (CDN, nginx, framework config, CMS).
- **Owner:** Dev, DevOps/Hosting, Security or Vendor (third-party service).
- **Effort:** developer time for someone who knows the codebase, including testing. Not AI time. If unsure, round up and say why in the action.
- **Agent-ready:**
  - **Yes:** an agent with repo access can make and test the change.
  - **Partial:** an agent can draft it, but a person must decide, approve or do part of it. Give the reason in brackets.
  - **No:** it needs a person, the editor/tool UI or a third party. Give the reason in brackets.
- **Verify by:** a concrete check a person or a re-run can do, with the page, viewport, command or setting.
- **Needs an authorised penetration test:** add one action for the items in that section, owner Security, Agent-ready: No.
- Never put a full secret in an action or in `actions.json`.

**Also write `actions.json`** next to the report, with the same actions:

```json
{
  "skill": "<name> v<version>",
  "target": "<site or project>",
  "date": "YYYY-MM-DD",
  "actions": [
    {
      "id": "A1",
      "priority": "P1",
      "title": "<short title>",
      "action": "<the full action text>",
      "resolves": ["<ID>"],
      "owner": "<owner>",
      "effort": "S",
      "agent_ready": "yes",
      "agent_note": "",
      "files": ["<path:line>"],
      "verify": "<verify by>"
    }
  ]
}
```

## Security Kit (inject into each page with your JavaScript tool)

Paste the whole block as one JavaScript evaluation. It defines `window.__sec` and returns a confirmation string. `headers()`, `scan()` and `sourceMapsExposed()` are async: `await` them. `scan()` re-fetches the site's own script files (same origin) to look for secrets and endpoints. Pass `{fetchScripts:false}` to skip that.

```javascript
(() => {
  const S = {};
  const cap = (arr, n = 20) => ({ count: arr.length, samples: arr.slice(0, n) });
  const host = u => { try { return new URL(u, location.href).host; } catch (e) { return '?'; } };
  const sameSite = u => { try { const h = new URL(u, location.href).hostname, me = location.hostname; const base = d => d.split('.').slice(-2).join('.'); return base(h) === base(me); } catch (e) { return false; } };
  const redact = s => s.length <= 10 ? s.slice(0, 2) + '…' : s.slice(0, 6) + '…[' + s.length + ' chars]';
  const SECRET_PATTERNS = [
    ['AWS access key', /AKIA[0-9A-Z]{16}/g],
    ['Google API key (often public by design: check restrictions)', /AIza[0-9A-Za-z_\-]{35}/g],
    ['Stripe secret key', /sk_(live|test)_[0-9a-zA-Z]{20,}/g],
    ['Slack token', /xox[baprs]-[0-9A-Za-z-]{10,}/g],
    ['GitHub token', /gh[pousr]_[0-9A-Za-z]{30,}/g],
    ['Private key block', /-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----/g],
    ['JWT', /eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g],
    ['Bearer token literal', /Bearer\s+[A-Za-z0-9\-._~+/]{20,}=*/g],
    ['Generic secret assignment', /(api[_-]?key|secret|client[_-]?secret|access[_-]?token|auth[_-]?token|password)["']?\s*[:=]\s*["'][^"'\s]{12,}["']/gi],
  ];
  const findSecrets = (text, where) => { const out = []; for (const [label, re] of SECRET_PATTERNS) { const m = text.match(re) || []; [...new Set(m)].slice(0, 5).forEach(v => out.push(`${label} in ${where}: ${redact(v)}`)); } return out; };

  S.headers = async (url = location.href) => {
    const r = await fetch(url, { cache: 'no-store', credentials: 'same-origin', redirect: 'follow' });
    const h = {}; r.headers.forEach((v, k) => { h[k] = v; });
    const want = ['strict-transport-security', 'content-security-policy', 'content-security-policy-report-only', 'x-content-type-options', 'x-frame-options', 'referrer-policy', 'permissions-policy', 'cross-origin-opener-policy', 'cross-origin-resource-policy', 'cross-origin-embedder-policy', 'cache-control', 'server', 'x-powered-by', 'x-aspnet-version', 'via', 'access-control-allow-origin', 'access-control-allow-credentials'];
    const present = {}, missing = [];
    want.forEach(k => { if (h[k] !== undefined) present[k] = h[k].slice(0, 300); else missing.push(k); });
    const metaCsp = document.querySelector('meta[http-equiv="Content-Security-Policy" i]')?.content || null;
    return { url: r.url, status: r.status, present, missing, metaCsp: metaCsp && metaCsp.slice(0, 1500), note: 'Browser fetch hides some headers (e.g. set-cookie). Confirm with curl -sSI.' };
  };

  S.csp = (policy) => {
    const p = policy || document.querySelector('meta[http-equiv="Content-Security-Policy" i]')?.content || '';
    if (!p) return 'No CSP passed or found in a meta tag. Pass the header value: __sec.csp("<policy>")';
    const dirs = {}; p.split(';').map(s => s.trim()).filter(Boolean).forEach(d => { const [k, ...v] = d.split(/\s+/); dirs[k.toLowerCase()] = v; });
    const issues = [];
    const scriptSrc = dirs['script-src'] || dirs['default-src'] || [];
    if (!dirs['default-src']) issues.push('No default-src fallback');
    if (!dirs['script-src'] && !dirs['default-src']) issues.push('No script-src: scripts unrestricted');
    if (scriptSrc.includes("'unsafe-inline'") && !scriptSrc.some(s => /^'(nonce|sha\d{3})-/.test(s))) issues.push("script-src allows 'unsafe-inline' without nonce/hash (XSS mitigation largely lost)");
    if (scriptSrc.includes("'unsafe-eval'")) issues.push("script-src allows 'unsafe-eval'");
    Object.entries(dirs).forEach(([k, v]) => {
      v.forEach(s => {
        if (s === '*' || /^(https?:|data:|blob:)$/.test(s) && /script|default|object|frame/.test(k)) issues.push(`${k} allows broad source ${s}`);
        if (/^http:\/\//.test(s)) issues.push(`${k} allows insecure http source ${s}`);
        if (/localhost|127\.0\.0\.1|0\.0\.0\.0|\.local\b/.test(s)) issues.push(`${k} allows development host ${s} (leftover from development)`);
        if (/^\*\./.test(s) || /\/\/\*\./.test(s)) issues.push(`${k} allows wildcard subdomain ${s}`);
      });
    });
    if (!dirs['object-src'] && !(dirs['default-src'] || []).includes("'none'")) issues.push("object-src not set to 'none'");
    if (!dirs['base-uri']) issues.push('base-uri not set');
    if (!dirs['frame-ancestors']) issues.push('frame-ancestors not set (clickjacking protection relies on X-Frame-Options). Note: frame-ancestors is ignored in a <meta> CSP');
    if (!dirs['form-action']) issues.push('form-action not set');
    return { directives: Object.keys(dirs), issues };
  };

  S.scan = async (opts = {}) => {
    const R = { url: location.href, protocol: location.protocol, origin: location.origin };
    const scripts = [...document.scripts];
    R.inlineScripts = scripts.filter(s => !s.src && s.textContent.trim()).length;
    R.inlineEventHandlers = document.querySelectorAll('[onclick],[onload],[onerror],[onmouseover],[onsubmit],[onchange]').length;
    R.externalScripts = scripts.filter(s => s.src).map(s => ({ src: s.src.slice(0, 120), thirdParty: !sameSite(s.src), sri: !!s.integrity, crossorigin: s.crossOrigin || null }));
    R.thirdPartyScriptsWithoutSRI = cap(R.externalScripts.filter(s => s.thirdParty && !s.sri).map(s => s.src));
    R.stylesheetsThirdPartyNoSRI = cap([...document.querySelectorAll('link[rel=stylesheet][href]')].filter(l => !sameSite(l.href) && !l.integrity).map(l => l.href.slice(0, 120)));
    const res = performance.getEntriesByType('resource').map(e => e.name);
    const origins = {}; res.concat(R.externalScripts.map(s => s.src)).forEach(u => { const h = host(u); origins[h] = (origins[h] || 0) + 1; });
    R.requestOrigins = Object.entries(origins).sort((a, b) => b[1] - a[1]).map(([h, n]) => `${h} (${n})${sameSite('https://' + h) ? '' : ' [third party]'}`);
    R.mixedContent = cap(res.filter(u => location.protocol === 'https:' && /^http:\/\//.test(u)).concat([...document.querySelectorAll('[src^="http:"],[href^="http:"]')].filter(e => e.tagName !== 'A').map(e => e.outerHTML.slice(0, 120))));
    R.cookiesVisibleToJS = document.cookie ? document.cookie.split(';').map(c => c.trim().split('=')[0]) : [];
    R.sessionLikeCookiesVisibleToJS = R.cookiesVisibleToJS.filter(n => /sess|sid|auth|token|jwt|login|remember/i.test(n));
    const storage = [];
    for (const [label, st] of [['localStorage', localStorage], ['sessionStorage', sessionStorage]]) { try { for (let i = 0; i < st.length; i++) { const k = st.key(i), v = st.getItem(k) || ''; const tokeny = /token|jwt|auth|session|secret|password|bearer/i.test(k) || /^eyJ[A-Za-z0-9_-]{10,}\./.test(v); storage.push(`${label}.${k} (${v.length} chars)${tokeny ? ' TOKEN-LIKE: ' + redact(v) : ''}`); } } catch (e) { storage.push(label + ' not readable'); } }
    R.webStorage = cap(storage, 40);
    R.forms = [...document.forms].map(f => { const pw = f.querySelector('input[type=password]'); const hidden = [...f.querySelectorAll('input[type=hidden]')].map(i => i.name); return { action: (f.getAttribute('action') || '(same page)').slice(0, 100), method: (f.method || 'get').toUpperCase(), insecureAction: /^http:\/\//.test(f.action), hasPassword: !!pw, passwordAutocomplete: pw ? (pw.getAttribute('autocomplete') || '(none)') : null, passwordOverGET: !!pw && (f.method || 'get').toLowerCase() === 'get', csrfLikeField: hidden.some(n => /csrf|xsrf|token|authenticity|__requestverification/i.test(n)), hiddenFields: hidden.slice(0, 8) }; });
    R.blankTargetsWithoutNoopener = cap([...document.querySelectorAll('a[target=_blank]')].filter(a => !/noopener|noreferrer/.test(a.rel)).map(a => a.href.slice(0, 100)), 10);
    R.iframes = [...document.querySelectorAll('iframe')].map(f => ({ src: (f.src || '').slice(0, 100), sandbox: f.getAttribute('sandbox'), thirdParty: f.src ? !sameSite(f.src) : false }));
    const lib = {};
    try { if (window.jQuery?.fn?.jquery) lib.jquery = window.jQuery.fn.jquery; } catch (e) {}
    try { const app = document.querySelector('[data-v-app]')?.__vue_app__ || document.querySelector('#app')?.__vue_app__; if (app?.version) lib.vue = app.version; else if (window.Vue?.version) lib.vue = window.Vue.version; } catch (e) {}
    try { const ng = document.querySelector('[ng-version]'); if (ng) lib.angular = ng.getAttribute('ng-version'); else if (window.angular?.version) lib.angularjs = window.angular.version.full; } catch (e) {}
    try { const hook = window.__REACT_DEVTOOLS_GLOBAL_HOOK__; if (hook?.renderers?.size) lib.react = [...hook.renderers.values()].map(r => r.version).join(','); else if (window.React?.version) lib.react = window.React.version; } catch (e) {}
    try { if (window.next?.version) lib.next = window.next.version; if (window.__NUXT__) lib.nuxt = 'present'; } catch (e) {}
    try { if (window.bootstrap?.Tooltip?.VERSION) lib.bootstrap = window.bootstrap.Tooltip.VERSION; else if (window.jQuery?.fn?.tooltip?.Constructor?.VERSION) lib.bootstrap = window.jQuery.fn.tooltip.Constructor.VERSION; } catch (e) {}
    try { if (window._?.VERSION) lib.lodash = window._.VERSION; if (window.moment?.version) lib.moment = window.moment.version; if (window.DOMPurify?.version) lib.dompurify = window.DOMPurify.version; } catch (e) {}
    const gen = document.querySelector('meta[name=generator]')?.content; if (gen) lib.generator = gen;
    R.libraryVersions = lib;
    const secrets = [];
    for (const g of ['__NEXT_DATA__', '__NUXT__', '__INITIAL_STATE__', '__APOLLO_STATE__', '__ENV__', 'env', 'config', 'APP_CONFIG']) { try { if (window[g]) secrets.push(...findSecrets(JSON.stringify(window[g]).slice(0, 2e6), 'window.' + g)); } catch (e) {} }
    scripts.filter(s => !s.src).forEach((s, i) => secrets.push(...findSecrets(s.textContent, 'inline script #' + i)));
    secrets.push(...findSecrets(document.documentElement.outerHTML.replace(/<script[\s\S]*?<\/script>/gi, ''), 'page HTML'));
    const sourceMaps = [];
    if (opts.fetchScripts !== false) {
      for (const s of R.externalScripts.filter(x => !x.thirdParty).slice(0, 25)) {
        try { const t = await (await fetch(s.src, { cache: 'no-store' })).text(); secrets.push(...findSecrets(t, s.src.split('/').pop())); const m = t.match(/\/\/[#@]\s*sourceMappingURL=([^\s'"]+)\s*$/m); if (m && !/^data:/.test(m[1])) sourceMaps.push(new URL(m[1], s.src).href); const urls = t.match(/https?:\/\/[a-z0-9.-]+\.[a-z]{2,}(?::\d+)?(?:\/[^\s"'`)]*)?/gi) || []; urls.filter(u => /api|graphql|graphcms|hygraph|firebase|supabase|amazonaws|azure|internal|staging|dev\.|test\.|localhost/i.test(u)).forEach(u => (R.endpointsInBundles = R.endpointsInBundles || new Set()).add(u.slice(0, 120))); } catch (e) {}
      }
    }
    R.endpointsInBundles = R.endpointsInBundles ? [...R.endpointsInBundles].slice(0, 30) : [];
    R.possibleSecrets = cap([...new Set(secrets)], 30);
    R.sourceMapReferences = cap(sourceMaps, 10);
    R.note = 'Secrets are redacted. Never copy full values into the report. Google/Firebase browser keys are often public by design: report as Informational unless unrestricted.';
    return R;
  };

  S.sourceMapsExposed = async (urls) => { const out = []; for (const u of (urls || []).slice(0, 10)) { try { const r = await fetch(u, { method: 'GET', cache: 'no-store' }); out.push(`${u} -> ${r.status} ${r.headers.get('content-type') || ''}`); } catch (e) { out.push(`${u} -> blocked/error`); } } return out; };

  window.__sec = S;
  return 'security kit loaded: await __sec.headers(), __sec.csp(policy), await __sec.scan(), await __sec.sourceMapsExposed(urls)';
})();
```

**Kit reference**

| Call | Returns |
| --- | --- |
| `await __sec.headers(url?)` | Security-relevant response headers present and missing, plus any `<meta>` CSP |
| `__sec.csp(policy?)` | CSP directives and weaknesses (`unsafe-*`, wildcards, `http:`, dev hosts like `localhost`, missing `object-src`/`base-uri`/`frame-ancestors`/`form-action`) |
| `await __sec.scan(opts?)` | Client-side exposure: inline scripts and handlers, scripts/styles without SRI, request origins, mixed content, JS-readable and session-like cookies, token-like web storage, form risks, `target=_blank` without `noopener`, iframes, library versions, endpoints and redacted possible secrets in bundles and page state, source map references |
| `await __sec.sourceMapsExposed(urls)` | HTTP status of referenced source maps (`light-active` only) |
