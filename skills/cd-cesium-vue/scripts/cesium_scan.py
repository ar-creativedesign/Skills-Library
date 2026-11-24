#!/usr/bin/env python3
"""Lead finder for cd-cesium-vue. Standard-library Python only; read-only.

Full mode:    python cesium_scan.py <repo> --json out.json
Branch mode:  python cesium_scan.py <repo> --branch [--base auto|<branch>] --json out.json

Lead severities: high, medium, low, info (the reviewer confirms and may change them).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", "dist-ssr", ".git", "coverage", ".vite", "reports"}
CODE_EXT = {".vue", ".ts", ".tsx", ".js", ".mjs", ".cjs"}

DEEP_REF_VIEWER = re.compile(r"\b(?:ref|reactive)\s*(?:<[^>]*>)?\s*\([^)]*\b(?:new\s+(?:Cesium\.)?Viewer|Cesium3DTileset|GeoJsonDataSource|CustomDataSource)\b")
DEEP_REF_TYPE = re.compile(r"\bref\s*<\s*(?:Cesium\.)?(?:Viewer|Scene|Cesium3DTileset|DataSource|Entity)\b")
NEW_VIEWER = re.compile(r"\bnew\s+(?:Cesium\.)?Viewer\s*\(")
NEW_HANDLER = re.compile(r"\bnew\s+(?:Cesium\.)?ScreenSpaceEventHandler\s*\(")
RENDER_LISTENER = re.compile(r"\b(?:postRender|preRender|onTick|changed)\.addEventListener\s*\(")
ION_TOKEN_LITERAL = re.compile(r"""\bIon\.defaultAccessToken\s*=\s*['"][A-Za-z0-9._-]{20,}['"]""")
DESTROY_CALL = re.compile(r"\.destroy\s*\(")
REMOVE_LISTENER = re.compile(r"\.removeEventListener\s*\(|(?:const|let)\s+\w+\s*=\s*[^;\n]*\.addEventListener\s*\(")


def sh(args, cwd):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout


def walk(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(fns):
            yield Path(dp) / f


def ref_exists(repo, ref):
    return sh(["git", "rev-parse", "--verify", "--quiet", ref + "^{commit}"], repo)[0] == 0


def current_branch(repo):
    rc, out = sh(["git", "symbolic-ref", "--short", "HEAD"], repo)
    return out.strip() if rc == 0 else None


def detect_base(repo, branch):
    if branch in ("main", "master"):
        return None, "On main/master; run a full project review instead."
    candidates = ("main", "master") if branch in ("develop", "staging") else ("develop", "staging", "main", "master")
    for c in candidates:
        if ref_exists(repo, c):
            return c, None
    for c in candidates:
        if ref_exists(repo, f"origin/{c}"):
            return f"origin/{c}", None
    return None, "Could not detect base branch; pass --base <branch>."


def parse_diff_hunks(diff_text):
    changed = {}
    cur_file = None
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            cur_file = line[6:]
            changed.setdefault(cur_file, set())
        elif line.startswith("@@ ") and cur_file is not None:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) is not None else 1
                if count > 0:
                    changed[cur_file].update(range(start, start + count))
    return changed


def branch_changes(repo, base_arg):
    branch = current_branch(repo) or "HEAD"
    if base_arg == "auto":
        base, err = detect_base(repo, branch)
        if err:
            return None, {"error": err, "branch": branch}
    else:
        base = base_arg
        if not ref_exists(repo, base):
            return None, {"error": f"Base branch '{base}' not found.", "branch": branch}

    rc, mb = sh(["git", "merge-base", base, "HEAD"], repo)
    if rc != 0:
        return None, {"error": f"No merge-base between {base} and HEAD.", "branch": branch, "base": base}
    merge_base = mb.strip()

    _, commit_cnt = sh(["git", "rev-list", "--count", f"{merge_base}..HEAD"], repo)
    _, diff_committed = sh(["git", "diff", "-U0", f"{merge_base}..HEAD"], repo)
    _, diff_staged = sh(["git", "diff", "--cached", "-U0"], repo)
    _, diff_unstaged = sh(["git", "diff", "-U0"], repo)
    _, untracked_out = sh(["git", "ls-files", "--others", "--exclude-standard"], repo)
    _, status_out = sh(["git", "status", "--porcelain"], repo)

    line_map = {}
    for d in (diff_committed, diff_staged, diff_unstaged):
        for rel, lines in parse_diff_hunks(d).items():
            line_map.setdefault(rel, set()).update(lines)

    for rel in [p.strip() for p in untracked_out.splitlines() if p.strip()]:
        fp = repo / rel
        if fp.is_file():
            try:
                cnt = len(fp.read_text(encoding="utf-8", errors="replace").splitlines())
            except OSError:
                cnt = 0
            line_map[rel] = set(range(1, cnt + 1))

    meta = {
        "mode": "branch",
        "branch": branch,
        "base": base,
        "merge_base": merge_base[:12],
        "commits": int(commit_cnt.strip() or 0),
        "uncommitted": len([l for l in status_out.splitlines() if l.strip()]),
        "changed_files": sorted(line_map.keys()),
    }
    return line_map, meta


def lead(leads, rule, tier, rel, line, detail):
    leads.append({
        "rule": rule,
        "tier": tier,
        "file": rel,
        "line": line,
        "detail": detail,
    })


def scan_code_file(path, rel, leads):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    lines = text.splitlines()
    has_destroy = bool(DESTROY_CALL.search(text))
    has_remove_listener = bool(REMOVE_LISTENER.search(text))

    for idx, ln in enumerate(lines, 1):
        if DEEP_REF_VIEWER.search(ln) or DEEP_REF_TYPE.search(ln):
            if "shallowRef" not in ln and "markRaw" not in ln:
                lead(leads, "deep reactivity", "high", rel, idx, "Cesium object wrapped in deep Vue ref/reactive; use shallowRef/markRaw")
        if ION_TOKEN_LITERAL.search(ln):
            lead(leads, "hardcoded ion token", "high", rel, idx, "literal Ion.defaultAccessToken; move to import.meta.env")
        if NEW_VIEWER.search(ln) and not has_destroy:
            lead(leads, "missing destroy", "high", rel, idx, "new Viewer() without .destroy() in this file")
        if NEW_HANDLER.search(ln) and not has_destroy:
            lead(leads, "handler leak", "high", rel, idx, "new ScreenSpaceEventHandler() without .destroy() in this file")
        if RENDER_LISTENER.search(ln) and not has_remove_listener:
            lead(leads, "listener leak", "medium", rel, idx, "render/tick listener added without stored remover or removeEventListener()")


def check_vite_cesium(repo, leads):
    pkg = repo / "package.json"
    if not pkg.exists():
        return
    try:
        pkg_text = pkg.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    if '"cesium"' not in pkg_text:
        return
    for name in ("vite.config.ts", "vite.config.js", "vite.config.mts", "vite.config.mjs"):
        vp = repo / name
        if vp.exists():
            txt = vp.read_text(encoding="utf-8", errors="replace")
            if "CESIUM_BASE_URL" not in txt and "cesium" not in txt.lower():
                lead(leads, "vite cesium config", "high", name, 1, "raw `cesium` dependency without CESIUM_BASE_URL or Vite Cesium plugin")
            break


def main():
    ap = argparse.ArgumentParser(description="Lead finder for cd-cesium-vue")
    ap.add_argument("repo", help="Path to Vue-Cesium repository")
    ap.add_argument("--json", required=True, help="Output JSON path")
    ap.add_argument("--branch", action="store_true", help="Branch diff mode")
    ap.add_argument("--base", default="auto", help="Base branch for --branch mode")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    out_path = Path(args.json)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.branch:
        line_map, meta = branch_changes(repo, args.base)
        if line_map is None:
            out_path.write_text(json.dumps({"meta": meta, "leads": []}, indent=2), encoding="utf-8")
            sys.exit(2)
    else:
        line_map = None
        meta = {"mode": "full"}

    leads = []
    if not args.branch:
        check_vite_cesium(repo, leads)

    for p in walk(repo):
        if p.suffix not in CODE_EXT:
            continue
        rel = p.relative_to(repo).as_posix()
        if line_map is not None and rel not in line_map:
            continue
        file_leads = []
        scan_code_file(p, rel, file_leads)
        if line_map is not None:
            changed_lines = line_map[rel]
            file_leads = [ld for ld in file_leads if ld["line"] in changed_lines]
        leads.extend(file_leads)

    out_path.write_text(json.dumps({"meta": meta, "leads": leads}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
