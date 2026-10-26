# Unity project review report template

```markdown
# {Project name} – Unity Project Review

{date} · Unity {version} · {render pipeline} · {agent/model} · skill: cd-unity-project-review v0.2.0

> Static, read-only review of the project folder. The game wasn't opened, built or played.

## Summary
{One-sentence verdict.} {N} findings: {c} critical, {h} high, {m} medium, {l} low.
Start with: {the top 3 actions from the action plan, one line each}

| Area | Health | Notes |
| --- | --- | --- |
| Project setup | Good / Needs work / At risk | |
| Version control | | |
| Structure and naming | | |
| Assets | | |
| Code quality | | |
| Build and tooling | | |

## Project facts
| Item | Value |
(Unity version, render pipeline, input, scripting backend, colour space, serialization, packages, scripts / lines, asmdefs, tests, scenes in build / in project, Resources size, LFS patterns)

## Findings
| ID | Area | Finding | Severity | Evidence (file:line / setting = value / count) | Fix (one line) |

## What's done well
{Bulleted}

## Not covered
{Runtime profiling, scene wiring, shader cost, build size, device testing, plus the editor tool for each}

## Action plan
| # | Priority | Action | Resolves | Owner | Effort | Agent-ready | Verify by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | P1 | {what to change and where} | UNI-03, UNI-07 | {owner} | S | Yes | {concrete check} |

**Effort:** S ≤ 2h · M ≤ 1 day · L ≤ 3 days · XL needs scoping. **Agent-ready:** Yes / Partial / No.
**Totals:** {n} actions resolve {N} findings · P1: {a} · P2: {b} · P3: {c} · P4: {d} · Agent-ready: {y} yes, {p} partial, {x} no
```

**How to write each finding:**
- **Finding:** what and where, with numbers. Example: "312 textures have Read/Write enabled (≈2× texture memory)".
- **Evidence:** paths with line numbers or setting values. For counts, list the top 5 examples and say the rest are in the scanner JSON.
- **Fix (one line):** the change in a few words. The detail goes in the action plan.
- Keep sentences short, use specifics rather than adjectives, use UK English, and no padding.

**How to write the action plan** (the last section; build it from the triaged findings):
- **Group** findings that share a fix (same CSS rule, config file, component or import preset) into one action, and list every ID in **Resolves**. One finding can appear in more than one action if it needs several changes.
- **Every finding is covered.** Before finishing, check that each finding ID appears in at least one action. Info-only findings may be left out; say so under the table.
- **Priority:**
  - **P1:** any Critical, or a High with effort S
  - **P2:** the other Highs
  - **P3:** Medium
  - **P4:** Low, Info and tooling/process improvements

  An action takes the highest priority any of its findings would get. Within a priority, order by reach (how many pages, users or assets), then cheapest first.
- **Action:** imperative and specific: what to change, where (file, rule, setting or layer) and to what. Example: "Create a texture import Preset with Read/Write off and add a Preset Manager rule for `Assets/_Project/Art/**`; reimport the 312 textures listed in `evidence/scan.json`".
- **Owner:** Dev, Tech Art, Art, Audio, Design or Build/DevOps.
- **Effort:** developer time for someone who knows the codebase, including testing. Not AI time. If unsure, round up and say why in the action.
- **Agent-ready:**
  - **Yes:** an agent with repo access can make and test the change.
  - **Partial:** an agent can draft it, but a person must decide, approve or do part of it. Give the reason in brackets.
  - **No:** it needs a person, the editor/tool UI or a third party. Give the reason in brackets.
- **Verify by:** a concrete check a person or a re-run can do, with the page, viewport, command or setting.
- **Tooling and process** (asmdefs, analyzers, LFS, tests in CI, Data Validation, clang-format): add these as P4 actions unless a finding makes them more urgent.
- Fixes that need the editor (reimports, Blueprint changes, redirector fix-up) are Agent-ready: **No** or **Partial**.

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

**Write the report to** `reports/cd-unity-project-review/report.md` (or the path the user gave) and the scanner JSON to `evidence/` beside it.
