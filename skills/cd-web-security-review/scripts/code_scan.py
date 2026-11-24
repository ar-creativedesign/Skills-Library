#!/usr/bin/env python3
"""Static security scan of a codebase (web front end, Node, Python, PHP, config, CI, containers).

Produces LEADS, not findings: confirm every hit by reading the code in context before reporting.
Secret values are always redacted in the output.

    python code_scan.py <repo-root> [--json out.json] [--sarif out.sarif] [--max-per-rule 25] [--no-git]
    python code_scan.py <repo-root> --branch [--base auto|<branch>] [--json out.json] [--sarif out.sarif]

Standard library only. Skips node_modules, build output and vendored folders.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

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


def parse_json_relaxed(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    pattern = r'("(?:\\.|[^"\\])*")|//.*?$|/\*.*?\*/'
    cleaned = re.sub(pattern, lambda m: m.group(1) if m.group(1) else "", text, flags=re.MULTILINE | re.DOTALL)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return json.loads(cleaned)


def sh(args, cwd):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout


def ref_exists(repo, ref):
    return sh(["git", "rev-parse", "--verify", "--quiet", ref + "^{commit}"], repo)[0] == 0


def pick_ref(repo, names):
    for n in names:
        for ref in (n, f"origin/{n}"):
            if ref_exists(repo, ref):
                return ref
    return None


def detect_base(repo, requested):
    _, cur = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo)
    cur = cur.strip()
    if requested and requested != "auto":
        ref = pick_ref(repo, [requested])
        return cur, ref, None if ref else f"base branch '{requested}' not found"
    if cur in ("main", "master"):
        return cur, None, "on main/master: run a full scan instead"
    if cur in ("develop", "staging"):
        ref = pick_ref(repo, ["main", "master"])
    else:
        ref = pick_ref(repo, ["develop", "staging", "main", "master"])
    return cur, ref, None if ref else "no develop/staging/main/master branch found; pass --base"


def changed_on_branch(repo, base):
    _, mb = sh(["git", "merge-base", "HEAD", base], repo)
    mb = mb.strip()
    _, names = sh(["git", "diff", "--name-status", mb], repo)
    files, deleted = set(), set()
    for line in names.splitlines():
        parts = line.split("\t")
        if not parts or not parts[0]:
            continue
        if parts[0].startswith("D"):
            deleted.add(parts[1].replace("\\", "/"))
        else:
            files.add(parts[-1].replace("\\", "/"))
    _, untracked = sh(["git", "ls-files", "--others", "--exclude-standard"], repo)
    new_files = set(u.replace("\\", "/") for u in untracked.splitlines() if u)
    files |= new_files
    lines = defaultdict(set)
    _, diff = sh(["git", "diff", "-U0", mb], repo)
    cur = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            cur = line[6:] if line.startswith("+++ b/") else None
            if cur:
                cur = cur.replace("\\", "/")
        elif line.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            start, count = int(m.group(1)), int(m.group(2) or 1)
            lines[cur].update(range(start, start + count))
    _, added = sh(["git", "diff", "--name-status", "--diff-filter=A", mb], repo)
    new_files |= {l.split("\t")[-1].replace("\\", "/") for l in added.splitlines() if l}
    _, commits = sh(["git", "rev-list", "--count", f"{mb}..HEAD"], repo)
    _, dirty = sh(["git", "status", "--porcelain"], repo)
    return {
        "merge_base": mb, "files": sorted(files), "deleted": sorted(deleted),
        "new_files": sorted(new_files), "lines": lines,
        "commits": int(commits.strip() or 0),
        "uncommitted": len([l for l in dirty.splitlines() if l])
    }


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


def walk(root, only_files=None):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            p = os.path.join(d, f)
            if f.endswith((".min.js", ".map", ".lock")) or f in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml") or f in SKIP_FILES:
                continue
            if not (f.endswith(TEXT_EXT) or f in SPECIAL_NAMES or f.startswith(".env")):
                continue
            relp = os.path.relpath(p, root).replace("\\", "/")
            if only_files is not None and relp not in only_files:
                continue
            try:
                if os.path.getsize(p) > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield p


def scan(root, max_per_rule, use_git=True, branch=False, base="auto"):
    hits = {}
    meta = {"stack": [], "dependency_manifests": [], "lockfiles": [], "security_tooling": []}
    ch = None

    if branch and use_git and os.path.isdir(os.path.join(root, ".git")):
        cur, b_ref, err = detect_base(root, base)
        if err or not b_ref:
            meta["branch_error"] = err or "no base branch detected"
        else:
            ch = changed_on_branch(root, b_ref)
            meta["branch"] = cur
            meta["base"] = b_ref
            meta["merge_base"] = ch["merge_base"]
            meta["commits"] = ch["commits"]
            meta["uncommitted"] = ch["uncommitted"]

    def add(rule, owasp, sev, desc, path, text, idx, shown=None):
        relp = os.path.relpath(path, root).replace("\\", "/")
        line = text.count("\n", 0, idx) + 1 if text else 0
        if ch is not None:
            if relp not in ch["files"]:
                return
            if line > 0 and relp not in ch["new_files"]:
                if line not in ch["lines"].get(relp, set()):
                    return

        r = hits.setdefault(rule, {"rule": rule, "owasp": owasp, "severity_hint": sev, "description": desc, "hits": []})
        if len(r["hits"]) < max_per_rule:
            ln = text.splitlines()[line - 1] if (text and line > 0 and line <= len(text.splitlines())) else ""
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
    pkg_path = os.path.join(root, "package.json")
    if os.path.exists(pkg_path):
        try:
            pkg = parse_json_relaxed(open(pkg_path, encoding="utf-8", errors="ignore").read())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            meta["stack"] = [f"{k}@{v}" for k, v in deps.items() if k in ("vue", "react", "next", "nuxt", "@angular/core", "svelte", "express", "fastify", "koa", "firebase", "firebase-admin", "@supabase/supabase-js", "graphql", "dompurify", "helmet", "jsonwebtoken", "axios", "bootstrap", "jquery")]
        except Exception:
            pass

    only_files = set(ch["files"]) if ch is not None else None
    for path in walk(root, only_files=only_files):
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        base = os.path.basename(path)
        k = kind(path)
        rel = os.path.relpath(path, root).replace("\\", "/")

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
                f_norm = f.replace("\\", "/")
                if ch is not None and f_norm not in ch["files"]:
                    continue
                b = os.path.basename(f)
                if (b.startswith(".env") and not re.search(r"\.(example|sample|template|dist)$", b)) or b.endswith((".pem", ".key", ".p12", ".pfx", ".keystore", ".jks")) or b in ("id_rsa", "id_ed25519", "credentials.json", "service-account.json"):
                    r = hits.setdefault("SENSITIVE_FILE_TRACKED", {"rule": "SENSITIVE_FILE_TRACKED", "owasp": "A04 Cryptographic Failures / A02", "severity_hint": "High",
                                                                   "description": "Sensitive-looking file committed to git (check contents; remove from history if real)", "hits": [], "count": 0})
                    r["hits"].append({"file": f_norm, "line": 0, "snippet": "tracked by git"}); r["count"] += 1

            if ch is not None:
                log_args = ["git", "-C", root, "log", "-p", f"{ch['merge_base']}..HEAD", "--no-color", "--unified=0"]
            else:
                log_args = ["git", "-C", root, "log", "-p", "--all", "-n", "300", "--no-color", "--unified=0"]
            log = subprocess.run(log_args, capture_output=True, text=True, timeout=120).stdout
            seen = set()
            for label, pat in SECRET_PATTERNS:
                for m in re.finditer(pat, "\n".join(l for l in log.splitlines() if l.startswith("-") and not l.startswith("---"))):
                    key = (label, m.group(0)[:12])
                    if key in seen:
                        continue
                    seen.add(key)
                    r = hits.setdefault("SECRET_IN_GIT_HISTORY", {"rule": "SECRET_IN_GIT_HISTORY", "owasp": "A04 Cryptographic Failures / A02", "severity_hint": "High",
                                                                  "description": "Possible secret removed from code but still in git history. Rotate it.", "hits": [], "count": 0})
                    if len(r["hits"]) < max_per_rule:
                        r["hits"].append({"file": "(git history)", "line": 0, "snippet": f"{label}: {redact(m.group(0))}"})
                    r["count"] += 1
        except Exception as e:
            meta["git_error"] = str(e)[:200]

    if not meta["lockfiles"] and meta["dependency_manifests"] and ch is None:
        hits["NO_LOCKFILE"] = {"rule": "NO_LOCKFILE", "owasp": "A03 Software Supply Chain Failures", "severity_hint": "Medium",
                               "description": "Dependency manifest without a lockfile: builds aren't reproducible", "count": 1,
                               "hits": [{"file": ", ".join(meta["dependency_manifests"]), "line": 0, "snippet": "no lockfile"}]}
    if "Dependabot" not in meta["security_tooling"] and meta["dependency_manifests"] and ch is None:
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


def to_sarif(tool_name, tool_version, results, root=""):
    level_map = {
        "Critical": "error",
        "High": "error",
        "Medium": "warning",
        "Low": "note",
        "Info": "note",
    }
    sarif_rules = []
    sarif_results = []
    seen_rules = set()

    for item in results:
        rid = item.get("rule")
        if not rid:
            continue
        if rid not in seen_rules:
            seen_rules.add(rid)
            sarif_rules.append({
                "id": rid,
                "name": rid,
                "shortDescription": {
                    "text": item.get("description", rid)
                },
                "defaultConfiguration": {
                    "level": level_map.get(item.get("severity_hint", "Info"), "note")
                }
            })
        for hit in item.get("hits", []):
            fpath = hit.get("file", "")
            lvl = level_map.get(item.get("severity_hint", "Info"), "note")
            if fpath in ("(git history)", "(repo)", "unknown"):
                sarif_results.append({
                    "ruleId": rid,
                    "level": lvl,
                    "message": {
                        "text": f"{item.get('description', '')}: {hit.get('snippet', '')}".strip()
                    }
                })
                continue
            ln = max(1, hit.get("line", 1))
            sarif_results.append({
                "ruleId": rid,
                "level": lvl,
                "message": {
                    "text": hit.get("snippet") or item.get("description", "")
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": fpath.replace("\\", "/"),
                                "uriBaseId": "%SRCROOT%"
                            },
                            "region": {
                                "startLine": ln
                            }
                        }
                    }
                ]
            })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": tool_version,
                        "rules": sarif_rules
                    }
                },
                "results": sarif_results
            }
        ]
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--json")
    ap.add_argument("--sarif")
    ap.add_argument("--branch", action="store_true", help="scan only branch changes vs merge-base")
    ap.add_argument("--base", default="auto", help="base branch to compare against (default: auto)")
    ap.add_argument("--max-per-rule", type=int, default=25)
    ap.add_argument("--no-git", action="store_true", help="skip git ls-files / history checks")
    a = ap.parse_args()
    res = scan(a.root, a.max_per_rule, not a.no_git, branch=a.branch, base=a.base)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
    if a.sarif:
        with open(a.sarif, "w", encoding="utf-8") as f:
            json.dump(to_sarif("cd-web-security-review", "1.3.0", res["results"], a.root), f, indent=1)
    print(f"Stack: {', '.join(res['stack']) or 'unknown'} | manifests: {', '.join(res['dependency_manifests']) or 'none'} | lockfiles: {', '.join(res['lockfiles']) or 'none'} | tooling: {', '.join(res['security_tooling']) or 'none'}")
    if res.get("branch"):
        print(f"Branch mode: {res['branch']} vs {res['base']} ({res.get('commits', 0)} commit(s), {res.get('uncommitted', 0)} uncommitted file(s))")
    for r in res["results"]:
        print(f"\n[{r['severity_hint']}] {r['rule']} ({r['owasp']}): {r['description']} — {r['count']} hit(s)")
        for h in r["hits"][:5]:
            print(f"   {h['file']}:{h['line']}  {h['snippet']}")
    print("\n" + res["note"])


if __name__ == "__main__":
    sys.exit(main())
