# Skills Library

Our company agent skills, for Claude Code, the Claude app, Codex and Google Antigravity. They hold what's specific to us: company policy, processes and standards. Every skill lives in `skills/` and is named `cd-<something>`, so it's obvious which skills are ours. Each skill stamps its name and version into the agent's first reply, its output and its final message (e.g. `Skill: cd-new-vue-project v1.0.0`), so you can see when a skill was actually used.

## Skills

| Skill | Version | What it does | Ask it like this |
| --- | --- | --- | --- |
| [`cd-new-vue-project`](skills/cd-new-vue-project/SKILL.md) | 1.0.0 | Starts a new company Vue project from our Vue template to company standards: local git (the team pushes to Azure DevOps), hosting secrets in Azure DevOps pipeline variables. Requests that go off standard, like GitHub, are flagged and confirmed rather than refused, and listed in the hand-off. Asks "company or personal?" when the request doesn't say. Extends `gg-new-vue-project`, which does the scaffolding and must be installed alongside it. | "New Vue project called Brief Tracker in ~/Projects" · "Scaffold a component library called cd-ui-kit in D:/Repos" |

### Token cost

Installed skills cost almost nothing until used: the agent only sees each skill's name and description (~100–150 tokens each).

| Skill | Mode | Rating | Typical run | What drives the cost |
| --- | --- | --- | --- | --- |
| `cd-new-vue-project` | – | 🟢 Light | 10–25k | Setup, install, lint and build output (the skill it extends does the work) |

🟢 under ~50k tokens, fine on every branch · 🟡 ~50–150k, per feature or release · 🔴 over ~150k, run deliberately.

## Install

A skill that extends another (`metadata.extends` in its `SKILL.md`) needs that skill installed alongside it, in the same skills folder.

| Where | How |
| --- | --- |
| Skill Manager | Point it at this repo. Skills are in `skills/`, one folder each. |
| Claude Code, all projects | `./install.sh claude`, which symlinks into `~/.claude/skills` |
| Claude Code, one project | `./install.sh claude-project ~/code/my-app` |
| Claude app (web/desktop) | Download the zips from the latest [release](../../releases), or run `./build-dist.sh`. Upload each one in Settings → Capabilities → Skills. On a Team or Enterprise plan an org admin can add them for everyone. |
| Antigravity workspace | `./install.sh antigravity ~/code/my-app`, which puts them in `.agents/skills/` |
| Antigravity global | `./install.sh antigravity-global`, which links into `~/.gemini/config/skills` |
| Anywhere else | `./install.sh --dest <skills folder>` |
| Windows | `.\install.ps1 -Target claude`, `-Target antigravity -Path C:\code\app`, `-Target antigravity-global`, or `-Dest <folder>` (links via junctions by default; add `-Copy` to copy) |

- **Install a subset:** add `--only cd-new-vue-project` (PowerShell: `-Only`).
- **Updating:** `install.sh` (symlinks) and `install.ps1` (junctions) link by default, so `git pull` updates every install. Add `--copy` / `-Copy` to copy instead. Start a new agent session after installing.

## Extending a skill

When a general-purpose skill already does the job, a `cd-` skill extends it instead of copying it, and lists only what company policy changes:

```text
skills/gg-new-vue-project/   the base skill (installed alongside): does the work, keeps stable names
skills/cd-new-vue-project/   this repo: "load gg-new-vue-project, then apply these differences"
```

1. Name the base in the frontmatter: `extends: "gg-new-vue-project"`. The skill stops and says so if the base isn't installed.
2. List the differences in a table, naming the base skill's setting, rule (bold label) or step (bold label). Never refer to step numbers. The names a base keeps stable are listed in its **Extending this skill** section; if you need one that isn't there, ask for it to be added to the base.
3. Where the two conflict, the `cd-` skill wins, and its stamp replaces the base's.
4. **Standards are defaults, not blocks:** when a request goes against one, the skill says which standard it departs from, asks the user to confirm, and lists confirmed departures in its output under **Off standard**.
5. **Which one runs:** when a request could be for either skill, the `cd-` skill asks once (e.g. "company or personal?") unless the request makes it clear. Don't rely on which skills a machine has installed: Skill Manager syncs the same set everywhere.
6. Add `tests/<cd-skill>/test_code.py` that clones the base skill's repo and checks every name you override (see `tests/cd-new-vue-project/test_code.py`). CI then fails here, not in someone's project, if the base changes in a way that breaks us.

## Adding a skill

1. **New skill:** create `skills/cd-<name>/` with a `SKILL.md` (plus optional `scripts/`, `references/`, `assets/`). Set `name:` to the folder name, write a `description:` that says when to use it, and add the three stamp lines. If it extends another skill, follow **Extending a skill**.
2. **Changing a skill:** edit its files. Bump `metadata.version` **and** the version in its three stamp lines (and in `assets/report-template.md` if it has one). The tests fail if they don't match.
3. **Test it:** `python tests/run_tests.py` (structure, stamps, file references, JS syntax and each skill's `tests/<cd-skill>/test_code.py`). Add `--browser` for `test_browser.py` tests (`pip install playwright && playwright install chromium`). Set `GG_SKILLS_REPO=<path or URL>` to run a contract test against a different copy of the base.
4. Add a row to the **Skills** and **Token cost** tables above, open a pull request and merge it.
5. **Release:** to publish zips for the Claude app, tag it: `git tag v2026.11.23 && git push --tags`. CI attaches one zip per skill to the release.

Conventions, checked by `tests/run_tests.py` in CI:
- The folder and `name:` start with `cd-` and match.
- `metadata.version` uses semantic versioning (`1.0.0`).
- The skill tells the agent to stamp `Skill: <name> v<version>` on its first reply, in its output and in its final message.
- Every `scripts/…`, `references/…` and `assets/…` path mentioned in `SKILL.md` exists.
- Review skills write to `reports/<skill-name>/`: `report.md` (ending with a prioritised **Action plan**) and `evidence/`. Each run empties that folder first; no history is kept.
- No secrets in the repo. Skills that touch external systems must say what they may and may not do.
