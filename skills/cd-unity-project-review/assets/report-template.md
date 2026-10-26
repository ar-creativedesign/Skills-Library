# Unity project review report template

```markdown
# {Project name} – Unity Project Review

{date} · Unity {version} · {render pipeline} · {agent/model} · skill: cd-unity-project-review v0.2.0

> Static, read-only review of the project folder. The game wasn't opened, built or played.

## Summary
{One-sentence verdict.} {N} findings: {c} critical, {h} high, {m} medium, {l} low.
Fix these first: {3 numbered items with IDs}

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
| ID | Area | Finding | Severity | Evidence (file:line / setting = value / count) | Recommendation |

## What's done well
{Bulleted}

## Not covered
{Runtime profiling, scene wiring, shader cost, build size, device testing, plus the editor tool for each}

## Suggested next steps
{Short, ordered; include tooling to add (asmdefs, analyzers, tests in CI, LFS)}
```

**How to write each finding:**
- **Finding:** what and where, with numbers. Example: "312 textures have Read/Write enabled (≈2× texture memory)".
- **Evidence:** paths with line numbers or setting values. For counts, list the top 5 examples and say the rest are in the scanner JSON.
- **Recommendation:** a concrete change and where to make it. Example: "Texture import preset with Read/Write off, applied via a Preset Manager rule for `Assets/_Project/Art/**`".
- Keep sentences short, use specifics rather than adjectives, use UK English, and no padding.

**Write the report to** `reports/cd-unity-project-review/report.md` (or the path the user gave) and the scanner JSON to `evidence/` beside it.
