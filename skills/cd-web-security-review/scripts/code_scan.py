#!/usr/bin/env python3
"""Static security scan of a codebase (web front end, Node, Python, PHP, config, CI, containers).

Produces LEADS, not findings: confirm every hit by reading the code in context before reporting.
Secret values are always redacted in the output.

    python code_scan.py <repo-root> [--json out.json] [--max-per-rule 25] [--no-git]

Standard library only. Skips node_modules, build output and vendored folders.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SKIP_DIRS = {".git", "node_modules", "dist", "build", "out", ".next", ".nuxt", ".output", "coverage", "vendor",
             "bower_components", ".venv", "venv", "env", "__pycache__", "Library", "Temp", ".cache", "storybook-static"}
TEXT_EXT = (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte", ".html", ".htm", ".py", ".php", ".rb", ".go",
            ".cs", ".java", ".kt", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".env", ".properties",
            ".xml", ".rules", ".tf", ".sh", ".ps1", ".sql", ".graphql", ".md", ".txt")
SPECIAL_NAMES = ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".htaccess", "nginx.conf", "firestore.rules",
                 "storage.rules", "database.rules.json", "firebase.json", "vercel.json", "netlify.toml", "_headers")
MAX_BYTES = 1_500_000
SKIP_FILES = {"code_scan.py", "sec-kit.js", "a11y-kit.js"}  # our own scanners contain the patterns they look for
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?|mocks?|e2e)(/|$)|\.(test|spec)\.")


def redact(s):
    s = s.strip().strip("\"'")
    return (s[:2] + "…") if len(s) <= 10 else f"{s[:6]}…[{len(s)} chars]"


SECRET_PATTERNS = [
    ("AWS access key", r"AKIA[0-9A-Z]{16}"),
    ("Google API key (often public by design for browser use: check restrictions)", r"AIza[0-9A-Za-z_\-]{35}"),
    ("Stripe secret key", r"sk_(?:live|test)_[0-9a-zA-Z]{20,}"),
    ("Slack token", r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    ("GitHub token", r"gh[pousr]_[0-9A-Za-z]{30,}"),
    ("Private key block", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----"),
    ("JWT", r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("Connection string with password", r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:\s/]+:[^@\s]{4,}@"),
    ("Generic secret assignment", r"(?i)(?:api[_-]?key|secret|client[_-]?secret|access[_-]?token|auth[_-]?token|password|passwd)[\"']?\s*[:=]\s*[\"'][^\"'\s$]{12,}[\"']"),
]

CODE_RULES = [
    # (id, OWASP 2025, severity hint, description, regex, file filter)
    ("XSS_SINK", "A05 Injection", "High", "Raw HTML sink: confirm the data is trusted or sanitised (DOMPurify etc.)",
     r"v-html\s*=|dangerouslySetInnerHTML|\.innerHTML\s*=|\.outerHTML\s*=|insertAdjacentHTML\(|document\.write\(|\[innerHTML\]\s*=|\{@html\s", "web"),
    ("EVAL", "A05 Injection", "High", "Dynamic code execution", r"\beval\s*\(|new\s+Function\s*\(|setTimeout\(\s*[\"'`]|setInterval\(\s*[\"'`]", "js"),
    ("SQL_CONCAT", "A05 Injection", "High", "SQL built by string concatenation/interpolation",
     r"(?i)(?:query|execute|exec|raw|prepare)\s*\(\s*(?:f[\"']|[\"'`][^\"'`]*\b(?:select|insert|update|delete)\b[^\"'`]*(?:\$\{|[\"'`]\s*\+|%s?[\"']\s*%|\{))", "code"),
    ("COMMAND_EXEC", "A05 Injection", "High", "Shell/command execution: check for user-controlled input",
     r"child_process|\bexecSync\(|\bexec\(\s*[`\"'][^`\"']*\$\{|os\.system\(|subprocess\.[a-z_]+\([^)]*shell\s*=\s*True|shell_exec\(|passthru\(", "code"),
    ("PATH_FROM_REQUEST", "A01 Broken Access Control", "High", "File path built from request input (path traversal risk)",
     r"(?:readFile|createReadStream|sendFile|download|open|send_file|send_from_directory)\s*\([^)]*(?:req\.(?:params|query|body)|request\.(?:args|form|GET|POST)|\$_(?:GET|POST|REQUEST))", "code"),
    ("OPEN_REDIRECT", "A01 Broken Access Control", "Medium", "Redirect target taken from request input",
     r"redirect\s*\(\s*(?:req\.(?:query|params|body)|request\.(?:args|form|GET)|\$_(?:GET|REQUEST))|location\.href\s*=\s*(?:new URLSearchParams|params\.get|route\.query)", "code"),
    ("TLS_VERIFY_OFF", "A04 Cryptographic Failures", "High", "TLS certificate verification disabled",
     r"rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED\s*=?\s*[\"']?0|verify\s*=\s*False|InsecureSkipVerify\s*:\s*true|CURLOPT_SSL_VERIFYPEER\s*,\s*(?:false|0)", "code"),
    ("WEAK_HASH_FOR_SECRETS", "A04 Cryptographic Failures", "High", "MD5/SHA1 near password/secret handling",
     r"(?i)(?:md5|sha1)\s*\([^)]*(?:pass|pwd|secret|token)|(?:pass|pwd|secret|token)[^\n]{0,40}(?:md5|sha1)\s*\(", "code"),
    ("INSECURE_RANDOM", "A04 Cryptographic Failures", "Medium", "Math.random/random used for security values",
     r"(?i)(?:token|secret|password|nonce|otp|salt|session)[^\n]{0,40}(?:Math\.random\(|random\.random\(|random\.randint\()", "code"),
    ("UNSAFE_DESERIALISE", "A08 Software or Data Integrity Failures", "High", "Unsafe deserialisation",
     r"pickle\.loads?\(|yaml\.load\((?![^)]*SafeLoader)|\bunserialize\(|ObjectInputStream|BinaryFormatter", "code"),
    ("JWT_VERIFY_OFF", "A07 Authentication Failures", "High", "JWT decoded without verification / 'none' algorithm",
     r"(?i)jwt\.decode\([^)]*verify\s*=\s*False|verify_signature[\"']?\s*:\s*False|algorithms?\s*[:=]\s*\[?[\"']none[\"']", "code"),
    ("CORS_WILDCARD", "A02 Security Misconfiguration", "Medium", "CORS allows any origin (worse with credentials)",
     r"Access-Control-Allow-Origin[\"']?\s*[,:]\s*[\"']\*|cors\(\s*\{\s*origin\s*:\s*(?:[\"']\*[\"']|true)|CORS_ORIGIN_ALLOW_ALL\s*=\s*True|allow_origins\s*=\s*\[\s*[\"']\*", "code"),
    ("COOKIE_FLAGS", "A07 Authentication Failures", "Medium", "Cookie/session configured without secure flags",
     r"(?i)(?:httpOnly|http_only)\s*[:=]\s*false|secure\s*:\s*false|SESSION_COOKIE_SECURE\s*=\s*False|sameSite\s*:\s*[\"']none[\"'](?![^\n]*secure\s*:\s*true)", "code"),
    ("DEBUG_IN_CONFIG", "A02 Security Misconfiguration", "Medium", "Debug mode / production source maps enabled",
     r"(?m)^\s*DEBUG\s*=\s*True|app\.run\([^)]*debug\s*=\s*True|productionSourceMap\s*:\s*true|sourcemap\s*:\s*true|devtool\s*:\s*[\"']source-map", "code"),
    ("CSP_WEAK_IN_CODE", "A02 Security Misconfiguration", "Medium", "CSP in code/config with unsafe-* or dev hosts",
     r"(?i)content-security-policy[^\n]*(?:unsafe-eval|unsafe-inline[^\n]*script|localhost|127\.0\.0\.1)", "any"),
    ("TARGET_BLANK_NO_REL", "A01 Broken Access Control", "Low", "target=_blank without rel=noopener (old browsers)",
     r"target=[\"']_blank[\"'](?![^>]*rel=[\"'][^\"']*noopener)", "web"),
    ("HTTP_URL_IN_CODE", "A04 Cryptographic Failures", "Low", "Plain http:// endpoint in application code",
     r"[\"'`]http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|www\.w3\.org|schemas\.|example\.)[a-z0-9.-]+", "js"),
]

CLIENT_ENV = re.compile(r"(?m)^\s*(?:export\s+)?((?:VITE|NEXT_PUBLIC|REACT_APP|NUXT_PUBLIC|PUBLIC|EXPO_PUBLIC|GATSBY)_[A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PRIVATE|AUTH|API_KEY|KEY))\s*=\s*(.*)$")
CLIENT_ENV_USE = re.compile(r"(?:import\.meta\.env|process\.env)\.((?:VITE|NEXT_PUBLIC|REACT_APP|NUXT_PUBLIC|PUBLIC|EXPO_PUBLIC|GATSBY)_[A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PRIVATE|AUTH|KEY))")


def kind(path):
    low = path.lower()
    if low.endswith((".vue", ".svelte", ".html", ".htm", ".jsx", ".tsx")):
        return {"web", "js", "code", "any"}
    if low.endswith((".js", ".mjs", ".cjs", ".ts")):
        return {"js", "code", "any", "web"}
    if low.endswith((".py", ".php", ".rb", ".go", ".cs", ".java", ".kt")):
        return {"code", "any"}
    return {"any", "config"}


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            p = os.path.join(d, f)
            if f.endswith((".min.js", ".map", ".lock")) or f in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml") or f in SKIP_FILES:
                continue
            if not (f.endswith(TEXT_EXT) or f in SPECIAL_NAMES or f.startswith(".env")):
                continue
            try:
                if os.path.getsize(p) > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield p


def scan(root, max_per_rule, use_git=True):
    hits = {}
    meta = {"stack": [], "dependency_manifests": [], "lockfiles": [], "security_tooling": []}

    def add(rule, owasp, sev, desc, path, text, idx, shown=None):
        r = hits.setdefault(rule, {"rule": rule, "owasp": owasp, "severity_hint": sev, "description": desc, "hits": []})
        if len(r["hits"]) < max_per_rule:
            line = text.count("\n", 0, idx) + 1
            ln = text.splitlines()[line - 1] if text else ""
            relp = os.path.relpath(path, root).replace("\\", "/")
            r["hits"].append({"file": relp, "line": line, "in_test_path": bool(TEST_PATH.search(relp)),
                              "snippet": shown if shown is not None else re.sub(r"\s+", " ", ln.strip())[:140]})
        r["count"] = r.get("count", 0) + 1
        r.setdefault("base_severity", sev)

    for name in ("package.json", "requirements.txt", "pyproject.toml", "Pipfile", "composer.json", "Gemfile", "go.mod", "pom.xml", "build.gradle", "*.csproj"):
        if os.path.exists(os.path.join(root, name)):
            meta["dependency_manifests"].append(name)
    for name in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock", "composer.lock", "Gemfile.lock", "go.sum"):
        if os.path.exists(os.path.join(root, name)):
            meta["lockfiles"].append(name)
    for p, label in [(".github/dependabot.yml", "Dependabot"), (".github/workflows", "GitHub Actions"), (".gitleaks.toml", "gitleaks config"),
                     (".semgrep.yml", "Semgrep config"), ("SECURITY.md", "SECURITY.md"), (".snyk", "Snyk")]:
        if os.path.exists(os.path.join(root, p)):
            meta["security_tooling"].append(label)
    try:
        pkg = json.load(open(os.path.join(root, "package.json"), encoding="utf-8"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        meta["stack"] = [f"{k}@{v}" for k, v in deps.items() if k in ("vue", "react", "next", "nuxt", "@angular/core", "svelte", "express", "fastify", "koa", "firebase", "firebase-admin", "@supabase/supabase-js", "graphql", "dompurify", "helmet", "jsonwebtoken", "axios", "bootstrap", "jquery")]
    except Exception:
        pass

    for path in walk(root):
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        base = os.path.basename(path)
        k = kind(path)
        rel = os.path.relpath(path, root).replace("\\", "/")
        is_test = bool(TEST_PATH.search(rel))

        for label, pat in SECRET_PATTERNS:
            for m in re.finditer(pat, text):
                sev = "Info" if label.startswith("Google API key") else "Critical"
                add("SECRET", "A04 Cryptographic Failures / A02", sev,
                    "Possible secret in the repository (value redacted). Rotate it if real, then remove it from code AND git history",
                    path, text, m.start(), f"{label}: {redact(m.group(0))}")

        if base.startswith(".env"):
            for m in CLIENT_ENV.finditer(text):
                add("CLIENT_EXPOSED_SECRET_ENV", "A04 Cryptographic Failures", "High",
                    "Secret-named variable with a client-bundle prefix (VITE_/NEXT_PUBLIC_/REACT_APP_…): it ships to every browser",
                    path, text, m.start(), f"{m.group(1)}={redact(m.group(2)) if m.group(2).strip() else '(empty)'}")
        for m in CLIENT_ENV_USE.finditer(text):
            add("CLIENT_EXPOSED_SECRET_ENV", "A04 Cryptographic Failures", "High",
                "Secret-named client env variable used in front-end code: it ships to every browser", path, text, m.start())

        if base in ("firestore.rules", "storage.rules", "database.rules.json"):
            for m in re.finditer(r"allow\s+(?:read|write|read,\s*write)[^;]*:\s*if\s+true|[\"']\.(?:read|write)[\"']\s*:\s*(?:true|[\"']true[\"'])", text):
                add("FIREBASE_RULES_OPEN", "A01 Broken Access Control", "Critical", "Firebase security rules allow public access", path, text, m.start())

        if base == "Dockerfile" and not re.search(r"(?m)^\s*USER\s+(?!root\b)", text):
            add("DOCKER_RUNS_AS_ROOT", "A02 Security Misconfiguration", "Low", "Dockerfile never switches to a non-root USER", path, text, 0, "no non-root USER instruction")

        if "/.github/workflows/" in "/" + rel and rel.endswith((".yml", ".yaml")):
            for m in re.finditer(r"pull_request_target", text):
                add("CI_PR_TARGET", "A08 Software or Data Integrity Failures", "High", "pull_request_target runs with secrets on untrusted PR code: review carefully", path, text, m.start())
            for m in re.finditer(r"run:[^\n]*\$\{\{\s*github\.event\.(?:issue|pull_request|comment|head_commit|review)[^}]*\}\}", text):
                add("CI_SCRIPT_INJECTION", "A05 Injection", "High", "Untrusted event data interpolated into a run: step (script injection)", path, text, m.start())
            for m in re.finditer(r"uses:\s*[\w.-]+/[\w./-]+@(?:main|master|latest)\b", text):
                add("CI_UNPINNED_ACTION", "A03 Software Supply Chain Failures", "Medium", "Third-party action pinned to a moving branch (pin to a release or commit SHA)", path, text, m.start())

        for rid, owasp, sev, desc, pat, filt in CODE_RULES:
            if filt not in k:
                continue
            for m in re.finditer(pat, text):
                add(rid, owasp, sev, desc, path, text, m.start())

    if use_git and os.path.isdir(os.path.join(root, ".git")):
        try:
            tracked = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True, timeout=60).stdout.splitlines()
            for f in tracked:
                b = os.path.basename(f)
                if (b.startswith(".env") and not re.search(r"\.(example|sample|template|dist)$", b)) or b.endswith((".pem", ".key", ".p12", ".pfx", ".keystore", ".jks")) or b in ("id_rsa", "id_ed25519", "credentials.json", "service-account.json"):
                    r = hits.setdefault("SENSITIVE_FILE_TRACKED", {"rule": "SENSITIVE_FILE_TRACKED", "owasp": "A04 Cryptographic Failures / A02", "severity_hint": "High",
                                                                   "description": "Sensitive-looking file committed to git (check contents; remove from history if real)", "hits": [], "count": 0})
                    r["hits"].append({"file": f, "line": 0, "snippet": "tracked by git"}); r["count"] += 1
            log = subprocess.run(["git", "-C", root, "log", "-p", "--all", "-n", "300", "--no-color", "--unified=0"], capture_output=True, text=True, timeout=120).stdout
            seen = set()
            for label, pat in SECRET_PATTERNS:
                for m in re.finditer(pat, "\n".join(l for l in log.splitlines() if l.startswith("-") and not l.startswith("---"))):
                    key = (label, m.group(0)[:12])
                    if key in seen:
                        continue
                    seen.add(key)
                    r = hits.setdefault("SECRET_IN_GIT_HISTORY", {"rule": "SECRET_IN_GIT_HISTORY", "owasp": "A04 Cryptographic Failures / A02", "severity_hint": "High",
                                                                  "description": "Possible secret removed from code but still in git history (last 300 commits). Rotate it.", "hits": [], "count": 0})
                    if len(r["hits"]) < max_per_rule:
                        r["hits"].append({"file": "(git history)", "line": 0, "snippet": f"{label}: {redact(m.group(0))}"})
                    r["count"] += 1
        except Exception as e:
            meta["git_error"] = str(e)[:200]

    if not meta["lockfiles"] and meta["dependency_manifests"]:
        hits["NO_LOCKFILE"] = {"rule": "NO_LOCKFILE", "owasp": "A03 Software Supply Chain Failures", "severity_hint": "Medium",
                               "description": "Dependency manifest without a lockfile: builds aren't reproducible", "count": 1,
                               "hits": [{"file": ", ".join(meta["dependency_manifests"]), "line": 0, "snippet": "no lockfile"}]}
    if "Dependabot" not in meta["security_tooling"] and meta["dependency_manifests"]:
        hits["NO_DEPENDENCY_UPDATES"] = {"rule": "NO_DEPENDENCY_UPDATES", "owasp": "A03 Software Supply Chain Failures", "severity_hint": "Low",
                                         "description": "No Dependabot (or similar) config found for automated dependency updates", "count": 1,
                                         "hits": [{"file": "(repo)", "line": 0, "snippet": "no .github/dependabot.yml"}]}

    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
    for r in hits.values():
        r.setdefault("base_severity", r["severity_hint"])
        if r["hits"] and all(h.get("in_test_path") for h in r["hits"]) and order[r["base_severity"]] < order["Low"]:
            r["severity_hint"] = "Low"
            r["description"] += " (only in test/fixture paths)"
    results = sorted(hits.values(), key=lambda r: (order[r["severity_hint"]], -r["count"]))
    return {"root": os.path.abspath(root), **meta, "results": results,
            "note": "Leads only; confirm in context. Secret values are redacted: never paste full values anywhere. Rules whose hits are all in test/fixture paths are downgraded to Low."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--json")
    ap.add_argument("--max-per-rule", type=int, default=25)
    ap.add_argument("--no-git", action="store_true", help="skip git ls-files / history checks")
    a = ap.parse_args()
    res = scan(a.root, a.max_per_rule, not a.no_git)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
    print(f"Stack: {', '.join(res['stack']) or 'unknown'} | manifests: {', '.join(res['dependency_manifests']) or 'none'} | lockfiles: {', '.join(res['lockfiles']) or 'none'} | tooling: {', '.join(res['security_tooling']) or 'none'}")
    for r in res["results"]:
        print(f"\n[{r['severity_hint']}] {r['rule']} ({r['owasp']}): {r['description']} — {r['count']} hit(s)")
        for h in r["hits"][:5]:
            print(f"   {h['file']}:{h['line']}  {h['snippet']}")
    print("\n" + res["note"])


if __name__ == "__main__":
    sys.exit(main())
