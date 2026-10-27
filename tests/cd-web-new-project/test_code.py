"""Contract test against the live template: every flag the skill documents must still be accepted.

Clones the latest main of the Vue template and dry-runs its setup script (--debug writes nothing)
for each project type with the flags from references/template.md. If the template adds a prompt
or renames a flag, this fails, so the skill gets updated before the team hits it.
Skips (with a note, not a failure) when there's no network or git/node isn't installed.
"""
import pathlib
import shutil
import subprocess
import tempfile

TEMPLATE = "https://github.com/TomGreener91/Vue_Template_Project.git"

CASES = {
    "web app": ["--type=project", "--hosting=none"],
    "web app + firebase": ["--type=project", "--hosting=firebase"],
    "web app + azure": ["--type=project", "--hosting=azure"],
    "component library": ["--type=plugin", "--name=demo-kit", "--plugin-type=component-library", "--docs=n", "--add-to-main=n"],
    "utils library": ["--type=plugin", "--name=demo-utils", "--plugin-type=utils-library", "--docs=n"],
    "vite plugin": ["--type=plugin", "--name=demo-vite", "--plugin-type=vite-plugin", "--docs=n"],
    "electron": ["--type=electron"],
    "extension": ["--type=extension"],
}


def run(skill, check):
    ref = (skill / "references/template.md").read_text(encoding="utf-8")
    for flag in ("--type", "--hosting", "--name", "--plugin-type", "--docs", "--add-to-main", "--cleanup"):
        check(f"`{flag}`" in ref, f"new-project: references/template.md documents {flag}")

    if not (shutil.which("git") and shutil.which("node")):
        print("SKIP new-project template contract: git or node not installed")
        return
    with tempfile.TemporaryDirectory() as d:
        repo = pathlib.Path(d) / "tpl"
        r = subprocess.run(["git", "clone", "-q", "--depth", "1", TEMPLATE, str(repo)], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"SKIP new-project template contract: couldn't clone template ({r.stderr.strip()[:120]})")
            return
        setup = repo / ".templateScripts/setup.cjs"
        check(setup.exists(), "new-project: template still has .templateScripts/setup.cjs")
        if not setup.exists():
            return
        for name, flags in CASES.items():
            p = subprocess.run(["node", str(setup), *flags, "--cleanup=y", "--debug"], cwd=repo,
                               capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
            out = (p.stdout + p.stderr).lower()
            ok = p.returncode == 0 and "non-interactive shell detected" not in out and "pass --" not in out
            check(ok, f"new-project: template setup accepts documented flags for {name}")
            if not ok:
                print((p.stdout + p.stderr)[-600:])
