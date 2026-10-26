"""Validate every skill in skills/ and run each skill's browser tests.

    python tests/run_tests.py            # structure checks + tests/<skill>/test_code.py for every skill
    python tests/run_tests.py --browser  # + browser tests in tests/<skill>/test_browser.py
                                         #   (needs: pip install playwright && playwright install chromium)

Structure rules (all skills):
  - folder and `name:` start with "cd-" and match
  - `description:` present, <= 1024 chars
  - `metadata.version` set, and the stamp "<name> v<version>" appears >= 3 times in SKILL.md
  - if assets/report-template.md exists it carries "skill: <name> v<version>"
  - every `scripts/…`, `references/…`, `assets/…` path mentioned in SKILL.md exists
  - every scripts/*.js passes `node --check`
"""
import functools
import http.server
import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
TESTS = ROOT / "tests"
failures = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def structure(skill):
    md = (skill / "SKILL.md").read_text(encoding="utf-8")
    fm = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    check(bool(fm), f"{skill.name}: SKILL.md has frontmatter")
    if not fm:
        return
    front = fm.group(1)
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    ver = re.search(r'^\s+version:\s*"([^"]+)"', front, re.M)
    check(skill.name.startswith("cd-"), f"{skill.name}: folder starts with cd-")
    check(bool(name) and name.group(1).strip() == skill.name, f"{skill.name}: name matches folder")
    check(bool(desc) and 0 < len(desc.group(1)) <= 1024, f"{skill.name}: description present and <= 1024 chars")
    check(bool(ver), f"{skill.name}: metadata.version set")
    if ver:
        stamp = f"{skill.name} v{ver.group(1)}"
        check(md.count(stamp) >= 3, f"{skill.name}: SKILL.md stamps '{stamp}' (first reply, report, final message)")
        rpt = skill / "assets/report-template.md"
        if rpt.exists():
            check(f"skill: {stamp}" in rpt.read_text(encoding="utf-8"), f"{skill.name}: report template carries the stamp")
            rtxt = rpt.read_text(encoding="utf-8")
            check("## Action plan" in rtxt and "actions.json" in rtxt, f"{skill.name}: report template has an action plan and actions.json")
    for ref in sorted(set(re.findall(r"`((?:scripts|references|assets)/[\w./-]+)`", md))):
        check((skill / ref).exists(), f"{skill.name}: referenced file {ref} exists")
    if shutil.which("node"):
        for js in (skill / "scripts").glob("*.js"):
            r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
            check(r.returncode == 0, f"{skill.name}: {js.name} syntax OK {r.stderr.strip()}")


skills = sorted(p for p in SKILLS.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
check(len(skills) > 0, "at least one skill found")
for s in skills:
    structure(s)

for s in skills:
    t = TESTS / s.name / "test_code.py"
    if t.exists():
        spec = importlib.util.spec_from_file_location(f"c_{s.name}", t)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run(s, check)

if "--browser" in sys.argv:
    from playwright.sync_api import sync_playwright

    handler = type("Quiet", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None})
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), functools.partial(handler, directory=str(TESTS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for s in skills:
                t = TESTS / s.name / "test_browser.py"
                if not t.exists():
                    print(f"SKIP {s.name}: no browser tests")
                    continue
                spec = importlib.util.spec_from_file_location(f"t_{s.name}", t)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.run(browser, f"http://127.0.0.1:8765/{s.name}", s, check)
            browser.close()
    finally:
        srv.shutdown()

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
