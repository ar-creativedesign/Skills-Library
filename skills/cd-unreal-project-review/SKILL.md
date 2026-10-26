---
name: cd-unreal-project-review
description: Review an Unreal Engine project's source folder for project setup, config, version control hygiene (LFS, locking), Content folder structure and asset naming, C++ code quality and packaging settings, then write a prioritised report with file references and fixes. Static and read-only; it doesn't open the editor, cook, build or play the game, and can't read Blueprint contents. Use when asked to review, audit or health-check an Unreal / UE5 project, codebase or repo.
metadata:
  version: "0.2.0"
---

# Unreal project review (static, read-only)

Review the Unreal project the user points you to and write a report a team can act on. This is a **static review of the project folder**: `.uproject`, config, version control, Content structure and naming, and C++. It doesn't open the editor, cook, build, profile or play the game, and **Blueprint and `.uasset` contents are binary and not inspected**. Say so in the report.

This skill is deliberately basic for now. The checklist in `references/checklist.md` is where the team's standards grow.

Files in this skill (paths relative to this folder):

| File | Use it for |
| --- | --- |
| `scripts/project_scan.py` | Scanner: `python scripts/project_scan.py <project-root> --json <file>`. Standard-library Python only. Prints project facts and leads by area, with file and line. |
| `references/checklist.md` | What good looks like per area, how to check it, naming prefixes, and the editor tools for what a static review can't see. Read it before the manual review. |
| `assets/report-template.md` | Report structure and how to write each finding. Read it before writing. |

## Show that this skill is in use (required)

1. **First line of your first reply:** `Skill: cd-unreal-project-review v0.2.0`, on its own line, then one sentence on what you're about to do.
2. **Report byline:** include `skill: cd-unreal-project-review v0.2.0` (the template has a slot for it).
3. **Final message:** end with `Skill: cd-unreal-project-review v0.2.0`.

## 1. Read the request

| Setting | Default | Change it when the request says… |
| --- | --- | --- |
| Project root | The folder in your workspace containing the `.uproject`. If there are several, ask which. | a path or repo the user names |
| Focus | All areas in `references/checklist.md` | specific areas, e.g. "just C++" or "content structure" |
| Target platforms | Read from config where possible, otherwise "unknown" | the platforms the user names |
| House rules | None | team conventions (naming prefixes, folder layout, coding standard). Apply them on top of the checklist. |
| Output folder | `reports/cd-unreal-project-review/` (see below) | a different path |

**Output folder (every run starts clean).** Unless the user gave another path, all output goes in `reports/cd-unreal-project-review/`, relative to the folder you're working in:
- `reports/cd-unreal-project-review/report.md`: the report, ending with the action plan.
- `reports/cd-unreal-project-review/evidence/`: the scanner JSON and any command output.

Before you write anything, empty `reports/cd-unreal-project-review/` so no files from an earlier run are left behind. Old reports aren't kept. Only ever clear this one folder: never the rest of `reports/`, other skills' folders or anything else in the project. If the user gave a different path, write there and don't delete anything. If you can't delete files, overwrite `report.md`, say which old files remain, and carry on.

## 2. Rules

1. **Read-only.**
   - Don't modify, move, rename, resave or delete anything. The one exception is emptying this skill's own output folder (section 1).
   - Don't open the editor, run commandlets, build or cook, unless the user explicitly asks.
   - Don't commit or push.
2. **Evidence for every finding:** file path, plus line or ini key, plus the value. Counts must come from the scanner or a command you ran.
3. **Leads aren't findings.** Confirm each scanner hit by reading the file. Drop anything deliberate and explained.
4. **Stay in your lane.** Blueprint logic, material and shader cost, asset references, map content and performance need the editor. List them under "Not covered" with the editor tool that checks each, rather than guessing.
5. **Big repos:** skip `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`, engine source and plugin binaries. Sample code if it's very large, and say how you sampled.

## 3. Procedure

1. **Orient.**
   - Engine version (or source build), modules, enabled plugins and project plugins.
   - Default maps, rendering features (Lumen, Nanite, virtual shadow maps) and packaging settings.
   - The Content top-level layout.
   - C++ or Blueprint-only.
   - Git with LFS, or another VCS (Perforce/Plastic: adapt the version-control checks).
2. **Run the scanner.** Save its JSON as `reports/cd-unreal-project-review/evidence/scan.json`.
3. **Manual review.** Work through `references/checklist.md` area by area. For C++, read the core gameplay classes (GameMode, Character/Pawn, PlayerController, components, subsystems) and judge the architecture, not just the patterns.
4. **Triage.** Merge duplicates. Give each finding an ID (`UE-01`…), an area, a severity and a recommendation:

   | Severity | Use when |
   | --- | --- |
   | Critical | Breaks builds or teammates' projects, or loses work. Examples: generated folders in git, no `.uproject` / broken module setup. |
   | High | Likely to cause crashes, merge pain or major cost. Examples: UObject pointers without `UPROPERTY`, `.uasset` not in LFS, a missing default map, files over 100 MB outside LFS. |
   | Medium | Maintainability or performance debt worth scheduling. Examples: expensive work in Tick, many ticking classes, cook-everything, very large files, spaces in asset names. |
   | Low | Hygiene and conventions. Examples: naming prefixes, StarterContent left in, hard-coded asset paths, heavy includes. |
   | Info | Facts and observations, including things done well. |

5. **Verify.** Re-open the evidence for every Critical/High finding before writing.
6. **Report.** Use `assets/report-template.md`. Build the action plan last, from the triaged findings: group shared fixes, prioritise, size the effort, and check every finding is covered. Write it as the final section of `report.md`. Then tell the user, in two or three sentences, the overall health, the counts by severity and the top three actions. Give the report location.
