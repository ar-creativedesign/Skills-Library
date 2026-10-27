# Skills Library

Our team's agent skills, for Claude (Claude Code and the Claude app) and Google Antigravity. Every skill lives in `skills/` and is named `cd-<something>`, so it's obvious which skills are ours. Each skill stamps its name and version into the agent's first reply, its output and its final message (e.g. `Skill: cd-web-a11y-audit v1.0.0`), so you can see when a skill was actually used.

## Skills

| Skill | Version | What it does | Ask it like this |
| --- | --- | --- | --- |
| [`cd-web-a11y-audit`](skills/cd-web-a11y-audit/SKILL.md) | 1.3.0 | WCAG 2.2 AA accessibility audit. **Live:** drives a real browser (keyboard, zoom/reflow, text spacing, contrast, screen sizes). **Code:** scans components, CSS, router and templates. **Both:** ties each live issue to the file causing it. | "Run an accessibility audit on https://example.com" · "Accessibility review of this repo" · "Audit https://example.com and this codebase" |
| [`cd-web-security-review`](skills/cd-web-security-review/SKILL.md) | 1.3.0 | Non-destructive OWASP Top 10:2025 review. **Live:** HTTPS/TLS, headers, CSP, cookies, client-side secrets, third-party scripts, exposed files, consent, DNS/email. **Code:** secrets and git history, injection sinks, access control, auth, config, dependencies, CI, hosting rules. Not a pen test. | "Security review of https://example.com, it's our site" · "Security review of this repo" |
| [`cd-unity-project-review`](skills/cd-unity-project-review/SKILL.md) | 0.2.0 | Static, read-only review of a Unity project folder: setup, version control (Force Text, meta files, LFS), structure and naming, asset import settings, C# quality, build settings. Doesn't open the editor or play the game. | "Review this Unity project" · "Health-check the Unity repo, focus on code" |
| [`cd-unreal-project-review`](skills/cd-unreal-project-review/SKILL.md) | 0.2.0 | Static, read-only review of an Unreal project folder: .uproject and config, version control (LFS, locking), Content structure and naming prefixes, C++ quality (UPROPERTY, Tick, hard references), packaging settings. Blueprints aren't inspected. | "Review this Unreal project" · "Audit the UE5 repo's content naming and C++" |
| [`cd-web-new-project`](skills/cd-web-new-project/SKILL.md) | 0.1.0 | Starts a new project from our [Vue template](https://github.com/TomGreener91/Vue_Template_Project) (latest `main`): web app, plugin/library, Electron app or browser extension. Runs the template's setup non-interactively, personalises names, cleans up, installs, verifies lint + build + health check, and makes a local git repo with **no remote** (push to Azure DevOps yourself). Asks for a name and location if you don't give them. | "New web project called Brief Tracker in ~/Projects" · "Scaffold a component library called cd-ui-kit in D:/Repos" |

Each skill picks **live**, **code** or **both** mode from what it has: a URL, the codebase open in the workspace, or both. Both is the most conclusive. Live mode needs an agent with a browser: Claude in Chrome, the Claude desktop app's built-in browser, Playwright in Claude Code, or Antigravity's browser. The security skill also uses a terminal (`curl`, `openssl`, `dig`). Without a browser, live mode stops rather than guessing; code mode still works.

## Install

| Where | How |
| --- | --- |
| Skill manager | Point it at this repo. Skills are in `skills/`, one folder each. |
| Claude Code, all projects | `./install.sh claude`, which symlinks into `~/.claude/skills` |
| Claude Code, one project | `./install.sh claude-project ~/code/my-app` |
| Claude app (web/desktop) | Download the zips from the latest [release](../../releases), or run `./build-dist.sh`. Upload each one in Settings → Capabilities → Skills. On a Team or Enterprise plan an org admin can add them for everyone. |
| Antigravity workspace | `./install.sh antigravity ~/code/my-app`, which puts them in `.agents/skills/` |
| Antigravity global, or anywhere else | `./install.sh --dest <skills folder>`. Check Antigravity's docs or settings for its current global path. |
| Windows | `.\install.ps1 -Target claude`, `-Target antigravity -Path C:\code\app`, or `-Dest <folder>` |

- **Install a subset:** add `--only cd-web-a11y-audit,cd-web-security-review` (PowerShell: `-Only`).
- **Updating:** `install.sh` symlinks by default, so `git pull` updates every install. Add `--copy` to copy instead. Start a new agent session after installing.

## Repo layout

```text
skills/<cd-skill>/          one folder per skill (Agent Skills format)
  SKILL.md                  frontmatter (name, description, metadata.version) + instructions
  scripts/  references/  assets/
tests/run_tests.py          validates every skill; runs tests/<cd-skill>/test_browser.py with --browser
tests/<cd-skill>/           per-skill fixtures and browser tests (optional)
prompts/<cd-skill>.md       standalone single-file prompts for agents without skill support (live mode only, v1.0)
install.sh · install.ps1 · build-dist.sh
.github/workflows/ci.yml    tests on every push/PR; tagged releases get one zip per skill
```

## Adding or changing a skill

1. **New skill:** create `skills/cd-<name>/` with a `SKILL.md`. Set `name:` to the folder name, write a `description:` that says when to use it, and add the three stamp lines (see the rules below).
2. **Changing a skill:** edit its files. Bump `metadata.version` **and** the version in its three stamp lines (and in `assets/report-template.md` if it has one). The tests fail if they don't match.
3. **Test it:**

   ```bash
   python tests/run_tests.py             # every skill: cd- prefix, frontmatter, stamp, file references, JS syntax
   python tests/run_tests.py --browser   # + per-skill browser tests (pip install playwright && playwright install chromium)
   ```

4. Add a row to the **Skills** table above, open a pull request and merge it.
5. **Release:** to publish zips for the Claude app, tag it: `git tag v2026.10.26 && git push --tags`. CI attaches one zip per skill to the release.

## Rules for every cd- skill

- The folder and `name:` start with `cd-` and match.
- `metadata.version` uses semantic versioning (`1.0.0`).
- The skill tells the agent to stamp `Skill: <name> v<version>` on its first reply, in its output and in its final message.
- Review skills write to `reports/<skill-name>/`: `report.md` (ending with a prioritised **Action plan**) and `evidence/`. Each run empties that folder first; no history is kept.
- No secrets in the repo. Skills that touch external systems must say what they may and may not do.
