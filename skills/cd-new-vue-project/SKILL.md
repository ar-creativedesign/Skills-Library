---
name: cd-new-vue-project
description: Start a new company Vue project from the Vue template to company standards (local git, pushed to Azure DevOps by the team). Extends gg-new-vue-project, which does the scaffolding; off-standard requests are flagged and confirmed, not refused. Use for company and client projects when asked to start, create or scaffold a new Vue project, web app, component library, Electron app or browser extension. If the user hasn't said whether a new project is for the company or personal, ask first. Needs gg-new-vue-project installed alongside it.
metadata:
  version: "1.0.0"
  extends: "gg-new-vue-project"
---

# New company Vue project

This skill **extends `gg-new-vue-project`**, which does all the work: template, setup, personalising, verifying and the hand-off. This file only lists where company standards differ, by the setting, rule and step names that skill keeps stable.

## 1. Load the base skill

1. Find `gg-new-vue-project/SKILL.md` in the same skills folder as this skill (a sibling folder). If it isn't installed, stop and tell the user to install `gg-new-vue-project` alongside this skill (e.g. with Skill Manager), then try again.
2. **Company or personal?** Unless the request makes it clear (the user says so, or names the company, a client, Azure DevOps or a personal GitHub owner), ask "Is this a company project or a personal one?" in the same question as any missing name or location. If it's personal, follow `gg-new-vue-project` on its own instead of this skill.
3. Read it in full, plus the template reference file it points to, then follow it with the differences in section 4. Where the two conflict, this file wins.

## 2. Show that this skill is in use (replaces the base skill's stamps)

1. **First line of your first reply:** `Skill: cd-new-vue-project v1.0.0 (extends gg-new-vue-project v<base version>)`, on its own line, then one sentence on what you're about to create.
2. **Project output:** the initial commit message and the README's "Created with" line say `cd-new-vue-project v1.0.0` where the base skill puts its own name and version.
3. **Final message:** end with `Skill: cd-new-vue-project v1.0.0`.

## 3. Standards are defaults, not blocks

When a request goes against a company standard in section 4, don't refuse and don't silently follow it:

1. Say in one sentence which standard it departs from and why the standard exists.
2. Ask the user to confirm. Combine it with any question the base skill asks anyway (e.g. confirming a GitHub owner and name), so they're asked once.
3. If they confirm, carry on with their choice and list it in the hand-off under **Off standard**. If they don't, use the standard.

## 4. Company standards

| In the base skill | Company standard |
| --- | --- |
| Setting **Remote** | `azure-devops`. A request for anything else (e.g. GitHub) is off standard (section 3): company projects live in Azure DevOps so the team, pipelines and access control stay in one place. If it sounds like a personal project, suggest `gg-new-vue-project` instead. |
| Rule **Git:** | With `azure-devops`: never add a remote, create a hosted repo or push; the team pushes to Azure DevOps themselves. With a confirmed off-standard remote, the base skill's rule for that remote applies. |
| Rule **No secrets.** | Hosting secrets go in the Azure DevOps pipeline's secret variables (or, with a confirmed off-standard remote, that CI's secret store), never in files. |
| Step **Hand-off.** | With `azure-devops`, use the base skill's `azure-devops` items: the GitHub Actions pipeline won't run in Azure DevOps (offer to remove it or convert it to an `azure-pipelines.yml`), and the push commands. Always end with an **Off standard** line: each confirmed departure, or "none". |

Add new company standards here as rows, naming the base skill's setting, rule or step they change. If a standard needs a name the base skill doesn't have, ask for it to be added to the base skill's **Extending this skill** list rather than referring to step numbers.
