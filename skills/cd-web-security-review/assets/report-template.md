# Security review report template

```markdown
# {Site name} – Security Review

{date} · OWASP Top 10:2025 · mode: {live|code|both} · test level: {passive|light-active} · {agent/model} · skill: cd-web-security-review v1.1.0

> Authorisation: {as given}. Non-destructive review. Not a penetration test.

## Summary
{One-sentence verdict.} {N} findings: {c} critical, {h} high, {m} medium, {l} low, {i} info.
Fix these first: {3–5 numbered items with IDs}
{If any critical exposure was found: say so first, and that the user was alerted.}

## Scope and method
Hosts in scope, pages reviewed, date and time, tools (browser, curl/openssl/dig), test level, requests sent.

## Findings
| ID | Finding | Severity | Confidence | OWASP 2025 | Affected | Found by | Source (file:line) | Evidence | Remediation |

## Security headers scorecard
| Header | Value seen | Verdict | Recommended value |
(HSTS, CSP, X-Content-Type-Options, X-Frame-Options / frame-ancestors, Referrer-Policy, Permissions-Policy, COOP, CORP, Cache-Control, Server / X-Powered-By)

## Cookies
| Name (no values) | Secure | HttpOnly | SameSite | Domain/Path | Expiry | Purpose | Set before consent? |

## Third-party and supply chain
| Origin | What loads | SRI | Before consent? | Version / known CVEs (with advisory link) |

## TLS, DNS and email
| Check | Result | Verdict |

## Dependencies
| Package | Version | Advisory (link) | Severity | Prod/dev | Fixed in |

## Secrets and repository hygiene
{Redacted secret findings (files and git history), tracked sensitive files, client-exposed env variables, lockfile/Dependabot status}

## What passed
{Positive controls observed}

## Needs an authorised penetration test
{Suspected items, plus the OWASP areas this review cannot cover}

## Not covered
{Limits: no terminal, login not provided, WAF blocked, etc.}
```

**How to write each finding:**
- **Finding:** what and where, with the measured value. Example: "CSP `connect-src` includes `http://localhost:8080` (development leftover)".
- **Evidence:** the command plus 1–3 response lines, a screenshot, or Kit output, with secrets redacted.
- **Found by / Source:** `live`, `code` or `both`, and the file:line (or config) that causes it where known.
- **Remediation:** a concrete config or code change. Example: "Add `Strict-Transport-Security: max-age=31536000; includeSubDomains` at the CDN/nginx". Name the layer to change (CDN, nginx, framework config, CMS).
- Keep sentences short, use specifics rather than adjectives, use UK English, no padding, and never include full secrets.

**Write the report to** the file path chosen in SKILL.md section 2. **Save evidence** (screenshots, command output with secrets redacted) in the evidence folder, linked with relative paths.
