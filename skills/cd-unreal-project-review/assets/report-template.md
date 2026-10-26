# Unreal project review report template

```markdown
# {Project name} – Unreal Project Review

{date} · Unreal {version} · {C++ / Blueprint-only} · {agent/model} · skill: cd-unreal-project-review v0.1.0

> Static, read-only review of the project folder. The editor wasn't opened, nothing was cooked or played, and Blueprint contents weren't inspected.

## Summary
{One-sentence verdict.} {N} findings: {c} critical, {h} high, {m} medium, {l} low.
Fix these first: {3 numbered items with IDs}

| Area | Health | Notes |
| --- | --- | --- |
| Project setup | Good / Needs work / At risk | |
| Version control | | |
| Content structure and naming | | |
| Assets | | |
| C++ quality | | |
| Packaging and build | | |

## Project facts
| Item | Value |
(engine, modules, enabled plugins, project plugins, default maps, rendering features, assets / maps, % assets with type prefix, C++ files / lines, ticking classes, tests, LFS patterns)

## Findings
| ID | Area | Finding | Severity | Evidence (file:line / ini key = value / count) | Recommendation |

## What's done well
{Bulleted}

## Not covered
{Blueprints, references and memory, redirectors, performance, shaders, package size, plus the editor tool for each}

## Suggested next steps
{Short, ordered; include tooling to add (LFS locking, Data Validation in CI, automation tests, clang-format)}
```

**How to write each finding:**
- **Finding:** what and where, with numbers. Example: "14 UObject pointer members without UPROPERTY across 6 headers".
- **Evidence:** paths with line numbers or ini keys and values. For counts, list the top 5 examples and say the rest are in the scanner JSON.
- **Recommendation:** a concrete change and where to make it. Example: "Mark as `UPROPERTY() TObjectPtr<UStaticMeshComponent> Mesh;` in `MyActor.h`".
- Keep sentences short, use specifics rather than adjectives, use UK English, and no padding.

**Write the report to** the path chosen in SKILL.md section 1. **Save the scanner JSON** next to it, in the evidence folder.
