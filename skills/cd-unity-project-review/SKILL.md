---
name: cd-unity-project-review
description: Review a Unity project's source folder for project setup, version control hygiene, folder structure and naming, asset import settings, C# code quality and build settings, then write a prioritised report with file references and fixes. Static and read-only; it doesn't open the editor, build or play the game. Use when asked to review, audit or health-check a Unity project, codebase or repo.
metadata:
  version: "0.2.0"
---

# Unity project review (static, read-only)

Review the Unity project the user points you to and write a report a team can act on. This is a **static review of the project folder**: settings, packages, version control, structure, asset import settings and C# code. It doesn't open the Unity editor, build, profile or play the game. Say so in the report.

This skill is deliberately basic for now. The checklist in `references/checklist.md` is where the team's standards grow.

Files in this skill (paths relative to this folder):

| File | Use it for |
| --- | --- |
| `scripts/project_scan.py` | Scanner: `python scripts/project_scan.py <project-root> --json <file>`. Standard-library Python only. Prints project facts and leads by area, with file and line. |
| `references/checklist.md` | What good looks like per area, how to check it, and what the scanner can't see. Read it before the manual review. |
| `assets/report-template.md` | Report structure and how to write each finding. Read it before writing. |

## Show that this skill is in use (required)

1. **First line of your first reply:** `Skill: cd-unity-project-review v0.2.0`, on its own line, then one sentence on what you're about to do.
2. **Report byline:** include `skill: cd-unity-project-review v0.2.0` (the template has a slot for it).
3. **Final message:** end with `Skill: cd-unity-project-review v0.2.0`.

## 1. Read the request

| Setting | Default | Change it when the request says… |
| --- | --- | --- |
| Project root | The folder in your workspace that contains `Assets/` and `ProjectSettings/`. If there are several, ask which. | a path or repo the user names |
| Focus | All areas in `references/checklist.md` | specific areas, e.g. "just code quality" or "assets and build size" |
| Target platforms | Read from settings where possible, otherwise "unknown" | the platforms the user names (they change what "good" looks like, e.g. mobile texture sizes) |
| House rules | None | team conventions the user gives or points to (naming, architecture). Apply them on top of the checklist. |
| Output folder | `reports/cd-unity-project-review/` (see below) | a different path |

**Output folder (every run starts clean).** Unless the user gave another path, all output goes in `reports/cd-unity-project-review/`, relative to the folder you're working in:
- `reports/cd-unity-project-review/report.md`: the report, ending with the action plan.
- `reports/cd-unity-project-review/evidence/`: the scanner JSON and any command output.

Before you write anything, empty `reports/cd-unity-project-review/` so no files from an earlier run are left behind. Old reports aren't kept. Only ever clear this one folder: never the rest of `reports/`, other skills' folders or anything else in the project. If the user gave a different path, write there and don't delete anything. If you can't delete files, overwrite `report.md`, say which old files remain, and carry on.

## 2. Rules

1. **Read-only.**
   - Don't modify, move, reimport or delete anything. The one exception is emptying this skill's own output folder (section 1).
   - Don't open the project in Unity, run builds or install packages, unless the user explicitly asks.
   - Don't commit or push.
2. **Evidence for every finding:** file path, plus line or setting name, plus the value. Counts must come from the scanner or a command you ran, not estimates.
3. **Leads aren't findings.** Confirm each scanner hit by reading the file. Downgrade or drop anything that's deliberate and explained (e.g. Read/Write enabled on a texture the code reads from).
4. **Stay in your lane.** You can't see scene/prefab wiring in detail, shader cost, frame times or runtime behaviour. List these under "Not covered" with the editor tool that would check them, rather than guessing.
5. **Big repos:** skip `Library/`, `Temp/`, `Logs/`, build output and LFS pointer contents. Sample code if there are thousands of scripts, and say how you sampled.

## 3. Procedure

1. **Orient.**
   - Unity version, render pipeline, input system, scripting backend and platforms.
   - Packages from `Packages/manifest.json`.
   - Top-level folder layout.
   - Assembly definitions.
   - Whether it's a git repo with LFS.
   - Third-party asset folders.
2. **Run the scanner.** Save its JSON as `reports/cd-unity-project-review/evidence/scan.json`.
3. **Manual review.** Work through `references/checklist.md` area by area. For code, read the largest and most-referenced scripts (managers, player and controller classes, anything flagged) and judge the architecture, not just the patterns.
4. **Triage.** Merge duplicates (one setting on 300 textures is **one** finding with a count). Give each finding an ID (`UNI-01`…), an area, a severity and a recommendation:

   | Severity | Use when |
   | --- | --- |
   | Critical | Breaks builds or teammates' projects, or loses work. Examples: Editor API in runtime code, missing `.meta` files committed, `Library/` in git. |
   | High | Likely to cause bugs, merge pain or major performance/memory cost. Examples: Hidden Meta Files, not Force Text, files over 100 MB without LFS, a missing build scene, expensive per-frame code in core systems. |
   | Medium | Maintainability or performance debt worth scheduling. Examples: no asmdefs in a large project, big scripts, Read/Write textures, long audio decompressed on load. |
   | Low | Hygiene and conventions. Examples: naming, empty callbacks, public fields, string-based calls. |
   | Info | Facts and observations, including things done well. |

5. **Verify.** Re-open the evidence for every Critical/High finding before writing.
6. **Report.** Use `assets/report-template.md`. Build the action plan last, from the triaged findings: group shared fixes, prioritise, size the effort, and check every finding is covered. Write it as the final section of `report.md`. Then tell the user, in two or three sentences, the overall health, the counts by severity and the top three actions. Give the report location.
