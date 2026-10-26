---
name: cd-web-security-review
description: Run a non-destructive security review against the OWASP Top 10:2025. Live mode checks a running site with a real browser and safe terminal commands (HTTPS/TLS, headers, CSP, cookies, client-side secrets, third-party scripts, exposed files, consent, DNS/email). Code mode reviews the codebase (secrets and git history, injection sinks, access control, auth, config, dependencies, CI, hosting rules). With both, it ties each live issue to its source. Writes a prioritised report. Use when asked for a security, vulnerability, hardening or OWASP check of a site or codebase the user owns or is authorised to test. Not a penetration test.
metadata:
  version: "1.3.0"
---

# Web security review (OWASP Top 10:2025, live site and codebase, non-destructive)

Review the site and/or codebase the user names, then write a prioritised report a development team can act on.

- **Live mode:** a real browser plus safe terminal commands (`curl`, `openssl`, `dig`). Covers configuration, transport, headers, client-side exposure, third-party risk and visible behaviour.
- **Code mode:** read-only review of the source and its git history. Covers secrets, injection sinks, access control, authentication, configuration, dependencies, CI and hosting rules.
- **Both:** ties each live issue to its source and covers server-side risks a live review can't see.

It is **not** a penetration test and never tries to exploit anything.

Files in this skill (paths relative to this folder):

| File | Use it for |
| --- | --- |
| `scripts/sec-kit.js` | The in-page check script (live mode). Read the file and run its **entire contents** as one JavaScript evaluation in each page. |
| `scripts/code_scan.py` | Static scanner (code mode): `python scripts/code_scan.py <repo> --json <file>`. Produces leads with OWASP category, file and line; secrets redacted. |
| `references/code-review.md` | Code mode: rules, scanner, dependency audit commands, optional Semgrep/Gitleaks, manual checklist, how to tie live findings to source. |
| `references/commands.md` | Terminal commands, the fixed exposure-path list, and the light-active checks. |
| `references/owasp-2025.md` | OWASP 2025 mapping, general protection checks, severity rubric and the Kit reference. |
| `references/browser-tools.md` | How to map each action onto Claude or Antigravity tools. Read it first. |
| `references/sources.md` | Official sources: standards status (OWASP Top 10:2025, ASVS 5.0), the ASVS chapter mapping, cheat sheets, MDN header pages, advisory databases. Use it for the Phase 0 standards check and for the Reference link on every finding. |
| `assets/report-template.md` | Report structure and how to write each finding. Read it before writing. |

## Show that this skill is in use (required)

So the team can see which skill produced a result:

1. **First line of your first reply:** `Skill: cd-web-security-review v1.3.0`, on its own line, then one sentence on what you're about to do.
2. **Report byline:** include `skill: cd-web-security-review v1.3.0` (the template already has a slot for it).
3. **Final message:** end with `Skill: cd-web-security-review v1.3.0`.

If you are only partly following this skill (for example the user asked for just one check), still add the stamp and say which parts you ran.

## 1. Choose the mode

| You have… | Mode |
| --- | --- |
| A URL and no access to the code | **Live** |
| Access to the code (a repo is open in your workspace, or the user gives a path or repo) and no URL | **Code** |
| Both | **Both** (the default whenever both are available). Do live first, then code, then tie them together. |

Say which mode you're using in your first reply. List what the chosen mode can't establish under "Not covered".

## 2. Read the request

Take what you need from the user's message and use these defaults for the rest. Write the values you used under "Scope and method" in the report.

| Setting | Default | Change it when the request says… |
| --- | --- | --- |
| Target URL | none (needed for live mode) | the URL given |
| Codebase | the repo open in your workspace, if any | a path or repo the user names; "don't look at the code" |
| Authorisation | **required for live mode.** Code mode on a repo the user opened or pointed you to needs no extra confirmation. | "my site", "we own it", "client X approved testing", etc. If it isn't stated, ask once: *"Do you own this site or have written permission to test it?"* Don't send any requests until you have a yes. If nobody can answer (unattended run), stop. |
| Scope (hosts you may contact) | The target host and its `www.` twin | other hosts named, e.g. "also api.example.com" |
| Exclude | nothing | paths to avoid |
| Test level | `passive` | "light-active", "active checks", "check for exposed files" (see `references/commands.md`) |
| Login | none | the user will sign in with a test account. Ask them to do it in the browser; never take passwords in chat. |
| Forms that may be submitted | none | named forms (e.g. "you can test the login form once with a fake user") |
| Max request rate | 1 per second | a different limit |
| Output folder | `reports/cd-web-security-review/` (see below) | a different path |

**Output folder (every run starts clean).** Unless the user gave another path, all output goes in `reports/cd-web-security-review/`, relative to the folder you're working in:
- `reports/cd-web-security-review/report.md`: the report, ending with the action plan.
- `reports/cd-web-security-review/actions.json`: the action plan as data, for turning into tickets.
- `reports/cd-web-security-review/evidence/`: screenshots, command output (secrets redacted) and scanner JSON.

Before you write anything, empty `reports/cd-web-security-review/` so no files from an earlier run are left behind. Old reports aren't kept. Only ever clear this one folder: never the rest of `reports/`, other skills' folders or anything else in the project. If the user gave a different path, write there and don't delete anything. If you can't delete files, overwrite `report.md`, say which old files remain, and carry on.

## 3. Rules (non-negotiable)

1. **Authorisation first** (above). Only contact hosts in scope. Never contact other subdomains, IP ranges or third parties you discover.
2. **No exploitation.** Never:
   - send attack payloads (script tags, SQL syntax, template expressions, path traversal, command injection)
   - fuzz, brute-force or guess credentials or IDs
   - bypass authentication, a WAF or a CAPTCHA
   - load-test, or run active scanners (sqlmap, nikto, ZAP/Burp active scan)
   - touch other users' data

   If you suspect a vulnerability, report it as **Suspected: needs authorised pen test**, with the evidence.
3. **Each mode uses its own evidence.**
   - Live findings come from what the running site returns: headers, cookies, DOM, network traffic, served JavaScript.
   - Code findings come from the actual source, with file and line. They describe what the code does, not proof of what's deployed. Say so where it matters.
   - If you can't reach the site or read the code you were asked to review, **stop and tell the user**. Never report from memory.
4. **Evidence and confidence for every finding.** Evidence means the command plus the relevant response lines, a screenshot, or Kit output. Confidence is **Confirmed**, **Likely** or **Suspected**.
5. **Protect what you find.**
   - Never write full secrets, tokens, keys, session IDs or personal data anywhere. Show at most the first 6 characters plus the length.
   - If live credentials or personal data are exposed, stop accessing that resource, don't use them, and **alert the user immediately** before continuing.
6. **Do no harm.**
   - In code mode, stay read-only: no edits, installs into the project, commits or pushes. Never test whether a found credential works.
   - Use GET/HEAD/OPTIONS only, except for forms the user named.
   - No accounts, purchases or messages.
   - Respect the rate limit.
   - Cookie banners: "Reject all / necessary only", or hide the banner with CSS. Never accept on the user's behalf.
7. **Bot protection.** On a 403, CAPTCHA or challenge, **do not evade** it: no user-agent spoofing, proxies or stealth plugins. Use a browser the user controls, or stop and report it. A WAF block counts as a positive finding.
8. **Be honest about coverage.** List what this review cannot establish.

## 4. Procedure

**Phase 0: Standards check** (every mode, about a minute).
1. Read `references/sources.md` → "Standards status".
2. If you can search the web, confirm the OWASP Top 10 is still the 2025 edition and ASVS is still 5.0.
3. Record the result and the date in the report's Scope section.
4. If a newer edition has been released, tell the user straight away. Keep mapping to the edition this skill uses unless they ask to switch.
5. With no web access, say "standards not re-checked; using the versions in sources.md (last reviewed <date>)".

Phases 1–5 are live mode. In code-only mode, skip to Phase 5b. In both mode, run them all.

**Phase 1: Discover (passive).**
1. Load the URL. Record:
   - the final URL after redirects, protocol and framework
   - whether it's an SPA
   - every host it talks to (Kit `requestOrigins` plus network requests)
2. List the pages to review: home, login/registration, forms, search, account area (if logged in), API endpoints seen in network traffic, error pages, `robots.txt`, `sitemap.xml`, `/.well-known/security.txt`.
3. Inventory third parties: analytics, tag managers, CDNs, CMS/API hosts, embeds, fonts. Note which load **before** cookie consent.

**Phase 2: Transport, TLS and DNS.** Run the passive commands in `references/commands.md`: HTTP→HTTPS redirect, headers, certificate, TLS versions, SPF, DMARC, CAA, DNSSEC. If you have no terminal, use `__sec.headers()` and list what you skipped, or give the user the commands to run and paste back.

**Phase 3: In-browser review (each page type).** Inject `scripts/sec-kit.js`, then:
1. `await __sec.headers()`. Compare it with curl and across page types.
2. `__sec.csp("<CSP header value>")`. With no argument it reads a `<meta>` CSP.
3. `await __sec.scan()`. Keep the JSON. Read `references/owasp-2025.md` → Kit reference for what it covers.
4. `light-active` only: `await __sec.sourceMapsExposed(<sourceMapReferences samples>)`.
5. Cookie flags from DevTools/the browser's cookie view or curl `Set-Cookie`: `Secure`, `HttpOnly`, `SameSite`, `Domain`, `Path`, expiry. Repeat after login.
6. Look up every detected library version for known CVEs (web search or vendor advisories) and cite the advisory URL.
7. Watch the network while using search, filters, forms and navigation. Note:
   - tokens in URLs
   - verbose error bodies
   - CMS/GraphQL calls and the kind of token they use. A read token for published content is normal; write or management tokens are not.
   - third-party requests that fire before consent

**Phase 4: Behaviour checks.** Run the checks in `references/commands.md` that match the test level:
- error handling (A10)
- reflection indicator (A05)
- open redirect (A01)
- authentication and session checks (A07, only with a test login)
- logged-out access to authenticated URLs (A01)
- clickjacking (A02)

**Phase 5: General protection checks.** Work through the list in `references/owasp-2025.md`:
- `security.txt`
- consent and tracking
- SPF and DMARC, CAA, DNSSEC
- certificate and HSTS
- information disclosure
- caching of personal pages
- SRI
- iframes

**Phase 5b: Code review** (code or both mode). Follow `references/code-review.md`:
1. Get oriented.
2. Run `scripts/code_scan.py`.
3. Run the dependency audit.
4. Run optional Semgrep/Gitleaks if the user agrees.
5. Work through the manual checklist.
6. Tie live findings to their source.

If the scanner reports a live-looking secret, **alert the user immediately** before continuing.

**Phase 6: Triage.** Merge duplicates: a header missing on every page is **one** finding. Give each finding:
- an ID (`SEC-01`…)
- a severity, using the rubric in `references/owasp-2025.md`
- an OWASP 2025 category
- a confidence
- **Found by** (live / code / both) and a **Source** (file:line) where known
- a **Reference**: the ASVS 5.0 chapter, plus the most relevant OWASP cheat sheet or MDN page (see `references/sources.md`), and the advisory link for dependency findings

**Phase 7: Verify.**
1. Re-test every finding once with a fresh request or page load, and drop anything you can't reproduce.
2. For exposed-file findings, compare the body with the site's normal 404/SPA fallback. For code findings, re-read the code path and drop anything a framework default, middleware or sanitiser already handles.
3. Check that no unredacted secret is in your notes or the report.
4. Say this was a re-test, not an independent second review.

**Phase 8: Report.**
1. Read `assets/report-template.md`.
2. Write `report.md` and save evidence in `evidence/`, in the output folder you cleared in section 2.
3. Build the action plan last, from the triaged findings: group shared fixes, prioritise, size the effort, and check every finding is covered. Write it as the final section of `report.md` and as `actions.json`.
4. Tell the user, in two or three sentences: any critical exposure first, then the counts by severity and the top three actions. Then give the report location.

If your environment has a better place for a shareable report (a document or artifact), you may publish there too. Never include unredacted secrets anywhere.
