# Security review report template

```markdown
# {Site name} – Security Review

{date} · OWASP Top 10:2025 · mode: {live|code|both} · test level: {passive|light-active} · {agent/model} · skill: cd-web-security-review v1.3.0

> Authorisation: {as given}. Non-destructive review. Not a penetration test.

## Summary
{One-sentence verdict.} {N} findings: {c} critical, {h} high, {m} medium, {l} low, {i} info.
Start with: {the top 3 actions from the action plan, one line each}
{If any critical exposure was found: say so first, and that the user was alerted.}

## Scope and method
Hosts in scope, pages reviewed, date and time, tools (browser, curl/openssl/dig), test level, requests sent.
Standards: OWASP Top 10:2025 and ASVS 5.0 (checked current on {date} / not re-checked). {Any newer edition noted.}

## Findings
| ID | Finding | Severity | Confidence | OWASP 2025 | ASVS 5.0 | Affected | Found by | Source (file:line) | Evidence | Fix (one line) | Reference |

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

## ASVS coverage summary
| ASVS 5.0 chapter | Reviewed? (live / code / not covered) | Findings |

## Sources
{Standards used, with the date checked; cheat sheets, MDN pages and advisories cited}

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
- **Found by / Source:** `live`, `code` or `both`, and the file:line (or config) that causes it where known.
- **ASVS / Reference:** the ASVS 5.0 chapter (e.g. `V3`), plus a link to the most relevant OWASP cheat sheet or MDN page; for dependencies, the GHSA/CVE advisory.
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
- **Action:** imperative and specific: what to change, where (file, rule, setting or layer) and to what. Example: "Add `Strict-Transport-Security: max-age=31536000; includeSubDomains` at the CDN (Cloudflare → Rules → Transform → Response headers)". Name the layer to change (CDN, nginx, framework config, CMS).
- **Owner:** Dev, DevOps/Hosting, Security or Vendor (third-party service).
- **Effort:** developer time for someone who knows the codebase, including testing. Not AI time. If unsure, round up and say why in the action.
- **Agent-ready:**
  - **Yes:** an agent with repo access can make and test the change.
  - **Partial:** an agent can draft it, but a person must decide, approve or do part of it. Give the reason in brackets.
  - **No:** it needs a person, the editor/tool UI or a third party. Give the reason in brackets.
- **Verify by:** a concrete check a person or a re-run can do, with the page, viewport, command or setting.
- **Exposed secrets:** the first action is always "Rotate the credential", P1, owner Dev or DevOps, Agent-ready: No. Removing it from code and history is a separate action.
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

**Write the report to** `reports/cd-web-security-review/report.md` (or the path the user gave). **Save evidence** (screenshots, command output with secrets redacted) in `evidence/` beside it, linked with relative paths (`evidence/headers.txt`).
