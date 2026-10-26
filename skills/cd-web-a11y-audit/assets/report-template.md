# Accessibility audit report template

```markdown
# {Site name} – Accessibility Audit

{date} · audited against WCAG 2.2 AA · {agent/model} · skill: cd-web-a11y-audit v1.0.0

## Summary
{One-sentence verdict.} {N} issues: {c} critical, {h} high, {m} medium, {l} low.

| Severity | Count |
| --- | --- |

Fix these first: {3–5 numbered items with IDs, one line each}

## Scope and method
Pages tested: {list}. Browser: {name/version}. Date and time.
| Label | Viewport (CSS px) | Represents |   ← the test matrix rows you actually ran
Automated checks and interactive checks performed. Re-test: {what was confirmed or dropped}.

## Site-wide issues
| ID | Issue | Severity | Guidance broken | Pages | Size / zoom | Evidence | Remediation |

## {Page name} ({path})
| ID | Issue | Severity | Guidance broken | Size / zoom | Evidence | Remediation |
(one section per page or template; "No page-specific issues" if none)

## Evidence
{Screenshots embedded or linked, each captioned with ID, page, viewport and what it shows}

## What passed
{Bulleted list of notable passes}

## Not covered
{Screen readers, PDFs, other browsers/devices, pages behind login, contrast over images, etc.}
```

**How to write each finding:**
- **Issue:** what happens, where and with what value, for example "Active pill white on #A8A8A8 = 2.38:1" or "At 640 × 400 sticky header and filters cover 100% of the viewport".
- **Guidance broken:** the WCAG number and name, plus the checklist item in brackets.
- **Size / zoom:** the matrix label(s) where it fails, or "All".
- **Evidence:** a screenshot file and/or the measurement.
- **Remediation:** a concrete fix aimed at the component or CSS rule, for example "Replace `height` with `min-height` on `.hero`; remove `overflow:hidden`". Quote the root-cause rule from `focusRules()` or computed styles where you found it.
- Keep sentences short, use specifics rather than adjectives, use UK English, and never pad.

**Write the report to** the file path chosen in SKILL.md section 1. **Save screenshots** in the evidence folder and link them with relative paths so the report renders in Obsidian, GitHub or VS Code.
