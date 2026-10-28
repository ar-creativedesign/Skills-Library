#!/usr/bin/env python3
"""Lead finder for cd-vue-code-review. Standard-library Python only; read-only.

Full mode:    python vue_scan.py <repo> --json out.json [--template <template-clone>]
Branch mode:  python vue_scan.py <repo> --branch [--base auto|<branch>] --json out.json

Branch mode compares against the merge-base with the base branch and includes staged, unstaged and
untracked (not ignored) changes. Line-level leads are reported only on added or changed lines; file-level
leads only for changed files. Every hit is a LEAD: the reviewer confirms it by reading the code.

Tiers: fix-now (High), should-fix (Medium), tidy (Low), info.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", "dist-ssr", ".git", "coverage", ".vite", ".nuxt", ".output", "reports", ".templateScripts"}
CODE_EXT = {".vue", ".ts", ".tsx", ".js", ".mjs", ".cjs"}
SRC_FOLDERS = {"assets", "components", "composables", "router", "services", "stores", "utils", "views",
               "types", "layouts", "plugins", "directives", "constants", "config", "i18n", "locales", "lib", "features", "modules", "pages"}
SRC_ROOT_OK = {"App.vue", "main.ts", "main.js", "vite-env.d.ts", "env.d.ts", "shims-vue.d.ts"}
STRAY = re.compile(r"(\.(bak|orig|tmp|swp|log)$|~$|\.DS_Store$|(^|[ _.-])(copy|old|backup)([ _.-]|\.|$)|\(\d+\)\.)", re.I)
PHYSICAL_TW = re.compile(r"(?<![\w-])(?:[a-z0-9]+:)*(ml|mr|pl|pr|left|right|border-l|border-r|rounded-l|rounded-r|rounded-tl|rounded-tr|rounded-bl|rounded-br|text-left|text-right|float-left|float-right|scroll-ml|scroll-mr|scroll-pl|scroll-pr)(?:-[\w./\[\]#%]+)?(?![\w-])")
CLASS_ATTR = re.compile(r'(?<![:\w-])class\s*=\s*"([^"]+)"')
HEX_IN_CLASS = re.compile(r"\b(?:bg|text|border|from|to|via|fill|stroke|ring|shadow|outline|decoration)-\[(?:#|rgb|hsl)")
RAW_COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")
ANIM = re.compile(r"(?<![\w:-])(?:[a-z0-9-]+:)*(animate-[\w-]+|transition(?:-[\w-]+)?)(?![\w-])")
CONSOLE = re.compile(r"\bconsole\.(log|warn|error|info|debug|trace|table)\s*\(")
ANY = re.compile(r"(:\s*any\b|\bas\s+any\b|<any>|\bany\[\])")
REACTIVE = re.compile(r"\breactive\s*\(")
NET = re.compile(r"\b(fetch\s*\(|axios(\.\w+)?\s*\(|\$fetch\s*\(|ky(\.\w+)?\s*\(|new\s+XMLHttpRequest)")
EMPTY_CATCH = re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*\}|\.catch\(\s*\(?\s*\w*\s*\)?\s*=>\s*(\{\s*\}|undefined|null)\s*\)")
TODO = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
VFOR = re.compile(r"<[\w-]+[^>]*\sv-for=")
EXPORT_FN = re.compile(r"^\s*export\s+(?:default\s+)?(?:async\s+)?(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*(?::[^=]+)?=>|const\s+(\w+)\s*=\s*defineStore)")
STATIC_VIEW_IMPORT = re.compile(r"^\s*import\s+\w+\s+from\s+['\"][^'\"]*/views/[^'\"]+['\"]")
OPTIONS_API = re.compile(r"export\s+default\s+(defineComponent\s*\()?\s*\{")
RUNTIME_PROPS = re.compile(r"defineProps\s*\(\s*[\[{]")
RUNTIME_EMITS = re.compile(r"defineEmits\s*\(\s*\[")
PROP_MUTATION = re.compile(r"\bprops\.\w+\s*(=(?!=)|\+\+|--|\+=|-=)")
DEEP_WATCH = re.compile(r"deep\s*:\s*true")
OPTIONS_STORE = re.compile(r"defineStore\(\s*['\"][^'\"]+['\"]\s*,\s*\{")
STORE_DESTRUCTURE = re.compile(r"const\s*\{[^}]+\}\s*=\s*use\w+Store\(\s*\)")
CODEY = re.compile(r"[;{}()=]|^\s*(const|let|var|if|for|return|import|export|await)\b")


def sh(args, cwd):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout


def parse_json_relaxed(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    pattern = r'("(?:\\.|[^"\\])*")|//.*?$|/\*.*?\*/'
    cleaned = re.sub(pattern, lambda m: m.group(1) if m.group(1) else "", text, flags=re.MULTILINE | re.DOTALL)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return json.loads(cleaned)


def walk(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS and (not d.startswith(".") or d in (".github", ".husky")))
        for f in sorted(fns):
            yield Path(dp) / f


# ---------------- branch mode helpers
def ref_exists(repo, ref):
    return sh(["git", "rev-parse", "--verify", "--quiet", ref + "^{commit}"], repo)[0] == 0


def pick(repo, names):
    for n in names:
        for ref in (n, f"origin/{n}"):
            if ref_exists(repo, ref):
                return ref
    return None


def detect_base(repo, requested):
    _, cur = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo)
    cur = cur.strip()
    if requested and requested != "auto":
        ref = pick(repo, [requested])
        return cur, ref, None if ref else f"base branch '{requested}' not found"
    if cur in ("main", "master"):
        return cur, None, "on main/master: run a full project review instead"
    if cur in ("develop", "staging"):
        ref = pick(repo, ["main", "master"])
    else:
        ref = pick(repo, ["develop", "staging", "main", "master"])
    return cur, ref, None if ref else "no develop/staging/main/master branch found; pass --base"


def changed(repo, base):
    _, mb = sh(["git", "merge-base", "HEAD", base], repo)
    mb = mb.strip()
    _, names = sh(["git", "diff", "--name-status", mb], repo)  # committed + staged + unstaged vs merge-base
    files, deleted = set(), set()
    for line in names.splitlines():
        parts = line.split("\t")
        if not parts or not parts[0]:
            continue
        if parts[0].startswith("D"):
            deleted.add(parts[1])
        else:
            files.add(parts[-1])
    _, untracked = sh(["git", "ls-files", "--others", "--exclude-standard"], repo)
    new_files = set(u for u in untracked.splitlines() if u)
    files |= new_files
    lines = defaultdict(set)
    _, diff = sh(["git", "diff", "-U0", mb], repo)
    cur = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            cur = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            start, count = int(m.group(1)), int(m.group(2) or 1)
            lines[cur].update(range(start, start + count))
    _, added = sh(["git", "diff", "--name-status", "--diff-filter=A", mb], repo)
    new_files |= {l.split("\t")[-1] for l in added.splitlines() if l}
    _, commits = sh(["git", "rev-list", "--count", f"{mb}..HEAD"], repo)
    _, dirty = sh(["git", "status", "--porcelain"], repo)
    return {"merge_base": mb, "files": sorted(files), "deleted": sorted(deleted), "new_files": sorted(new_files),
            "lines": lines, "commits": int(commits.strip() or 0), "uncommitted": len([l for l in dirty.splitlines() if l])}


# ---------------- scanning
class Scan:
    def __init__(self, repo, only_files=None, only_lines=None, new_files=None):
        self.repo = repo
        self.only = only_files
        self.lines = only_lines
        self.new_files = new_files or set()
        self.leads = []

    def keep_line(self, rel, ln):
        if self.lines is None or rel in self.new_files:
            return True
        return ln in self.lines.get(rel, set())

    def add(self, tier, rule, rel, ln, msg, source="good practice"):
        if self.only is not None and rel not in self.only:
            return
        if ln and not self.keep_line(rel, ln):
            return
        self.leads.append({"tier": tier, "rule": rule, "file": rel, "line": ln, "message": msg, "source": source})


def sfc_blocks(text):
    blocks = []
    for m in re.finditer(r"^<(template|script|style)\b[^>]*>", text, re.M):
        blocks.append((m.group(1), m.start(), text.count("\n", 0, m.start()) + 1, m.group(0)))
    return blocks


def script_lines(text):
    m = re.search(r"<script\b[^>]*setup[^>]*>(.*?)</script>", text, re.S)
    if not m:
        m = re.search(r"<script\b[^>]*>(.*?)</script>", text, re.S)
    if not m:
        return 0
    return len([l for l in m.group(1).splitlines() if l.strip() and not l.strip().startswith("//")])


def scan_file(s, p, rel, text, agents):
    lines = text.splitlines()
    name = p.name
    ext = p.suffix
    parts = Path(rel).parts
    in_src = parts[:1] == ("src",)
    folder = parts[1] if in_src and len(parts) > 2 else ""
    is_logger = rel.endswith("utils/logger.ts")
    is_service = folder == "services" or name.endswith(".service.ts")
    is_test = bool(re.search(r"\.(spec|test)\.[jt]sx?$", name)) or "__tests__" in parts or parts[:1] == ("tests",)
    A = "AGENTS.md" if agents else "good practice"

    if STRAY.search(name):
        s.add("tidy", "stray file", rel, None, "backup/temp/duplicate-looking file; delete it if unused")
        return  # don't lint a leftover copy: one finding, not every issue twice

    # --- naming and placement
    if in_src:
        if folder == "stores" and ext == ".ts" and not name.endswith(".store.ts") and name != "index.ts":
            s.add("should-fix", "naming", rel, None, "store file should be named `*.store.ts`", A)
        if folder == "services" and ext == ".ts" and not name.endswith(".service.ts") and name != "index.ts":
            s.add("should-fix", "naming", rel, None, "service file should be named `*.service.ts`", A)
        if folder == "composables" and ext in (".ts", ".js") and not re.match(r"use[A-Z]\w*\.(ts|js)$", name) and name != "index.ts":
            s.add("should-fix", "naming", rel, None, "composable should be named `useThing.ts`")
        if ext == ".vue" and not re.match(r"[A-Z][A-Za-z0-9]*\.vue$", name):
            s.add("should-fix", "naming", rel, None, "component file should be PascalCase")
        if folder == "views" and ext == ".vue" and not name.endswith(("View.vue", "Page.vue", "Layout.vue")):
            s.add("tidy", "naming", rel, None, "view should end in `View.vue`")
        if ext == ".vue" and folder in ("stores", "services", "utils", "composables"):
            s.add("should-fix", "placement", rel, None, f"component inside `src/{folder}/`")
        if name.endswith(".store.ts") and folder != "stores":
            s.add("should-fix", "placement", rel, None, "store outside `src/stores/`", A)
        if name.endswith(".service.ts") and folder != "services":
            s.add("should-fix", "placement", rel, None, "service outside `src/services/`", A)
        if len(parts) == 2 and name not in SRC_ROOT_OK and not p.is_dir():
            s.add("should-fix", "placement", rel, None, "loose file in `src/` root; move it into a feature or type folder")
    if ext not in CODE_EXT:
        return

    # --- size
    n = len(lines)
    if ext == ".vue":
        sl = script_lines(text)
        if sl > 50:
            s.add("should-fix", "composable extraction", rel, None, f"`<script setup>` has {sl} code lines (> 50); extract logic into composables", A)
        if n > 300:
            s.add("should-fix", "component size", rel, None, f"{n} lines; split into smaller components")
        order = [b[0] for b in sfc_blocks(text)]
        want = [b for b in ("template", "script", "style") if b in order]
        dedup = []
        for b in order:
            if b not in dedup:
                dedup.append(b)
        if dedup != want and agents:
            s.add("tidy", "block order", rel, 1, "SFC block order should be template → script → style", A)
        for b in sfc_blocks(text):
            if b[0] == "script" and 'lang="ts"' not in b[3] and "lang='ts'" not in b[3]:
                s.add("should-fix", "TypeScript", rel, b[2], "`<script>` without `lang=\"ts\"`", A)
        if OPTIONS_API.search(text) and "<script setup" not in text:
            s.add("should-fix", "Composition API", rel, None, "Options API component; use `<script setup lang=\"ts\">`", A)
    elif n > 400 and not is_test:
        s.add("should-fix", "file size", rel, None, f"{n} lines; split by responsibility")
    if name.endswith(".store.ts") and n > 250:
        s.add("fix-now", "mega-store", rel, None, f"store is {n} lines; split by domain", A)

    # --- line rules
    comment_run, run_start, comment_lines = 0, 0, 0
    in_template = ext != ".vue"
    for i, line in enumerate(lines, 1):
        st = line.strip()
        if ext == ".vue":
            if st.startswith("<template"):
                in_template = True
            elif st.startswith("<script") or st.startswith("<style"):
                in_template = False
        if st.startswith("//") or (st.startswith("*") and not st.startswith("*/")) or st.startswith("/*"):
            comment_lines += 1
        if st.startswith("//") and CODEY.search(st[2:]):
            if comment_run == 0:
                run_start = i
            comment_run += 1
        else:
            if comment_run >= 6:
                s.add("tidy", "commented-out code", rel, run_start, f"{comment_run} consecutive lines of commented-out code")
            comment_run = 0
        if not is_logger and not is_test and CONSOLE.search(line) and not st.startswith("//"):
            s.add("should-fix", "logging", rel, i, "raw `console.*`; use `logger` from `src/utils/logger.ts`", A)
        if ANY.search(line) and not st.startswith("//") and ext in (".ts", ".tsx", ".vue"):
            s.add("fix-now", "no any", rel, i, "explicit `any` defeats strict typing; give it a real type or `unknown`")
        if REACTIVE.search(line) and "import" not in line:
            s.add("should-fix", "ref over reactive", rel, i, "`reactive()`; prefer `ref()`", A)
        if NET.search(line) and not is_service and not is_test and in_src and not st.startswith("//"):
            s.add("fix-now", "API calls in services", rel, i, "network call outside `src/services/`", A)
        if EMPTY_CATCH.search(line):
            s.add("fix-now", "no silent failure", rel, i, "error swallowed; log it and show the user feedback", A)
        if TODO.search(line):
            s.add("tidy", "TODO", rel, i, st[:100])
        if PROP_MUTATION.search(line):
            s.add("fix-now", "prop mutation", rel, i, "props are read-only; emit an event or use a local copy")
        if OPTIONS_STORE.search(line):
            s.add("should-fix", "setup stores", rel, i, "options-style `defineStore('id', { … })`; use a setup store `defineStore('id', () => { … })`", A)
        if STORE_DESTRUCTURE.search(line) and "storeToRefs" not in line:
            s.add("should-fix", "storeToRefs", rel, i, "store destructured directly; state loses reactivity (use `storeToRefs()`; actions are fine)", A)
        if DEEP_WATCH.search(line):
            s.add("tidy", "deep watcher", rel, i, "`deep: true` watcher; watch a specific getter if possible")
        if RUNTIME_PROPS.search(line):
            s.add("should-fix", "typed props", rel, i, "runtime `defineProps`; use `defineProps<{ … }>()`", A)
        if RUNTIME_EMITS.search(line):
            s.add("should-fix", "typed emits", rel, i, "array `defineEmits`; use `defineEmits<{ … }>()`", A)
        if "/router/" in "/" + rel and STATIC_VIEW_IMPORT.search(line):
            s.add("should-fix", "lazy routes", rel, i, "static view import in router; use `() => import(...)`", A)
        if VFOR.search(line):
            if ":key" not in line and "v-bind:key" not in line and not re.search(r"\skey=", line):
                nxt = " ".join(lines[i:i + 3])
                if ":key" not in nxt:
                    s.add("fix-now", "v-for key", rel, i, "`v-for` without `:key`")
            if " v-if=" in line:
                s.add("fix-now", "v-if with v-for", rel, i, "`v-if` and `v-for` on the same element")
        for cm in CLASS_ATTR.finditer(line):
            cls = cm.group(1)
            ph = sorted({m.group(1) for m in PHYSICAL_TW.finditer(cls)})
            if ph and agents:
                s.add("should-fix", "logical properties (RTL)", rel, i, "physical utilities " + ", ".join(ph) + "; use logical (`ms-`, `pe-`, `text-start`, `border-s`)", A)
            if HEX_IN_CLASS.search(cls):
                s.add("should-fix", "semantic tokens", rel, i, "arbitrary colour value in class; use a theme token", A)
            for am in ANIM.finditer(cls):
                tok = am.group(0)
                if "motion-safe:" not in tok and "motion-reduce:" not in tok and agents:
                    s.add("tidy", "motion-safe", rel, i, f"`{tok}` not guarded with `motion-safe:`", A)
                    break
            if len(cls.split()) >= 15:
                s.add("tidy", "long utility chain", rel, i, f"{len(cls.split())} utilities on one element; consider a `@layer components` class", A)
        if ext == ".vue" and not in_template and RAW_COLOUR.search(line) and "main.css" not in rel and not st.startswith("//"):
            s.add("should-fix", "semantic tokens", rel, i, "hard-coded colour in component; use a theme token", A)
        m = EXPORT_FN.match(line)
        if m and ext in (".ts", ".js") and not is_test:
            prev = "\n".join(lines[max(0, i - 4):i - 1])
            if "*/" not in prev:
                fn = next(g for g in m.groups() if g)
                s.add("tidy", "JSDoc", rel, i, f"exported `{fn}` has no JSDoc intent line", A)
    if comment_run >= 6:
        s.add("tidy", "commented-out code", rel, run_start, f"{comment_run} consecutive lines of commented-out code")
    if n >= 40 and comment_lines / max(n, 1) > 0.35:
        s.add("tidy", "comment density", rel, None, f"{int(100 * comment_lines / n)}% of lines are comments; trim the ones that restate the code")


def chains(s, files):
    """The same long class string repeated across the project: candidate for a @layer components class."""
    seen = defaultdict(list)
    for rel, text in files:
        for i, line in enumerate(text.splitlines(), 1):
            for cm in CLASS_ATTR.finditer(line):
                cls = " ".join(sorted(cm.group(1).split()))
                if len(cls.split()) >= 6:
                    seen[cls].append((rel, i))
    for cls, where in seen.items():
        if len(where) >= 3:
            rel, ln = where[0]
            s.add("should-fix", "repeated utility chain", rel, ln,
                  f"same {len(cls.split())}-utility class list used {len(where)}× (e.g. {', '.join(f'{r}:{l}' for r, l in where[:3])}); extract to `@layer components`",
                  "AGENTS.md")


def unused(s, repo, files):
    """Components/composables/stores/services/utils that nothing imports (leads only)."""
    imports = defaultdict(int)
    texts = {rel: text for rel, text in files}
    for rel, text in files:
        for m in re.finditer(r"""(?:from|import\s*\(|import)\s*['"]([^'"]+)['"]""", text):
            spec = m.group(1)
            if spec.startswith("@/"):
                target = "src/" + spec[2:]
            elif spec.startswith("."):
                target = os.path.normpath(str(Path(rel).parent / spec)).replace("\\", "/")
            else:
                continue
            imports[re.sub(r"\.(vue|ts|js)$", "", target)] += 1
            imports[re.sub(r"\.(vue|ts|js)$", "", target) + "/index"] += 1
    for rel in texts:
        parts = Path(rel).parts
        if len(parts) > 2 and parts[0] == "src" and parts[1] in ("components", "composables", "stores", "services", "utils") \
                and Path(rel).suffix in (".vue", ".ts", ".js") and not rel.endswith(".d.ts") and Path(rel).stem != "index":
            key = re.sub(r"\.(vue|ts|js)$", "", rel)
            stem = Path(rel).stem
            if imports.get(key, 0) == 0 and not any(stem in t for r, t in files if r != rel):
                s.add("should-fix", "unused file", rel, None, "nothing imports this; delete it or wire it up")


def structure(s, repo, agents):
    src = repo / "src"
    if not src.is_dir():
        s.add("info", "structure", "src", None, "no `src/` folder: not a standard Vite + Vue layout")
        return
    for d in sorted(src.iterdir()):
        if d.is_dir():
            if d.name not in SRC_FOLDERS:
                s.add("tidy", "folder layout", f"src/{d.name}", None, "non-standard top-level `src/` folder; document it or fold it into an existing one")
            entries = [e for e in d.rglob("*") if e.is_file()]
            if not entries:
                s.add("tidy", "empty folder", f"src/{d.name}", None, "empty folder")
            elif len([e for e in d.iterdir() if e.is_file()]) > 25:
                s.add("should-fix", "folder size", f"src/{d.name}", None, f"{len([e for e in d.iterdir() if e.is_file()])} files flat in one folder; group by feature")
    tests = [p for p in walk(repo) if re.search(r"\.(spec|test)\.[jt]sx?$", p.name)]
    if not tests:
        s.add("info", "tests", ".", None, "no unit/component tests found (`*.spec.ts` / `*.test.ts`)")
    if not agents:
        s.add("info", "house rules", ".", None, "no AGENTS.md: reviewing against general good practice only")


def drift(s, repo, tpl):
    """Compare quality-gate config with a clone of the template's latest main. Advisory: older projects predate it."""
    cfgs = ["eslint.config.js", "stylelint.config.js", ".prettierrc.json", "tsconfig.json", "commitlint.config.js",
            ".lintstagedrc.json", ".husky/pre-commit", ".husky/commit-msg", "scripts/health-check.js", "AGENTS.md"]
    out = []
    for c in cfgs:
        a, b = repo / c, tpl / c
        if not b.exists():
            continue
        if not a.exists():
            out.append(("should-fix" if c.startswith((".husky", "eslint", "tsconfig")) else "info", c, "missing compared with the template"))
        elif hashlib.sha1(a.read_bytes()).hexdigest() != hashlib.sha1(b.read_bytes()).hexdigest():
            out.append(("info", c, "differs from the template; compare and adopt deliberate improvements"))
    try:
        pj = parse_json_relaxed((repo / "package.json").read_text(encoding="utf-8", errors="ignore"))
        tj = parse_json_relaxed((tpl / "package.json").read_text(encoding="utf-8", errors="ignore"))
        missing = sorted(set(tj.get("scripts", {})) - set(pj.get("scripts", {})))
        gates = [m for m in missing if m.startswith(("lint", "health"))]
        if gates:
            out.append(("should-fix", "package.json", "missing quality scripts: " + ", ".join(gates)))
        rest = [m for m in missing if m not in gates]
        if rest:
            out.append(("info", "package.json", "scripts the template has that this project doesn't: " + ", ".join(rest)))
        tdev = set(tj.get("devDependencies", {}))
        pdev = set(pj.get("devDependencies", {})) | set(pj.get("dependencies", {}))
        tools = sorted(d for d in tdev - pdev if re.match(r"(eslint|stylelint|prettier|vue-tsc|typescript|husky|lint-staged|@commitlint)", d))
        if tools:
            out.append(("should-fix", "package.json", "quality tools the template has but this project lacks: " + ", ".join(tools)))
    except (OSError, ValueError):
        pass
    try:
        ts = parse_json_relaxed((repo / "tsconfig.json").read_text(encoding="utf-8", errors="ignore"))
        if ts.get("compilerOptions", {}).get("strict") is False:
            out.append(("should-fix", "tsconfig.json", "`strict` is off"))
    except (OSError, ValueError):
        pass
    for tier, f, msg in out:
        s.leads.append({"tier": tier, "rule": "template drift", "file": f, "line": None, "message": msg, "source": "template"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--branch", action="store_true", help="review only this branch's changes (incl. uncommitted)")
    ap.add_argument("--base", default="auto")
    ap.add_argument("--template", help="path to a clone of the template's latest main (full mode drift check)")
    ap.add_argument("--json")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    agents = (repo / "AGENTS.md").exists()
    meta = {"repo": str(repo), "mode": "branch" if a.branch else "full", "agents_md": agents}

    only = lines = new_files = None
    if a.branch:
        cur, base, err = detect_base(repo, a.base)
        meta.update({"branch": cur, "base": base})
        if err:
            meta["error"] = err
            print(f"ERROR: {err}")
            if a.json:
                Path(a.json).parent.mkdir(parents=True, exist_ok=True)
                Path(a.json).write_text(json.dumps({"meta": meta, "leads": []}, indent=2))
            sys.exit(2)
        ch = changed(repo, base)
        only, lines, new_files = set(ch["files"]), ch["lines"], set(ch["new_files"])
        meta.update({k: ch[k] for k in ("merge_base", "commits", "uncommitted", "files", "deleted", "new_files")})

    s = Scan(repo, only, lines, new_files)
    files = []
    for p in walk(repo):
        rel = p.relative_to(repo).as_posix()
        if p.suffix in CODE_EXT or p.suffix in (".css",):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if rel.startswith("src/") or p.parent == repo:
                files.append((rel, text))
        else:
            text = ""
        if rel.startswith("src/") or STRAY.search(p.name):
            scan_file(s, p, rel, text, agents)
    chains(s, [(r, t) for r, t in files if r.startswith("src/")])
    if not a.branch:
        unused(s, repo, [(r, t) for r, t in files if r.startswith("src/")])
        structure(s, repo, agents)
        if a.template:
            drift(s, repo, Path(a.template).resolve())

    order = {"fix-now": 0, "should-fix": 1, "tidy": 2, "info": 3}
    s.leads.sort(key=lambda l: (order[l["tier"]], l["rule"], l["file"], l["line"] or 0))
    counts = defaultdict(int)
    for l in s.leads:
        counts[l["tier"]] += 1
    meta["counts"] = dict(counts)

    hdr = f"mode={meta['mode']} agents_md={agents}"
    if a.branch:
        hdr += f" branch={meta['branch']} base={meta['base']} commits={meta['commits']} uncommitted={meta['uncommitted']} files={len(meta['files'])}"
    print(hdr)
    print("leads: " + ", ".join(f"{k}={counts.get(k, 0)}" for k in order))
    for tier in order:
        group = [l for l in s.leads if l["tier"] == tier]
        if not group:
            continue
        print(f"\n## {tier} ({len(group)})")
        for l in group[:60]:
            loc = f"{l['file']}:{l['line']}" if l["line"] else l["file"]
            print(f"- [{l['rule']}] {loc}: {l['message']} ({l['source']})")
        if len(group) > 60:
            print(f"- … {len(group) - 60} more in the JSON")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({"meta": meta, "leads": s.leads}, indent=2))


if __name__ == "__main__":
    main()
