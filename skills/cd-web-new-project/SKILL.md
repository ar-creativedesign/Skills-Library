---
name: cd-web-new-project
description: Start a new web project from the team's Vue 3 + Vite + TypeScript template (TomGreener91/Vue_Template_Project, latest main). Scaffolds a web app, Vue/Vite plugin or library, Electron app or browser extension using the template's own setup script, personalises the names, cleans up the template files, installs dependencies, verifies lint, build and health check, and makes a local git repo with no remote. Use when asked to start, create, scaffold or bootstrap a new web project, Vue app, component library, Electron app or browser extension.
metadata:
  version: "0.1.0"
---

# New web project (Vue template)

Create a new project from the team's template, ready for someone to open and start building. The template's own setup script does the scaffolding; this skill decides the options, runs it non-interactively, personalises the result and proves it works.

Files in this skill (paths relative to this folder):

| File | Use it for |
| --- | --- |
| `references/template.md` | The template's project types, setup flags, what each type generates and known quirks. Read it before running setup. |

## Show that this skill is in use (required)

1. **First line of your first reply:** `Skill: cd-web-new-project v0.1.0`, on its own line, then one sentence on what you're about to create.
2. **Project output:** the initial commit message and the README's "Created with" line include `cd-web-new-project v0.1.0`.
3. **Final message:** end with `Skill: cd-web-new-project v0.1.0`.

## 1. Read the request

| Setting | Default | Change it when the request says… |
| --- | --- | --- |
| Project name | **none: required** | the name given. Convert it to kebab-case for `package.json` (e.g. "Brief Tracker" → `brief-tracker`) and keep the original as the display name. |
| Location | **none: required** | the parent folder given. The project is created at `<location>/<project-name>/`. |
| Type | `project` (web app) | "plugin", "component library", "utils library", "Vite plugin", "Electron", "desktop app", "browser extension" (see `references/template.md`) |
| Hosting (web app only) | `none` | "GitHub Pages", "Firebase" or "Azure Static Web Apps" |
| Plugin options (plugin only) | plugin type from the request; docs `n`; add to main `n` | what the request says |
| Description | none | a one-line description for the README and `package.json` |

**If the project name or the location is missing, ask for both in one short question before doing anything else.** Never invent a name or pick a folder. Ask about other settings only if the request is genuinely ambiguous (e.g. "a library" could be a component library or a utils library).

## 2. Rules

1. **Template source:** always the latest `main` of `https://github.com/TomGreener91/Vue_Template_Project` (public). Never fork it or push to it. Record the commit you used.
2. **Never overwrite.** If `<location>/<project-name>/` already exists and isn't empty, stop and ask for another name or location.
3. **Git: local only.** Run `git init` and make the initial commit. Never add a remote, create a hosted repo or push; the team pushes to Azure DevOps themselves. If `git config user.name` or `user.email` isn't set, don't invent one: skip the commit, leave the files staged, and tell the user.
4. **No secrets.** Hosting tokens (Firebase, Azure) are never written into files. List them in the hand-off as secrets the user adds in their pipeline settings.
5. **Keep the template's conventions.** Don't add, remove or upgrade dependencies, or restructure `src/`, unless the user asks. The project's `AGENTS.md` sets the coding rules from here on. If it says to prefix commands (e.g. `rtk run --`) and that tool is installed, do so.
6. **Stop on failure.** If setup, install, lint, build or the health check fails, don't paper over it. Report the command, the error and what you think the cause is.

## 3. Procedure

1. **Check the basics.** `node --version` is 20 or later, `npm` and `git` are available, and the target folder is free (rule 2).
2. **Copy the template.**
   ```bash
   git clone --depth 1 https://github.com/TomGreener91/Vue_Template_Project.git "<location>/<project-name>"
   cd "<location>/<project-name>"
   git rev-parse --short HEAD        # note this as <template-sha>
   rm -rf .git                       # it's a copy, not a fork
   git init -b main                  # husky needs a git repo before install
   ```
3. **Run the template setup non-interactively.** Build the flags from section 1 using `references/template.md`, always with `--cleanup=y` (removes `.templateScripts/`). Example:
   ```bash
   node .templateScripts/setup.cjs --type=project --hosting=none --cleanup=y </dev/null
   ```
   If it stops with `Non-interactive shell detected. Pass --<flag>=…`, the template has gained a new prompt: read `.templateScripts/setup.cjs` (restore it with `git clone` again if cleanup already ran), add the flag and re-run in a fresh folder.
4. **Install:** `npm install`.
5. **Personalise.**
   - `package.json`: `name` → `<project-name>`; add `description` if given.
   - `index.html`: `<title>` → the display name.
   - `README.md`: replace the first heading with the display name, add the description, and add a line: `Created with cd-web-new-project v0.1.0 from Vue_Template_Project@<template-sha> on <YYYY-MM-DD>.`
   - Leave the demo views and store in place as working examples unless the user asked for a blank app.
6. **Verify.** Run, in order, and record each result:
   - `npm run lint` (must pass)
   - `npm run build` (must pass)
   - `npm run health-check` (grade must be **C or better**; the report files are git-ignored)

   For a plugin, also run the build inside the plugin folder if the template created one.
7. **Initial commit** (subject to rule 3): `git add -A && git commit -m "chore: initial scaffold from Vue_Template_Project@<template-sha> (cd-web-new-project v0.1.0)"`. The template's commitlint and lint-staged hooks run here, so the message must stay a conventional commit.
8. **Hand-off.** Tell the user, briefly:
   - where the project is, its type and the template commit used
   - the verify results (lint, build, health grade, and the top warnings from `health-report.md`, e.g. `npm audit` counts)
   - how to run it: `npm run dev`
   - **Azure DevOps:** the template generates a GitHub Actions pipeline (`.github/workflows/ci-cd.yml` and `.github/actions/`). It won't run in Azure DevOps. Say so, and offer to remove it or convert it to an `azure-pipelines.yml`.
   - any secrets the chosen hosting needs (see `references/template.md`)
   - next step: push to Azure DevOps with `git remote add origin <url>` then `git push -u origin main`

   End with `Skill: cd-web-new-project v0.1.0`.
