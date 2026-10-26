# Accessibility audit report template

```markdown
# {Site name} – Accessibility Audit

{date} · audited against WCAG 2.2 AA · mode: {live|code|both} · {agent/model} · skill: cd-web-a11y-audit v1.3.0

## Summary
{One-sentence verdict.} {N} issues: {c} critical, {h} high, {m} medium, {l} low.

| Severity | Count |
| --- | --- |

Start with: {the top 3 actions from the action plan, e.g. **A1** focus styles, one line each}

## Scope and method
Pages tested: {list}. Browser: {name/version}. Date and time.
| Label | Viewport (CSS px) | Represents |   ← the test matrix rows you actually ran
Automated checks and interactive checks performed. Re-test: {what was confirmed or dropped}.
Standards: WCAG 2.2 AA (checked current on {date} / not re-checked). EN 301 549 {version}. {Any newer standard noted.}

## Site-wide issues
| ID | Issue | Severity | Guidance broken | Pages | Size / zoom | Found by | Source (file:line) | Evidence | Fix (one line) | Reference |

## {Page name} ({path})
| ID | Issue | Severity | Guidance broken | Size / zoom | Found by | Source (file:line) | Evidence | Fix (one line) | Reference |
(one section per page or template; "No page-specific issues" if none)

## Evidence
{Screenshots embedded or linked, each captioned with ID, page, viewport and what it shows}

## Code-only findings
{Leads confirmed in code but not reproduced live (or no live audit), same columns; confidence noted}

## What passed
{Bulleted list of notable passes}

## Sources
{Standards used, with the date checked; key Understanding/APG pages cited}

## Not covered
{Screen readers, PDFs, other browsers/devices, pages behind login, contrast over images, etc.}

## Action plan
| # | Priority | Action | Resolves | Owner | Effort | Agent-ready | Verify by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | P1 | {what to change and where} | ACC-03, ACC-07 | {owner} | S | Yes | {concrete check} |

**Effort:** S ≤ 2h · M ≤ 1 day · L ≤ 3 days · XL needs scoping. **Agent-ready:** Yes / Partial / No.
**Totals:** {n} actions resolve {N} findings · P1: {a} · P2: {b} · P3: {c} · P4: {d} · Agent-ready: {y} yes, {p} partial, {x} no
```

**How to write each finding:**
- **Issue:** what happens, where and with what value, for example "Active pill white on #A8A8A8 = 2.38:1" or "At 640 × 400 sticky header and filters cover 100% of the viewport".
- **Guidance broken:** the WCAG number and name, plus the checklist item in brackets.
- **Size / zoom:** the matrix label(s) where it fails, or "All".
- **Evidence:** a screenshot file and/or the measurement.
- **Found by / Source:** `live`, `code` or `both`, and the file:line (or component) that causes it where known.
- **Reference:** a link to the WCAG Understanding page for the criterion (see `references/sources.md`), plus an APG pattern for widget fixes.
- **Fix (one line):** the change in a few words, for example "Use `min-height` on `.hero`". The detail goes in the action plan.
- Keep sentences short, use specifics rather than adjectives, use UK English, and never pad.

**How to write the action plan** (the last section; build it from the triaged findings):
- **Group** findings that share a fix (same CSS rule, config file, component or import preset) into one action, and list every ID in **Resolves**. One finding can appear in more than one action if it needs several changes.
- **Every finding is covered.** Before finishing, check that each finding ID appears in at least one action. Info-only findings may be left out; say so under the table.
- **Priority:**
  - **P1:** any Critical, or a High with effort S
  - **P2:** the other Highs
  - **P3:** Medium
  - **P4:** Low, Info and tooling/process improvements

  An action takes the highest priority any of its findings would get. Within a priority, order by reach (how many pages, users or assets), then cheapest first.
- **Action:** imperative and specific: what to change, where (file, rule, setting or layer) and to what. Example: "Replace `height` with `min-height` on `.hero` in `styles/hero.css:12` and remove `overflow:hidden`". Quote the root-cause rule from `focusRules()` or computed styles where you found it.
- **Owner:** Dev (front end), Dev (back end), Design, Content or Vendor (third-party component).
- **Effort:** developer time for someone who knows the codebase, including testing. Not AI time. If unsure, round up and say why in the action.
- **Agent-ready:**
  - **Yes:** an agent with repo access can make and test the change.
  - **Partial:** an agent can draft it, but a person must decide, approve or do part of it. Give the reason in brackets.
  - **No:** it needs a person, the editor/tool UI or a third party. Give the reason in brackets.
- **Verify by:** a concrete check a person or a re-run can do, with the page, viewport, command or setting.
- **Tooling and process** (missing a11y lint rules, axe in tests, Lighthouse CI): add these as P4 actions with the exact package and config.

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

**Write the report to** `reports/cd-web-a11y-audit/report.md` (or the path the user gave). **Save screenshots** in `evidence/` beside it and link them with relative paths (`evidence/home-200pct.png`) so the report renders in Obsidian, GitHub or VS Code.
