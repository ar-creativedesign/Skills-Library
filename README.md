# Skills Library

Our team's agent skills, for Claude (Claude Code and the Claude app) and Google Antigravity. Every skill lives in `skills/` and is named `cd-<something>`, so it's obvious which skills are ours. Each skill stamps its name and version into the agent's first reply, its output and its final message (e.g. `Skill: cd-web-a11y-audit v1.0.0`), so you can see when a skill was actually used.

## Skills

| Skill | Version | What it does | Ask it like this |
| --- | --- | --- | --- |
| [`cd-web-a11y-audit`](skills/cd-web-a11y-audit/SKILL.md) | 1.0.0 | WCAG 2.2 AA accessibility audit of a live site, driving a real browser: keyboard, zoom/reflow, text spacing, contrast, screen sizes, ARIA. Writes an evidence-based report. | "Run an accessibility audit on https://example.com" |
| [`cd-web-security-review`](skills/cd-web-security-review/SKILL.md) | 1.0.0 | Non-destructive security review against OWASP Top 10:2025: HTTPS/TLS, headers, CSP, cookies, client-side secrets, third-party scripts, exposed files, consent, DNS/email protection. Not a pen test. | "Security review of https://example.com, it's our site, light-active" |

The web skills need an agent with a browser: Claude in Chrome, the Claude desktop app's built-in browser, Playwright in Claude Code, or Antigravity's browser. The security skill also uses a terminal (`curl`, `openssl`, `dig`). Without a browser, both skills are told to stop rather than guess.

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
templates/cd-skill-template/   starting point for a new skill
prompts/<cd-skill>.md       standalone single-file prompts for agents without skill support (optional)
install.sh · install.ps1 · build-dist.sh
.github/workflows/ci.yml    tests on every push/PR; tagged releases get one zip per skill
```

## Adding or changing a skill

1. **New skill:** copy `templates/cd-skill-template` to `skills/cd-<name>`. Set `name:` to the folder name, write a `description:` that says when to use it, and replace every `cd-your-skill-name v0.1.0` stamp.
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
- No secrets in the repo. Skills that touch external systems must say what they may and may not do.
