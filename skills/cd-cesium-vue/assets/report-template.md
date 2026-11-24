# Vue-Cesium Audit Report Template

Use the **branch** or **full** header and summary, then the shared sections.

```markdown
# {Project name} – Vue-Cesium Audit ({Branch | Full project})

{date} · mode: {branch|full} · {branch: `<branch>` vs `<base>` @ <merge-base sha>, {n} commits + {u} uncommitted files, {f} files changed | full: {files reviewed / sampled}} · rules: AGENTS.md {found|not found} + cesium-patterns · {agent/model} · skill: cd-cesium-vue v1.0.0

## Verdict  (branch mode)
**{Ready to merge | Fix first | Needs discussion}**: {one sentence why}.
{N} findings: {c} critical, {h} high, {m} medium, {l} low
Start with: {the top actions, one line each}

## Summary  (full mode)
{One-sentence verdict.} {N} findings: {c} critical, {h} high, {m} medium, {l} low.
Start with: {the top 3 actions, one line each}

| Area | Rating | Notes |
| --- | --- | --- |
| Reactivity & state | Green / Amber / Red | |
| WebGL & listener lifecycle | | |
| Vite build & assets | | |
| Tokens & security | | |
| Performance & rendering | | |

## Findings
Sorted by severity, then confidence.

| ID | Area | Finding | Severity | Confidence | Rule | Where | Why it matters | Fix (one line) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| {"None." if empty}

## What's done well
{Bulleted, specific}

## Not covered
{Runtime WebGL profiling, GPU memory testing, sampling notes}

## Action plan
| # | Priority | Action | Resolves | Owner | Effort | Agent-ready | Verify by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | P1 | {what to change and where} | CES-01 | Dev (front end) | S | Yes | {concrete check} |

**Effort:** S ≤ 2h · M ≤ 1 day · L ≤ 3 days · XL needs scoping. **Agent-ready:** Yes / Partial / No.
**Totals:** {n} actions resolve {N} findings · P1: {a} · P2: {b} · P3: {c} · P4: {d} · Agent-ready: {y} yes, {p} partial, {x} no
```

**Write the report to** `reports/cd-cesium-vue/report.md` (or the path the user gave) and the scanner JSON to `evidence/scan.json` beside it.
