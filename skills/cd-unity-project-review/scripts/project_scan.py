#!/usr/bin/env python3
"""Static review of a Unity project folder: setup, version control, structure, asset import settings and C# code.

Read-only. Doesn't open Unity or build anything. Produces LEADS to confirm in context.

    python project_scan.py <unity-project-root> [--json out.json] [--max-per-rule 25] [--no-git]

Standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SKIP_DIRS = {"Library", "Temp", "Obj", "obj", "Logs", "UserSettings", "Build", "Builds", ".git", ".vs", ".idea", "MemoryCaptures", "Recordings"}
KNOWN_LTS = ("2019.4", "2020.3", "2021.3", "2022.3", "6000.0", "6000.3")  # verify against Unity's release list
BINARY_EXT = (".psd", ".tif", ".tiff", ".png", ".jpg", ".jpeg", ".tga", ".exr", ".hdr", ".fbx", ".obj", ".blend", ".max", ".ma", ".mb",
              ".wav", ".mp3", ".ogg", ".aif", ".aiff", ".mp4", ".mov", ".webm", ".ttf", ".otf", ".unitypackage", ".zip", ".dll", ".so", ".a", ".bank")
SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}


class Report:
    def __init__(self, root, cap):
        self.root, self.cap, self.rules, self.facts = root, cap, {}, {}

    def add(self, rule, area, sev, desc, file="(project)", line=0, detail=""):
        r = self.rules.setdefault(rule, {"rule": rule, "area": area, "severity_hint": sev, "description": desc, "count": 0, "hits": []})
        r["count"] += 1
        if len(r["hits"]) < self.cap:
            rel = os.path.relpath(file, self.root).replace("\\", "/") if os.path.isabs(file) else file
            r["hits"].append({"file": rel, "line": line, "detail": detail[:160]})


def read(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except OSError:
        return ""


def yaml_val(text, key):
    m = re.search(rf"(?m)^\s*{re.escape(key)}:\s*(.*)$", text)
    return m.group(1).strip() if m else None


def git_lines(root, *args):
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=120)
        return r.stdout.splitlines() if r.returncode == 0 else None
    except Exception:
        return None


def body_after(text, start):
    """Return the brace-balanced body starting at the first '{' at/after start."""
    i = text.find("{", start)
    if i < 0:
        return ""
    depth = 0
    for j in range(i, min(len(text), i + 20000)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    return text[i + 1:i + 20000]


def scan(root, cap=25, use_git=True):
    R = Report(root, cap)
    ps = os.path.join(root, "ProjectSettings")
    assets = os.path.join(root, "Assets")
    if not os.path.isdir(assets) or not os.path.isdir(ps):
        R.add("NOT_A_UNITY_PROJECT", "Setup", "Critical", "Assets/ and ProjectSettings/ not found: point the scanner at the Unity project root")
        return finish(R)

    # ---- Setup: version, packages, settings
    ver = yaml_val(read(os.path.join(ps, "ProjectVersion.txt")), "m_EditorVersion") or "unknown"
    R.facts["unity_version"] = ver
    if ver != "unknown" and not ver.startswith(KNOWN_LTS):
        R.add("NON_LTS_EDITOR", "Setup", "Info", f"Editor {ver} isn't in the known LTS list {KNOWN_LTS} (verify; LTS is usually preferred for production)")
    manifest = {}
    try:
        manifest = json.load(open(os.path.join(root, "Packages", "manifest.json"), encoding="utf-8")).get("dependencies", {})
    except Exception:
        R.add("NO_PACKAGE_MANIFEST", "Setup", "Medium", "Packages/manifest.json missing or unreadable")
    R.facts["packages"] = len(manifest)
    rp = "URP" if "com.unity.render-pipelines.universal" in manifest else "HDRP" if "com.unity.render-pipelines.high-definition" in manifest else "Built-in"
    R.facts["render_pipeline"] = rp
    if rp == "Built-in" and ver.startswith("6000"):
        R.add("BUILTIN_RP_ON_UNITY6", "Setup", "Low", "Built-in Render Pipeline on Unity 6: Unity's investment is in URP/HDRP; plan accordingly")
    for name, v in manifest.items():
        if re.search(r"-(pre|exp|preview)|preview", str(v)):
            R.add("PREVIEW_PACKAGE", "Setup", "Medium", "Pre-release/experimental package in use", "Packages/manifest.json", 0, f"{name}: {v}")
        if str(v).startswith(("http", "git", "ssh")) and "#" not in str(v):
            R.add("UNPINNED_GIT_PACKAGE", "Setup", "Medium", "Git package without a pinned tag/commit (#...): builds aren't reproducible", "Packages/manifest.json", 0, f"{name}: {v}")
        if str(v).startswith("file:") and ".." in str(v):
            R.add("LOCAL_PATH_PACKAGE", "Setup", "Low", "Package referenced from a path outside the project: other machines may not have it", "Packages/manifest.json", 0, f"{name}: {v}")
    if not os.path.exists(os.path.join(root, "Packages", "packages-lock.json")):
        R.add("NO_PACKAGES_LOCK", "Version control", "Low", "Packages/packages-lock.json not present (commit it for reproducible package resolution)")

    pset = read(os.path.join(ps, "ProjectSettings.asset"))
    if pset:
        cs = yaml_val(pset, "m_ActiveColorSpace")
        R.facts["color_space"] = {"0": "Gamma", "1": "Linear"}.get(cs, cs)
        if cs == "0":
            R.add("GAMMA_COLOR_SPACE", "Build settings", "Low", "Gamma colour space (Linear is the norm for modern PBR projects; check target platforms)")
        aih = yaml_val(pset, "activeInputHandler")
        R.facts["input_handling"] = {"0": "Input Manager (old)", "1": "Input System (new)", "2": "Both"}.get(aih, aih)
        if aih == "2":
            R.add("BOTH_INPUT_SYSTEMS", "Build settings", "Low", "Both old and new input handling enabled: pick one to avoid confusion and overhead")
        if yaml_val(pset, "gcIncremental") == "0":
            R.add("INCREMENTAL_GC_OFF", "Build settings", "Low", "Incremental GC disabled (can cause frame spikes)")
        sb = re.search(r"scriptingBackend:\s*\n((?:\s+\w+: \d+\n)+)", pset)
        if sb:
            R.facts["scripting_backend"] = {k: {"0": "Mono", "1": "IL2CPP"}.get(v, v) for k, v in re.findall(r"(\w+): (\d+)", sb.group(1))}
    eset = read(os.path.join(ps, "EditorSettings.asset"))
    ser = yaml_val(eset, "m_SerializationMode")
    R.facts["serialization"] = {"0": "Mixed", "1": "Force Binary", "2": "Force Text"}.get(ser, ser)
    if ser in ("0", "1"):
        R.add("NOT_FORCE_TEXT", "Version control", "High", "Asset serialization isn't Force Text: scenes/prefabs can't be diffed or merged")
    vcs = (yaml_val(eset, "m_ExternalVersionControlSupport") or "") + " " + (yaml_val(read(os.path.join(ps, "VersionControlSettings.asset")), "m_Mode") or "")
    if "Hidden" in vcs:
        R.add("HIDDEN_META_FILES", "Version control", "High", "Version control mode hides .meta files: they must be visible and committed")

    # ---- Version control
    gi = read(os.path.join(root, ".gitignore"))
    if not gi:
        R.add("NO_GITIGNORE", "Version control", "High", "No .gitignore at the project root (use the standard Unity one)")
    else:
        for folder in ("Library", "Temp", "Obj", "Logs", "UserSettings", "Build"):
            if not re.search(rf"(?im)^\s*/?\[?{folder[0]}.?{folder[0].lower()}?\]?{folder[1:]}/?|^\s*/?{folder}/?\s*$", gi) and folder.lower() not in gi.lower():
                R.add("GITIGNORE_GAP", "Version control", "Medium", "Generated folder not ignored", ".gitignore", 0, folder)
    ga = read(os.path.join(root, ".gitattributes"))
    lfs_patterns = re.findall(r"(?m)^\s*(\S+)\s+.*filter=lfs", ga)
    R.facts["lfs_patterns"] = len(lfs_patterns)
    if not lfs_patterns:
        R.add("NO_LFS", "Version control", "Medium", "No Git LFS patterns in .gitattributes for binary assets (textures, models, audio, video)")
    tracked = git_lines(root, "ls-files") if use_git and os.path.isdir(os.path.join(root, ".git")) else None
    if tracked is not None:
        for gen in ("Library/", "Temp/", "Obj/", "Logs/", "UserSettings/"):
            n = sum(1 for f in tracked if f.startswith(gen))
            if n:
                R.add("GENERATED_FOLDER_COMMITTED", "Version control", "Critical", "Generated folder committed to git (bloats repo, causes conflicts)", gen, 0, f"{n} files")

    # ---- Walk Assets
    files, dirs = [], []
    for d, ds, fs in os.walk(assets):
        ds[:] = [x for x in ds if x not in SKIP_DIRS and not x.startswith(".") and not x.endswith("~")]
        for x in ds:
            dirs.append(os.path.join(d, x))
        for f in fs:
            files.append(os.path.join(d, f))
    fileset = set(files)
    metas = [f for f in files if f.endswith(".meta")]
    real = [f for f in files if not f.endswith(".meta") and not os.path.basename(f).startswith(".")]
    R.facts.update({"asset_files": len(real), "folders": len(dirs)})
    for f in real + dirs:
        if f + ".meta" not in fileset:
            R.add("MISSING_META", "Version control", "High", "Asset/folder without a .meta file: references will break on other machines", f)
    for m in metas:
        target = m[:-5]
        if target not in fileset and not os.path.isdir(target):
            R.add("ORPHAN_META", "Version control", "Medium", ".meta file with no asset (leftover; delete it)", m)

    # Structure & naming
    root_loose = [f for f in real if os.path.dirname(f) == assets]
    if len(root_loose) > 5:
        R.add("ASSETS_ROOT_CLUTTER", "Structure", "Low", f"{len(root_loose)} loose files directly in Assets/ (group them into folders)", assets, 0, ", ".join(os.path.basename(x) for x in root_loose[:8]))
    flagged = []
    for p in sorted(dirs + real):
        b = os.path.basename(p)
        if " " in b or re.search(r"[^\w.\-() ]", b):
            parent = next((f for f in flagged if p.startswith(f + os.sep)), None)
            if parent:
                continue  # report the top-most offending folder only
            flagged.append(p)
            n = sum(1 for x in real if x.startswith(p + os.sep)) if os.path.isdir(p) else 0
            R.add("NAME_SPACES_OR_SYMBOLS", "Structure", "Low", "Spaces or special characters in asset/folder names (breaks scripts, CLI tools, addressable keys)", p, 0, f"{n} files inside" if n else "")
    res_size = 0
    for d in dirs:
        if os.path.basename(d) == "Resources":
            for dd, _, fs in os.walk(d):
                for f in fs:
                    if not f.endswith(".meta"):
                        try:
                            res_size += os.path.getsize(os.path.join(dd, f))
                        except OSError:
                            pass
            R.add("RESOURCES_FOLDER", "Assets", "Info", "Resources folder (everything inside ships in every build and loads an index at startup; prefer Addressables)", d)
    R.facts["resources_mb"] = round(res_size / 1e6, 1)
    if res_size > 50e6:
        R.add("RESOURCES_LARGE", "Assets", "Medium", f"Resources folders total {res_size / 1e6:.0f} MB (startup time and build size)")
    for f in real:
        try:
            sz = os.path.getsize(f)
        except OSError:
            continue
        rel = os.path.relpath(f, root).replace("\\", "/")
        in_lfs = any(re.fullmatch(pat.replace(".", r"\.").replace("*", ".*").lstrip("/"), os.path.basename(f)) or rel.endswith(pat.lstrip("*")) for pat in lfs_patterns)
        if sz > 100e6 and not in_lfs:
            R.add("FILE_OVER_100MB_NOT_LFS", "Version control", "High", "File over 100 MB not covered by LFS (GitHub rejects it)", f, 0, f"{sz / 1e6:.0f} MB")
        elif sz > 25e6 and f.lower().endswith(BINARY_EXT) and not in_lfs:
            R.add("LARGE_BINARY_NOT_LFS", "Version control", "Medium", "Large binary not covered by LFS", f, 0, f"{sz / 1e6:.0f} MB")

    # Scenes in build settings
    ebs = read(os.path.join(ps, "EditorBuildSettings.asset"))
    build_scenes = re.findall(r"enabled:\s*1\s*\n\s*path:\s*(\S+)(?:\s*\n\s*guid:\s*([0-9a-f]+))?", ebs)
    R.facts["scenes_in_build"] = len(build_scenes)
    R.facts["scenes_in_project"] = sum(1 for f in real if f.endswith(".unity"))
    scene_guids = {}
    for m in metas:
        if m.endswith(".unity.meta"):
            g = yaml_val(read(m), "guid")
            if g:
                scene_guids[g] = m[:-5]
    for sp, guid in build_scenes:
        if os.path.exists(os.path.join(root, sp)):
            continue
        if guid and guid in scene_guids:
            R.add("BUILD_SCENE_PATH_STALE", "Build settings", "Low", "Build Settings path is out of date but the scene is found by GUID (re-save Build Settings / Build Profile)",
                  "ProjectSettings/EditorBuildSettings.asset", 0, f"{sp} -> {os.path.relpath(scene_guids[guid], root)}")
        else:
            R.add("BUILD_SCENE_MISSING", "Build settings", "High", "Scene listed in Build Settings doesn't exist", "ProjectSettings/EditorBuildSettings.asset", 0, sp)

    # Import settings from .meta
    for m in metas:
        t = read(m)
        if "TextureImporter:" in t:
            if re.search(r"(?m)^\s*isReadable:\s*1", t):
                R.add("TEXTURE_READ_WRITE", "Assets", "Medium", "Texture Read/Write enabled (doubles memory; only needed for CPU access)", m)
            if re.search(r"(?m)^\s*textureType:\s*8", t) and re.search(r"(?m)^\s*enableMipMap:\s*1", t):
                R.add("SPRITE_MIPMAPS", "Assets", "Low", "Sprite/UI texture with mipmaps enabled (wasted memory for 2D/UI)", m)
            if re.search(r"(?m)^\s*textureCompression:\s*0", t):
                R.add("TEXTURE_UNCOMPRESSED", "Assets", "Low", "Texture set to uncompressed (check it's deliberate)", m)
            mts = [int(x) for x in re.findall(r"(?m)^\s*maxTextureSize:\s*(\d+)", t)]
            if mts and max(mts) >= 8192:
                R.add("TEXTURE_8K", "Assets", "Info", "Max texture size cap is 8192+ (only matters if the source is that large; check per-platform overrides)", m)
        elif "AudioImporter:" in t:
            src = m[:-5]
            try:
                big = os.path.getsize(src) > 3_000_000  # source size as a rough proxy for clip length
            except OSError:
                big = False
            if big and re.search(r"(?m)^\s*loadType:\s*0", t):
                R.add("AUDIO_LONG_DECOMPRESS_ON_LOAD", "Assets", "Medium", "Large audio clip set to Decompress On Load (use Streaming or Compressed In Memory for music/ambience)", m)
        elif "ModelImporter:" in t:
            if re.search(r"(?m)^\s*isReadable:\s*1", t):
                R.add("MESH_READ_WRITE", "Assets", "Low", "Mesh Read/Write enabled (extra memory; only needed for CPU mesh access)", m)

    # ---- Code
    cs_files = [f for f in real if f.endswith(".cs")]
    asmdefs = [f for f in real if f.endswith(".asmdef")]
    R.facts.update({"cs_files": len(cs_files), "asmdefs": len(asmdefs)})
    total_lines, todo = 0, 0
    tests = sum(1 for f in cs_files if re.search(r"(?i)/tests?/|\btests?\b.*\.cs$", f.replace("\\", "/")))
    R.facts["test_scripts"] = tests
    if len(cs_files) > 50 and not asmdefs:
        R.add("NO_ASMDEFS", "Code", "Medium", f"{len(cs_files)} scripts and no assembly definitions (slow iteration: every change recompiles everything)")
    if cs_files and tests == 0:
        R.add("NO_TESTS", "Code", "Low", "No test scripts found (Unity Test Framework edit/play mode tests)")
    for f in cs_files:
        t = read(f)
        lines = t.count("\n") + 1
        total_lines += lines
        rel = f.replace("\\", "/")
        in_editor_folder = "/Editor/" in rel
        todo += len(re.findall(r"//\s*(TODO|FIXME|HACK)", t))
        if lines > 600:
            R.add("LARGE_SCRIPT", "Code", "Medium", "Script over 600 lines (split responsibilities)", f, 0, f"{lines} lines")
        if re.search(r"(?m)^\s*using\s+UnityEditor", t) and not in_editor_folder:
            before = t[: re.search(r"(?m)^\s*using\s+UnityEditor", t).start()]
            if "#if UNITY_EDITOR" not in before:
                R.add("EDITOR_API_IN_RUNTIME", "Code", "Critical", "UnityEditor used outside an Editor folder without #if UNITY_EDITOR: player builds will fail", f)
        if "namespace " not in t and "MonoBehaviour" in t:
            R.add("NO_NAMESPACE", "Code", "Low", "Script without a namespace (name clashes with packages/assets)", f)
        for m in re.finditer(r"void\s+(Update|FixedUpdate|LateUpdate|OnGUI)\s*\(\s*\)", t):
            body = body_after(t, m.end())
            ln = t.count("\n", 0, m.start()) + 1
            if not body.strip():
                R.add("EMPTY_UNITY_CALLBACK", "Code", "Low", "Empty Unity callback (still called every frame; delete it)", f, ln, m.group(1))
                continue
            for pat, what in [(r"GetComponent(s|InChildren|InParent)?\s*[<(]", "GetComponent"), (r"GameObject\.Find|FindObjectOfType|FindObjectsOfType|FindFirstObjectByType|FindAnyObjectByType|FindWithTag|FindGameObjectsWithTag", "Find*"),
                              (r"\.(Where|Select|OrderBy|ToList|ToArray|Any|First)\s*\(", "LINQ"), (r"new\s+List<|new\s+Dictionary<|new\s+\w+\[\s*\w+\s*\]", "allocation"),
                              (r"Resources\.Load", "Resources.Load"), (r"\bInstantiate\s*\(|\bDestroy\s*\(", "Instantiate/Destroy (consider pooling)"), (r"SendMessage|BroadcastMessage", "SendMessage")]:
                if re.search(pat, body):
                    R.add("EXPENSIVE_IN_FRAME_LOOP", "Code", "Medium", "Per-frame callback does expensive work (cache references, pool, avoid allocations)", f, ln, f"{m.group(1)}: {what}")
        for m in re.finditer(r"void\s+(Start|Awake|OnEnable|OnDisable|OnDestroy)\s*\(\s*\)\s*\{\s*\}", t):
            R.add("EMPTY_UNITY_CALLBACK", "Code", "Low", "Empty Unity callback (delete it)", f, t.count("\n", 0, m.start()) + 1, m.group(1))
        for m in re.finditer(r"\basync\s+void\s+(\w+)", t):
            R.add("ASYNC_VOID", "Code", "Medium", "async void (exceptions are lost; use async Task / UniTask / Awaitable)", f, t.count("\n", 0, m.start()) + 1, m.group(1))
        for m in re.finditer(r"(StartCoroutine|Invoke|InvokeRepeating|CancelInvoke)\s*\(\s*\"", t):
            R.add("STRING_BASED_CALL", "Code", "Low", "String-based method call (not refactor-safe; use nameof or direct references)", f, t.count("\n", 0, m.start()) + 1, m.group(1))
        if "MonoBehaviour" in t or "ScriptableObject" in t:
            n = len(re.findall(r"(?m)^\s*public\s+(?!static|const|readonly|override|virtual|abstract|event|class|enum|struct|interface|void|async|delegate)[\w<>\[\],. ]+\s+\w+\s*(=[^;]*)?;", t))
            if n >= 5:
                R.add("MANY_PUBLIC_FIELDS", "Code", "Low", "Many public fields (prefer [SerializeField] private + read-only properties)", f, 0, f"{n} public fields")
        n_log = len(re.findall(r"Debug\.Log(Warning|Error)?\s*\(", t))
        if n_log >= 10:
            R.add("DEBUG_LOG_HEAVY", "Code", "Low", "Many Debug.Log calls (strip or wrap with a conditional logger for release builds)", f, 0, f"{n_log} calls")
    R.facts.update({"cs_lines": total_lines, "todo_fixme_hack": todo})
    return finish(R)


def finish(R):
    results = sorted(R.rules.values(), key=lambda r: (SEV_ORDER[r["severity_hint"]], -r["count"]))
    return {"root": os.path.abspath(R.root), "facts": R.facts, "results": results,
            "note": "Leads only: confirm each in context. The scanner can't see scene/prefab content, shader cost or runtime behaviour."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--json")
    ap.add_argument("--max-per-rule", type=int, default=25)
    ap.add_argument("--no-git", action="store_true")
    a = ap.parse_args()
    res = scan(a.root, a.max_per_rule, not a.no_git)
    if a.json:
        json.dump(res, open(a.json, "w", encoding="utf-8"), indent=1)
    print("Facts: " + json.dumps(res["facts"]))
    for r in res["results"]:
        print(f"\n[{r['severity_hint']}] {r['rule']} ({r['area']}): {r['description']} — {r['count']} hit(s)")
        for h in r["hits"][:5]:
            print(f"   {h['file']}{':' + str(h['line']) if h['line'] else ''}  {h['detail']}")
    print("\n" + res["note"])


if __name__ == "__main__":
    sys.exit(main())
