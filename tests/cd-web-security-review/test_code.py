"""Builds a throwaway repo with deliberate weaknesses (secrets assembled at runtime, never committed
to this library) and checks scripts/code_scan.py flags them with values redacted."""
import importlib.util
import pathlib
import re
import subprocess
import tempfile


def run(skill, check):
    spec = importlib.util.spec_from_file_location("sec_code_scan", skill / "scripts/code_scan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    stripe = "sk_" + "live_" + "51Habcdefghijklmnopqrstuv" + "WXYZ"
    aws = "AKIA" + "ABCDEFGHIJKLMNOP"
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "src").mkdir()
        (root / ".github/workflows").mkdir(parents=True)
        (root / "package.json").write_text('{"dependencies":{"vue":"^3.4.0","express":"^4.19.0"}}')
        (root / ".env").write_text("VITE_CMS_TOKEN=" + "abcdefghijklmnop1234\nDB_PASSWORD=" + "hunter2hunter2\n")
        (root / "src/App.vue").write_text('<template><div v-html="post.body"></div><a href="https://x.org" target="_blank">x</a></template>\n'
                                          '<script>const t = import.meta.env.VITE_CMS_TOKEN; eval(userInput)</script>\n')
        (root / "src/server.js").write_text("const cp = require('child_process')\n"
                                            "app.get('/f', (req, res) => res.sendFile(req.query.path))\n"
                                            "app.get('/r', (req, res) => res.redirect(req.query.next))\n"
                                            "app.use(cors({ origin: '*' }))\n"
                                            "db.query(`SELECT * FROM users WHERE id = ${req.params.id}`)\n"
                                            "https.request({ rejectUnauthorized: false })\n"
                                            "const stripe = '" + stripe + "'\n")
        (root / "firestore.rules").write_text("service cloud.firestore { match /databases/{db}/documents { match /{d=**} { allow read, write: if true; } } }")
        (root / "Dockerfile").write_text("FROM node:20\nCOPY . .\nCMD node server.js\n")
        (root / ".github/workflows/ci.yml").write_text("on: pull_request_target\njobs:\n  a:\n    steps:\n      - uses: someone/action@main\n      - run: echo \"${{ github.event.pull_request.title }}\"\n")
        g = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)
        g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
        (root / "old.js").write_text("const k = '" + aws + "'\n")
        g("add", "-A"); g("commit", "-qm", "one")
        (root / "old.js").unlink()
        g("add", "-A"); g("commit", "-qm", "two")
        res = mod.scan(d, 25)
    rules = {r["rule"]: r for r in res["results"]}
    for rid in ["SECRET", "CLIENT_EXPOSED_SECRET_ENV", "XSS_SINK", "EVAL", "SQL_CONCAT", "COMMAND_EXEC", "PATH_FROM_REQUEST",
                "OPEN_REDIRECT", "CORS_WILDCARD", "TLS_VERIFY_OFF", "FIREBASE_RULES_OPEN", "DOCKER_RUNS_AS_ROOT", "CI_PR_TARGET",
                "CI_SCRIPT_INJECTION", "CI_UNPINNED_ACTION", "SENSITIVE_FILE_TRACKED", "SECRET_IN_GIT_HISTORY", "NO_LOCKFILE"]:
        check(rid in rules, f"sec code: {rid} detected")
    dump = str(res)
    check(stripe not in dump and aws not in dump and "hunter2hunter2" not in dump, "sec code: secret values redacted in output")
    check(rules.get("SECRET", {}).get("severity_hint") == "Critical", "sec code: live-looking secret rated Critical")
