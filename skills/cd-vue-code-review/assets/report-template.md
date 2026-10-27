# Vue code review report template

Use the **branch** or **full** header and summary, then the shared sections.

```markdown
# {Project name} – Vue Code Review ({Branch | Full project})

{date} · mode: {branch|full} · {branch: `<branch>` vs `<base>` @ <merge-base sha>, {n} commits + {u} uncommitted files, {f} files changed | full: {files reviewed / sampled}} · rules: AGENTS.md {found|not found} + good practice · {agent/model} · skill: cd-vue-code-review v0.1.0

## Verdict  (branch mode)
**{Ready to merge | Fix first | Needs discussion}**: {one sentence why}.
{F} fix now · {S} should fix · {T} tidy-up
Start with: {the top actions, one line each}

## Summary  (full mode)
{One-sentence verdict.} {F} fix now · {S} should fix · {T} tidy-up.
Start with: {the top 3 actions, one line each}

| Area | Rating | Notes |
| --- | --- | --- |
| Architecture and layering | Green / Amber / Red | |
| Correctness and Vue practice | | |
| TypeScript | | |
| Readability | | |
| Styling | | |
| Folder structure and tidiness | | |
| Tests and docs | | |
| Template drift | | (advisory) |

## Fix now
| ID | Finding | Rule | Where | Why it matters | Fix (one line) |
| --- | --- | --- | --- | --- | --- |
{"None." if empty}

## Should fix
| ID | Finding | Rule | Where | Why it matters | Fix (one line) |

## Tidy-up
| ID | Finding | Rule | Where | Fix (one line) |

## Template drift  (full mode, advisory)
| File | Status | Note |

## What's done well
{Bulleted, specific}

## Not covered
{Runtime behaviour, tests not run, health check not run, accessibility → cd-web-a11y-audit, security → cd-web-security-review, sampling notes}

## Action plan
| # | Priority | Action | Resolves | Owner | Effort | Agent-ready | Verify by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | P1 | {what to change and where} | VUE-01, VUE-04 | Dev | S | Yes | {concrete check} |

**Effort:** S ≤ 2h · M ≤ 1 day · L ≤ 3 days · XL needs scoping. **Agent-ready:** Yes / Partial / No.
**Totals:** {n} actions resolve {N} findings · P1 (fix now): {a} · P2 (should fix): {b} · P3 (tidy-up): {c}
```

**How to write each finding:**
- **Finding:** what's wrong, specifically. For repeats, give the count. Example: "Network call made directly in a component (3 places)".
- **Rule:** `AGENTS.md: "<quoted rule>"` or `Good practice: <name>` (from the checklist).
- **Where:** `file:line`. For repeats, the top 3 locations, with "+N more" if there are others.
- **Why it matters:** one sentence on the consequence, not the rule restated. Example: "the error is lost and the user sees a blank list".
- **Fix (one line):** the change in a few words. The detail goes in the action plan.
- Keep sentences short, use specifics rather than adjectives, use UK English, and no padding. In branch mode, keep the whole report short enough to read before a merge.

**How to write the action plan** (the last section; build it from the triaged findings):
- **Group** findings that share a fix (same component, store, pattern or config) into one action, and list every ID in **Resolves**.
- **Every finding is covered.** Before finishing, check that each finding ID appears in at least one action. Info items are left out unless the user asks.
- **Priority:**
  - **P1:** Fix now. In branch mode, these must be done before merge.
  - **P2:** Should fix.
  - **P3:** Tidy-up.

  Within a priority, order by reach, then cheapest first.
- **Action:** imperative and specific: what to change, where and to what. Example: "Move the `fetch('/api/users')` in `UserList.vue:42` into `src/services/user.service.ts` as `getUsers()`, and call it from a `useUsers()` composable with an error banner".
- **Owner:** Dev (front end), Dev (back end) or Design.
- **Effort:** developer time for someone who knows the codebase, including testing. Not AI time.
- **Agent-ready:**
  - **Yes:** an agent with repo access can make and test the change.
  - **Partial:** it needs a decision or approval. Give the reason in brackets.
  - **No:** give the reason in brackets.
- **Verify by:** a concrete check, e.g. "`vue_scan.py --branch` shows no fix-now leads; the list shows an error banner when the API is down".

**Write the report to** `reports/cd-vue-code-review/report.md` (or the path the user gave) and the scanner JSON to `evidence/scan.json` beside it.
