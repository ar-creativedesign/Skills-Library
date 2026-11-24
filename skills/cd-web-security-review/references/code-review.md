# Code mode: reviewing the codebase for security

Used by `SKILL.md` when you have the project's source code. Code mode covers what a live review can't see:
- server-side logic
- access control
- dependencies
- secrets in the repo and its history
- configuration
- CI/CD and hosting rules

It also finds the root cause of live findings. It's a **review**, not a penetration test. You read and run read-only tools; you don't attack anything.

## Rules in code mode

- **Read-only.** Don't change files, install packages into the project, commit, or push unless the user asks. Global tools you run (e.g. `npx`, `pipx run`) must not write into the repo.
- **Secrets:** never print, copy or paste full values. The scanner redacts them; keep it that way in the report. If a live credential is found, tell the user at once and recommend rotation. Never test whether it works.
- **Don't run the application against production data,** and don't call external APIs with credentials found in the repo.

## 1. Get oriented

Map the system before scanning:
- entry points (front end, API/server, functions/lambdas)
- frameworks and versions
- where auth happens (middleware, guards, route config)
- how data is stored (ORM, raw SQL, Firestore/Supabase rules, CMS)
- config and environment files (`.env*`, `config/*`, framework config)
- hosting config (`nginx.conf`, `firebase.json`, `vercel.json`, `netlify.toml`, `_headers`, Dockerfile, Terraform)
- CI (`.github/workflows`)

## 2. Run the scanner

```bash
python scripts/code_scan.py <repo-root> --json reports/cd-web-security-review/evidence/security-code-scan.json [--sarif reports/cd-web-security-review/evidence/security-code-scan.sarif]
# On a feature branch or PR, add --branch to scan only added/modified lines:
python scripts/code_scan.py <repo-root> --branch [--base auto|<branch>] --json reports/cd-web-security-review/evidence/security-code-scan.json
```

It's standard-library Python only, and reads git history read-only. It flags **leads** with an OWASP 2025 category, file and line:

| Area | What it flags |
| --- | --- |
| Secrets | Secrets in files and in the last 300 commits of git history (redacted); sensitive files tracked by git (`.env`, keys, service-account JSON); secret-named `VITE_`/`NEXT_PUBLIC_`/`REACT_APP_` variables that ship to the browser |
| Injection | XSS sinks (`v-html`, `innerHTML`, `dangerouslySetInnerHTML`…); `eval`/`new Function`; SQL built from strings; command execution |
| Access control | File paths and redirects built from request input |
| Crypto and auth | TLS verification turned off; weak hashing for secrets; insecure randomness; JWT decoded without verification; unsafe deserialisation |
| Configuration | Wildcard CORS; insecure cookie flags; debug mode or production source maps; weak CSP in code; open Firebase rules |
| Containers and CI | Root Docker images; risky GitHub Actions (`pull_request_target`, script injection, actions pinned to a moving branch) |
| Dependencies | Missing lockfile; missing Dependabot config |

Rules whose hits are only in test or fixture paths are downgraded to Low. **Read each hit in context before keeping it.** A sink fed by a constant, or a `verify=False` in a test helper, isn't a finding.

## 3. Dependency vulnerabilities

Use whatever matches the stack and is available. Don't install anything into the project.

```bash
npm audit --omit=dev --json            # Node (needs package-lock.json; no node_modules needed)
npx --yes osv-scanner -r .             # any ecosystem, if Node is available (uses the OSV database)
pip-audit -r requirements.txt          # Python (pipx run pip-audit … if not installed)
composer audit                         # PHP
dotnet list package --vulnerable       # .NET
```

For each finding, record:
- the package and version
- the advisory ID (GHSA/CVE) and its link
- the severity
- whether the vulnerable code path is plausibly used
- the fixed version

Production dependencies outrank dev-only ones.

Also check whether Dependabot (or Renovate) is configured, whether a lockfile is committed, and whether any third-party script loaded at runtime is pinned (SRI or self-hosted).

## 4. Optional deeper scanners (if present or allowed)

If the user agrees and the tools are installed or runnable without touching the repo:
- **Semgrep:** `semgrep --config p/owasp-top-ten --config p/secrets --json -o <evidence>/semgrep.json .` This downloads rules from the Semgrep registry.
- **Gitleaks:** `gitleaks detect --redact --report-path reports/cd-web-security-review/evidence/gitleaks.json`.
- **GitHub code scanning (CodeQL):** if it's already enabled, read its alerts rather than re-running it.

Tag each finding with the tool that produced it.

## 5. Manual review checklist

| Area | Look for | OWASP 2025 |
| --- | --- | --- |
| Authorisation | Every API route and server action checks authentication **and** ownership/role (not just "logged in"). Look for direct object IDs from the request used without an ownership check. Admin routes are protected server-side, not just hidden in the UI. Firestore/Supabase/storage rules match. | A01 |
| Input handling | Parameterised queries / ORM everywhere; output encoding by default; any raw HTML sink fed only by sanitised or trusted content (CMS rich text through DOMPurify or similar); file uploads checked for type and size and stored outside web root | A05 |
| Authentication | Password hashing (bcrypt/argon2/scrypt); MFA support; rate limiting/lockout on login and reset; session rotation on login; logout invalidates server-side; tokens not in `localStorage` when avoidable; JWT signature and expiry checked | A07 |
| Secrets and config | Secrets only in server-side env or a secret manager; client env contains only public values (e.g. a CMS **read-only, published-content** token, never a management token); `.env` gitignored; production config has debug off and source maps off or private | A02, A04 |
| Security headers and CSP | Set at the server/CDN (`nginx.conf`, `_headers`, `vercel.json`, `firebase.json`, framework middleware such as `helmet`); `frame-ancestors` in a header, not a meta tag; no dev hosts (`localhost`) or `unsafe-eval` in production CSP | A02 |
| Error handling | Global error handler returns generic messages; no stack traces in production responses; failures fail closed (deny), not open | A10 |
| Logging | Security events (login, failed login, permission denied, admin actions) logged without secrets or personal data; alerts exist for spikes | A09 |
| Supply chain and CI | Lockfile committed; Dependabot/Renovate; actions pinned; minimal `permissions:` in workflows; no secrets echoed; `pull_request_target` avoided or hardened; build provenance where it matters | A03, A08 |
| Data protection | Personal data minimised; HTTPS-only cookies; retention/deletion paths exist; analytics only after consent | A04, A06 |

## 6. Tie live and code findings together

For each live finding, find its source:
- a missing header → which server/CDN config should set it
- a CSP with `localhost` → the file that defines the CSP (often `index.html` or a hosting config)
- an exposed endpoint or token in the bundle → the env variable or file that puts it there
- a version banner → the server config

Put the file and line in the finding's **Source** column. A code-only lead that you can't reproduce live stays at confidence **Likely**, or **Suspected** for injection and access control, with **Found by: code**. A finding seen in both is **Found by: both**.
