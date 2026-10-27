---
name: cd-vue-code-review
description: AI code review of a Vue 3 + Vite + TypeScript project against the project's own AGENTS.md rules plus general good practice, covering structure, readability, folder tidiness and template drift. Branch mode reviews only what the current branch changed (including uncommitted work) and gives a merge verdict. Full mode reviews the whole project. Findings are split into Fix now, Should fix and Tidy-up, then a prioritised action plan. Read-only; doesn't run the health check. Use when asked to review Vue code, a branch, changes before a PR, or a whole Vue project.
metadata:
  version: "0.1.0"
---

# Vue code review

Review Vue code the way a lead developer would before a merge: does it follow **our rules** (the project's `AGENTS.md`), is it **readable and tidy**, and is it **put together well**? It's an AI review that complements the template's health check. Lint, types, formatting, the build and dependency audits belong to `npm run health-check`; this skill judges what those tools can't.

Files in this skill (paths relative to this folder):

| File | Use it for |
| --- | --- |
| `scripts/vue_scan.py` | Lead finder, standard-library Python. Full: `python scripts/vue_scan.py <repo> --json <file> [--template <clone>]`. Branch: add `--branch [--base auto\|<branch>]`. It finds candidates; you confirm them. |
| `references/checklist.md` | What to review, the rule precedence, and which tier each kind of problem goes in. Read it before the manual review. |
| `assets/report-template.md` | Report structure, how to write findings and the action plan. Read it before writing. |

## Show that this skill is in use (required)

1. **First line of your first reply:** `Skill: cd-vue-code-review v0.1.0`, on its own line, then one sentence saying the mode (branch or full) and, for branch mode, the branch and base.
2. **Report byline:** include `skill: cd-vue-code-review v0.1.0` (the template has a slot for it).
3. **Final message:** end with `Skill: cd-vue-code-review v0.1.0`.

## 1. Choose the mode

| Mode | When | Reviews |
| --- | --- | --- |
| **Branch** | "review my branch / changes / PR", or not stated and you're on a branch other than `main`/`master` that has changes | Only what this branch changed since it split from its base, **plus uncommitted work** (staged, unstaged and new files). Old issues are ignored; wider scans pick them up. |
| **Full** | "review the whole project", "full review", or not stated and you're on `main`/`master` or there are no changes | Everything, including folder structure, unused files and drift from the template. |

**Base branch** (branch mode): on a feature branch, compare against `develop`, else `staging`, else `main`/`master`. On `develop` or `staging`, compare against `main`/`master`. On `main`/`master`, branch mode doesn't apply; run full mode. The user can override ("review against main"). The scanner does this detection with `--base auto`.

## 2. Read the request

| Setting | Default | Change it when the request says… |
| --- | --- | --- |
| Project root | The repo open in your workspace (folder with `package.json` and `src/`) | a path the user names |
| Mode and base | From section 1 | "branch", "full", "against develop/main" |
| Focus | Everything in `references/checklist.md` | specific areas, e.g. "just structure" or "just the stores" |
| Output folder | `reports/cd-vue-code-review/` (see below) | a different path |

**Output folder (every run starts clean).** Unless the user gave another path, all output goes in `reports/cd-vue-code-review/`, relative to the project root:
- `reports/cd-vue-code-review/report.md`: the report, ending with the action plan.
- `reports/cd-vue-code-review/evidence/`: the scanner JSON.

Before you write anything, empty `reports/cd-vue-code-review/` so no files from an earlier run are left behind. Only ever clear this one folder. If the user gave a different path, write there and don't delete anything.

## 3. Rules

1. **Read-only.** Don't edit, format, fix, stage, commit, stash or switch branches. Don't run `npm install`, the health check, lint or the build. The exception is emptying this skill's output folder. Fix things only if the user asks after the review.
2. **Rule precedence.**
   1. The project's `AGENTS.md` (and anything it imports or links, such as `CLAUDE.md` or `RELEASE_PROCESS.md`) is the house rulebook.
   2. General good practice from `references/checklist.md` applies on top.
   3. **Where they disagree, `AGENTS.md` wins and the general rule is dropped, not raised.**
   4. With no `AGENTS.md`, use general good practice only and say so.
3. **Evidence for every finding:** file and line, the rule it breaks (quote the `AGENTS.md` line, or name the good-practice rule), and why it matters in one sentence.
4. **Leads aren't findings.** Read the code around every scanner hit. Drop false positives, and merge repeats: one rule broken in 12 places is **one** finding with a count and the top locations.
5. **Separate "fix now" from "tidy".** Use the tiers in `references/checklist.md`. A Fix now finding must be something that's wrong (a bug, broken architecture rule, lost type safety or silent failure), never a preference.
6. **Comments are fine in moderation.** Flag commented-out code or comments only when it's excessive: large dead blocks, or files where comments drown the code. A few commented-out log lines are at most a Tidy-up.
7. **Template drift is advisory.** Older projects predate the latest template. Differences are Info, unless a quality gate has been weakened or removed (lint, types, hooks, strict mode); that's Should fix.
8. **Stay in your lane.** Accessibility → `cd-web-a11y-audit`. Security (secrets, `v-html` with user data, auth) → `cd-web-security-review`. Note such issues briefly under "Not covered" and point to the skill; don't review them in depth.

## 4. Procedure

1. **Orient.**
   - Read `AGENTS.md` fully, plus the files it links that set rules. List the rules you'll check against.
   - Read `package.json`, `vite.config.*`, `tsconfig.json`, `src/main.ts`, the router and the top-level `src/` layout.
   - If `health-report.md` exists, read it for context (don't re-run it) and don't repeat what it already reports.
2. **Mode setup.**
   - **Branch:** run `python scripts/vue_scan.py <repo> --branch --json reports/cd-vue-code-review/evidence/scan.json`. Note the branch, base, commit count, uncommitted file count and the changed files from its output. If it says you're on `main`/`master`, switch to full mode and say so.
   - **Full:** clone the latest template for the drift check: `git clone --depth 1 https://github.com/TomGreener91/Vue_Template_Project.git <temp-folder>`, outside the project. Then run `python scripts/vue_scan.py <repo> --template <temp-folder> --json reports/cd-vue-code-review/evidence/scan.json`. Delete the temp clone afterwards. Without network, skip drift and say so.
3. **Review.**
   - **Branch:** read every changed file in full, plus the files they import from and the files that use them. Judge the change: does it fit the existing architecture, put things in the right place, and leave the code at least as readable as before? Only report problems on lines the branch added or changed, or design problems the change itself introduces.
   - **Full:** work through `references/checklist.md` area by area. Read the largest and most-used files in full (stores, services, router, layout, the biggest components), and sample the rest. Say how you sampled.
4. **Triage.** Confirm each lead, merge repeats, and assign a tier and severity. Give each finding an ID (`VUE-01`…).
5. **Verdict** (branch mode):
   - **Fix first:** any Fix now finding.
   - **Needs discussion:** no Fix now, but the change raises a design question the team should agree on (e.g. a new pattern or folder).
   - **Ready to merge:** neither. Should fix and Tidy-up findings can follow in a later PR.
6. **Report.** Read `assets/report-template.md`. Build the action plan last, from the triaged findings: group shared fixes, prioritise, size the effort, and check every finding is covered. Write `report.md`.
7. **Tell the user**, in two or three sentences: the verdict (branch) or overall health (full), the counts per tier, and the top three actions. Then give the report location. End with `Skill: cd-vue-code-review v0.1.0`.
