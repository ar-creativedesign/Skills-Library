# Skills Library

Our team's agent skills, for Claude (Claude Code and the Claude app) and Google Antigravity. Every skill lives in `skills/` and is named `cd-<something>`, so it's obvious which skills are ours. Each skill stamps its name and version into the agent's first reply, its output and its final message (e.g. `Skill: cd-web-a11y-audit v1.0.0`), so you can see when a skill was actually used.

## Skills

| Skill | Version | What it does | Ask it like this |
| --- | --- | --- | --- |
| [`cd-web-a11y-audit`](skills/cd-web-a11y-audit/SKILL.md) | 1.3.0 | WCAG 2.2 AA accessibility audit. **Live:** drives a real browser (keyboard, zoom/reflow, text spacing, contrast, screen sizes). **Code:** scans components, CSS, router and templates. **Both:** ties each live issue to the file causing it. | "Run an accessibility audit on https://example.com" · "Accessibility review of this repo" · "Audit https://example.com and this codebase" |
| [`cd-web-security-review`](skills/cd-web-security-review/SKILL.md) | 1.3.0 | Non-destructive OWASP Top 10:2025 review. **Live:** HTTPS/TLS, headers, CSP, cookies, client-side secrets, third-party scripts, exposed files, consent, DNS/email. **Code:** secrets and git history, injection sinks, access control, auth, config, dependencies, CI, hosting rules. Not a pen test. | "Security review of https://example.com, it's our site" · "Security review of this repo" |
| [`cd-unity-project-review`](skills/cd-unity-project-review/SKILL.md) | 0.2.0 | Static, read-only review of a Unity project folder: setup, version control (Force Text, meta files, LFS), structure and naming, asset import settings, C# quality, build settings. Doesn't open the editor or play the game. | "Review this Unity project" · "Health-check the Unity repo, focus on code" |
| [`cd-unreal-project-review`](skills/cd-unreal-project-review/SKILL.md) | 0.2.0 | Static, read-only review of an Unreal project folder: .uproject and config, version control (LFS, locking), Content structure and naming prefixes, C++ quality (UPROPERTY, Tick, hard references), packaging settings. Blueprints aren't inspected. | "Review this Unreal project" · "Audit the UE5 repo's content naming and C++" |

Each skill picks **live**, **code** or **both** mode from what it has: a URL, the codebase open in the workspace, or both. Both is the most conclusive. Live mode needs an agent with a browser: Claude in Chrome, the Claude desktop app's built-in browser, Playwright in Claude Code, or Antigravity's browser. The security skill also uses a terminal (`curl`, `openssl`, `dig`). Without a browser, live mode stops rather than guessing; code mode still works.

## Token cost

How much context a typical run uses, so you know what's cheap to run often and what to save for when it matters. Installed skills cost almost nothing until used: the agent only sees each skill's name and description (~100–150 tokens each).

| Rating | Typical run |
| --- | --- |
| 🟢 Light | under ~50k tokens. Fine to run on every branch or PR. |
| 🟡 Medium | ~50–150k tokens. Run per feature, release or review cycle. |
| 🔴 Heavy | over ~150k tokens. Run deliberately, e.g. before launch or for an audit. |

| Skill | Mode | Rating | Typical run | What drives the cost |
| --- | --- | --- | --- | --- |
| `cd-web-new-project` | – | 🟢 Light | 10–25k | Setup, install, lint and build output |
| `cd-vue-code-review` | branch | 🟢 Light | 15–50k | Size of the diff and the files around it |
| `cd-vue-code-review` | full | 🟡 Medium | 60–150k | Project size; large files are sampled |
| `cd-unity-project-review` | – | 🟡 Medium | 30–80k | Scanner summary plus reading the key scripts |
| `cd-unreal-project-review` | – | 🟡 Medium | 30–80k | Scanner summary plus reading the key C++ |
| `cd-web-security-review` | code | 🟡 Medium | 40–120k | Repo size, dependency and secret scan output |
| `cd-web-security-review` | live | 🟡 Medium | 60–150k | Command output, in-page kit, a few screenshots |
| `cd-web-a11y-audit` | code | 🟡 Medium | 40–100k | Repo size, scanner output |
| `cd-web-a11y-audit` | live / both | 🔴 Heavy | 150–400k | Pages × screen sizes: kit injection on each page load, screenshots, page reads |

These are estimates. Skill instructions are only 3–12k tokens; scanner scripts run without being read, so only their summary counts. The real cost is the work: screenshots (~1–1.5k each), page reads and the files the agent opens.

**To keep runs cheap:**
- **Vue code review:** use branch mode day to day, and full mode occasionally.
- **Live audits:** narrow the scope, e.g. "audit the home, search and contact pages" or "desktop and mobile only".
- **Long audits:** run them in a fresh session.

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

4. Add a row to the **Skills** and **Token cost** tables above, open a pull request and merge it.
5. **Release:** to publish zips for the Claude app, tag it: `git tag v2026.10.26 && git push --tags`. CI attaches one zip per skill to the release.

## Rules for every cd- skill

- The folder and `name:` start with `cd-` and match.
- `metadata.version` uses semantic versioning (`1.0.0`).
- The skill tells the agent to stamp `Skill: <name> v<version>` on its first reply, in its output and in its final message.
- Output goes in `reports/<skill-name>/`: `report.md` (ending with a prioritised **Action plan**) and `evidence/`. Each run empties that folder first; no history is kept.
- No secrets in the repo. Skills that touch external systems must say what they may and may not do.
