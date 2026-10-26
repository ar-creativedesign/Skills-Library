# OWASP Top 10:2025 mapping, protection checks and severity

Used by `SKILL.md`.

## What this review can and can't establish

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

## General protection checks

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

## Severity rubric

| Severity | Use when |
| --- | --- |
| Critical | Directly exploitable exposure seen with no further steps. Examples: live secret or private key in served JavaScript, `.git` or `.env` downloadable, database dump public, admin panel open without auth, credentials sent over HTTP. |
| High | Serious weakness likely to be exploitable or to remove a key protection. Examples: no HTTPS redirect or HSTS on a site with logins, session cookie without `HttpOnly`/`Secure`, CORS reflecting any origin with credentials, unencoded reflection of input (suspected XSS), known exploitable CVE in a loaded library, source maps exposing proprietary code with secrets. |
| Medium | Missing defence-in-depth that would limit impact. Examples: CSP with `'unsafe-inline'`/`'unsafe-eval'` or wildcards, no clickjacking protection, third-party scripts without SRI, outdated library with moderate CVEs, verbose errors, tracking before consent, no DMARC enforcement. |
| Low | Hardening and hygiene. Examples: version banners, missing Referrer-/Permissions-Policy, no `security.txt`, `target=_blank` without `noopener` on old-browser audiences, missing CAA. |
| Info | Observations with no direct risk, or positive notes. |

Confidence: **Confirmed** (reproduced, with evidence), **Likely** (strong indicator, not fully reproducible without testing further), **Suspected** (indicator only; needs an authorised pen test).

## Kit reference (`scripts/sec-kit.js`)

`headers()`, `scan()` and `sourceMapsExposed()` are async: `await` them. `scan()` re-fetches the site's own script files (same origin) to look for secrets and endpoints; pass `{fetchScripts:false}` to skip that.

| Call | Returns |
| --- | --- |
| `await __sec.headers(url?)` | Security-relevant response headers present and missing, plus any `<meta>` CSP |
| `__sec.csp(policy?)` | CSP directives and weaknesses (`unsafe-*`, wildcards, `http:`, dev hosts like `localhost`, missing `object-src`/`base-uri`/`frame-ancestors`/`form-action`) |
| `await __sec.scan(opts?)` | Client-side exposure: inline scripts and handlers, scripts/styles without SRI, request origins, mixed content, JS-readable and session-like cookies, token-like web storage, form risks, `target=_blank` without `noopener`, iframes, library versions, endpoints and redacted possible secrets in bundles and page state, source map references |
| `await __sec.sourceMapsExposed(urls)` | HTTP status of referenced source maps (`light-active` only) |
