"""Contract test against the base skill this one extends.

cd-new-vue-project only lists company differences and refers to gg-new-vue-project by name. This
clones the base skills repo and checks that every setting, rule and step this skill overrides still
exists there. If the base renames one, this fails here before anyone hits it.

Skips (with a note, not a failure) when the repo can't be cloned. Set GG_SKILLS_REPO to a local
path or another URL to test against a different copy.
"""
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

BASE_REPO = os.environ.get("GG_SKILLS_REPO", "https://github.com/TomGreener91/skills.git")
BASE = "gg-new-vue-project"

# What this skill's SKILL.md overrides, as it appears in the base skill's SKILL.md.
OVERRIDES = {
    "Setting Remote": "| Remote |",
    "Remote value azure-devops": "`azure-devops`",
    "Rule Git": "**Git:**",
    "Rule No secrets": "**No secrets.**",
    "Step Hand-off": "**Hand-off.**",
    "Extending this skill section": "## Extending this skill",
}


def run(skill, check):
    md = (skill / "SKILL.md").read_text(encoding="utf-8")
    check(bool(re.search(rf'^\s+extends:\s*"{BASE}"\s*$', md, re.M)), f"overlay: names {BASE} in metadata.extends")

    if not shutil.which("git"):
        print("SKIP overlay contract: git not installed")
        return
    with tempfile.TemporaryDirectory() as d:
        repo = pathlib.Path(d) / "base"
        r = subprocess.run(["git", "clone", "-q", "--depth", "1", BASE_REPO, str(repo)], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"SKIP overlay contract: couldn't clone {BASE_REPO} ({r.stderr.strip()[:120]})")
            return
        base_md_path = repo / "skills" / BASE / "SKILL.md"
        check(base_md_path.exists(), f"overlay: {BASE} exists in the base repo")
        if not base_md_path.exists():
            return
        base_md = base_md_path.read_text(encoding="utf-8")
        for name, anchor in OVERRIDES.items():
            check(anchor in base_md, f"overlay: {BASE} still has {name}")
