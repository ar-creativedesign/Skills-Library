#!/usr/bin/env python3
"""Static review of an Unreal Engine project folder: .uproject, config, version control, Content structure/naming and C++ code.

Read-only. Doesn't open the editor, cook or build. Blueprints and .uasset contents are binary and not inspected.
Produces LEADS to confirm in context.

    python project_scan.py <unreal-project-root> [--json out.json] [--max-per-rule 25] [--no-git]

Standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SKIP_DIRS = {"Binaries", "Intermediate", "Saved", "DerivedDataCache", ".git", ".vs", ".idea", ".vscode", "Build"}
SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
# Common prefixes from the widely used UE style guide (Allar) and Epic's conventions; extend in the checklist.
KNOWN_PREFIXES = ("BP_", "B_", "BPI_", "BPC_", "ABP_", "AM_", "AS_", "A_", "AN_", "AO_", "BS_", "BT_", "BB_", "SK_", "SKM_", "SKEL_", "SM_", "S_",
                  "M_", "MI_", "MF_", "MPC_", "MM_", "PM_", "T_", "TC_", "RT_", "HDR_", "WBP_", "W_", "UI_", "NS_", "NE_", "NP_", "P_", "PS_",
                  "SC_", "SCUE_", "SW_", "SA_", "MS_", "MSS_", "DA_", "DT_", "E_", "F_", "ST_", "CT_", "C_", "CA_", "CU_", "L_", "LS_", "LSA_",
                  "MAP_", "LV_", "PHYS_", "PHYSMAT_", "PP_", "FX_", "CR_", "IK_", "RTG_", "IMC_", "IA_", "Font_", "Media_", "MT_", "SB_", "EUW_", "EUB_",
                  "GA_", "GE_", "GC_", "BTT_", "BTS_", "BTD_", "EQS_", "CR_", "LUT_", "VDB_", "HLOD_", "WP_", "PCG_", "LVL_", "Map_")
LARGE_FILE = 100e6


class Report:
    def __init__(self, root, cap):
        self.root, self.cap, self.rules, self.facts = root, cap, {}, {}

    def add(self, rule, area, sev, desc, file="(project)", line=0, detail=""):
        r = self.rules.setdefault(rule, {"rule": rule, "area": area, "severity_hint": sev, "description": desc, "count": 0, "hits": []})
        r["count"] += 1
        if len(r["hits"]) < self.cap:
            rel = os.path.relpath(file, self.root).replace("\\", "/") if os.path.isabs(file) else file
            r["hits"].append({"file": rel, "line": line, "detail": detail[:160]})


def parse_json_relaxed(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    pattern = r'("(?:\\.|[^"\\])*")|//.*?$|/\*.*?\*/'
    cleaned = re.sub(pattern, lambda m: m.group(1) if m.group(1) else "", text, flags=re.MULTILINE | re.DOTALL)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return json.loads(cleaned)


def read(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except OSError:
        return ""


def ini_values(text):
    """Very small UE .ini reader: returns {(section, key): [values...]} keeping +/- array entries."""
    out, section = {}, ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        m = re.match(r"([+\-.!]?)([^=]+)=(.*)", line)
        if m:
            out.setdefault((section, m.group(2).strip()), []).append(m.group(3).strip())
    return out


def body_after(text, start):
    i = text.find("{", start)
    if i < 0:
        return ""
    depth = 0
    for j in range(i, min(len(text), i + 40000)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    return ""


def git_lines(root, *args):
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=120)
        return r.stdout.splitlines() if r.returncode == 0 else None
    except Exception:
        return None


def scan(root, cap=25, use_git=True):
    R = Report(root, cap)
    uprojects = [f for f in os.listdir(root) if f.endswith(".uproject")] if os.path.isdir(root) else []
    if not uprojects:
        R.add("NOT_AN_UNREAL_PROJECT", "Setup", "Critical", "No .uproject in this folder: point the scanner at the Unreal project root")
        return finish(R)
    up_path = os.path.join(root, uprojects[0])
    try:
        up = parse_json_relaxed(read(up_path))
    except Exception:
        up = {}
        R.add("UPROJECT_UNREADABLE", "Setup", "High", ".uproject is not valid JSON", up_path)
    eng = up.get("EngineAssociation", "unknown")
    R.facts.update({"project": uprojects[0], "engine": eng if not re.fullmatch(r"\{?[0-9A-Fa-f-]{36}\}?", eng) else f"source build ({eng})",
                    "modules": [m.get("Name") for m in up.get("Modules", [])],
                    "plugins_enabled": [p.get("Name") for p in up.get("Plugins", []) if p.get("Enabled", True)],
                    "plugins_disabled_count": sum(1 for p in up.get("Plugins", []) if p.get("Enabled") is False)})
    if not eng or eng == "unknown":
        R.add("NO_ENGINE_ASSOCIATION", "Setup", "Medium", "EngineAssociation empty: the team may open it with different engine versions", up_path)
    proj_plugins = os.path.join(root, "Plugins")
    if os.path.isdir(proj_plugins):
        R.facts["project_plugins"] = sorted(os.listdir(proj_plugins))

    # ---- Config
    cfg = os.path.join(root, "Config")
    eng_ini = ini_values(read(os.path.join(cfg, "DefaultEngine.ini")))
    game_ini = ini_values(read(os.path.join(cfg, "DefaultGame.ini")))
    if not eng_ini:
        R.add("NO_DEFAULT_ENGINE_INI", "Setup", "Medium", "Config/DefaultEngine.ini missing or empty")

    def first(d, key):
        for (s, k), v in d.items():
            if k == key:
                return v[-1]
        return None
    R.facts.update({"game_default_map": first(eng_ini, "GameDefaultMap"), "editor_startup_map": first(eng_ini, "EditorStartupMap"),
                    "project_version": first(game_ini, "ProjectVersion"), "build_configuration": first(game_ini, "BuildConfiguration"),
                    "lumen_gi": first(eng_ini, "r.DynamicGlobalIlluminationMethod"), "virtual_shadow_maps": first(eng_ini, "r.Shadow.Virtual.Enable"),
                    "ray_tracing": first(eng_ini, "r.RayTracing") or first(eng_ini, "r.SkinCache.CompileShaders")})
    for key in ("GameDefaultMap", "EditorStartupMap"):
        v = first(eng_ini, key)
        if v and v.startswith("/Game/"):
            path = os.path.join(root, "Content", v[len("/Game/"):].split(".")[0] + ".umap")
            if not os.path.exists(path):
                R.add("DEFAULT_MAP_MISSING", "Build settings", "High", f"{key} points at a map that doesn't exist", "Config/DefaultEngine.ini", 0, v)
    if (first(game_ini, "IncludeDebugFiles") or "").lower() == "true":
        R.add("PACKAGE_DEBUG_FILES", "Build settings", "Low", "Packaging includes debug files (bigger builds; usually only for internal builds)", "Config/DefaultGame.ini")
    if (first(game_ini, "bCookAll") or "").lower() == "true":
        R.add("COOK_ALL", "Build settings", "Medium", "Cook everything in Content (bloats builds; list maps/directories to cook instead)", "Config/DefaultGame.ini")
    if not any(k == "+MapsToCook" or k.endswith("MapsToCook") for (_, k) in game_ini) and os.path.isdir(os.path.join(root, "Content")):
        R.add("NO_MAPS_TO_COOK", "Build settings", "Info", "No explicit MapsToCook list (cook relies on defaults; confirm what ships)", "Config/DefaultGame.ini")

    # ---- Version control
    gi = read(os.path.join(root, ".gitignore"))
    if not gi:
        R.add("NO_GITIGNORE", "Version control", "High", "No .gitignore at the project root (use the standard Unreal one)")
    else:
        for folder in ("Binaries", "Intermediate", "Saved", "DerivedDataCache"):
            if folder.lower() not in gi.lower():
                R.add("GITIGNORE_GAP", "Version control", "Medium", "Generated folder not ignored", ".gitignore", 0, folder)
    ga = read(os.path.join(root, ".gitattributes"))
    lfs = re.findall(r"(?m)^\s*(\S+)\s+.*filter=lfs", ga)
    R.facts["lfs_patterns"] = len(lfs)
    if not any(p.endswith((".uasset", ".umap")) for p in lfs):
        R.add("NO_LFS_FOR_UASSETS", "Version control", "High", "Git LFS isn't tracking *.uasset/*.umap: binary assets bloat the repo and can't be merged (also consider LFS file locking)")
    elif "lockable" not in ga:
        R.add("NO_LFS_LOCKING", "Version control", "Low", "LFS patterns for .uasset/.umap aren't marked lockable (binary assets can't be merged; locking prevents lost work)", ".gitattributes")
    tracked = git_lines(root, "ls-files") if use_git and os.path.isdir(os.path.join(root, ".git")) else None
    if tracked is not None:
        for gen in ("Binaries/", "Intermediate/", "Saved/", "DerivedDataCache/"):
            n = sum(1 for f in tracked if f.startswith(gen))
            if n:
                R.add("GENERATED_FOLDER_COMMITTED", "Version control", "Critical", "Generated folder committed to git", gen, 0, f"{n} files")

    # ---- Content
    content = os.path.join(root, "Content")
    assets = []
    for d, ds, fs in os.walk(content):
        ds[:] = [x for x in ds if x not in SKIP_DIRS]
        for f in fs:
            if f.endswith((".uasset", ".umap")):
                assets.append(os.path.join(d, f))
    R.facts.update({"assets": len(assets), "maps": sum(1 for a in assets if a.endswith(".umap"))})
    if os.path.isdir(content):
        top = os.listdir(content)
        loose = [x for x in top if x.endswith((".uasset", ".umap"))]
        if len(loose) > 5:
            R.add("CONTENT_ROOT_CLUTTER", "Structure", "Low", f"{len(loose)} assets directly in Content/ (group under a project folder, e.g. Content/<Game>/)", content, 0, ", ".join(loose[:8]))
        if "StarterContent" in top:
            R.add("STARTER_CONTENT", "Structure", "Low", "StarterContent still in the project (bloat; migrate what you use, delete the rest)", os.path.join(content, "StarterContent"))
        if "Developers" in top:
            R.add("DEVELOPERS_FOLDER", "Structure", "Info", "Content/Developers present: make sure it's excluded from cooking and not referenced by shipping content", os.path.join(content, "Developers"))
        if "Collections" in top:
            R.add("COLLECTIONS_FOLDER", "Structure", "Info", "Content/Collections present (check whether shared collections are intended to be committed)")
    unprefixed = 0
    for a in assets:
        b = os.path.basename(a)
        if re.search(r"[^\w\-.]", b):
            R.add("NAME_SPACES_OR_SYMBOLS", "Structure", "Medium", "Spaces or special characters in asset names (cooking, packaging and scripting problems)", a)
        if not b.startswith(KNOWN_PREFIXES) and not a.endswith(".umap"):
            unprefixed += 1
            if unprefixed <= cap:
                R.add("ASSET_WITHOUT_TYPE_PREFIX", "Structure", "Low", "Asset name without a recognised type prefix (BP_, SM_, T_, M_, MI_…)", a)
        try:
            sz = os.path.getsize(a)
        except OSError:
            sz = 0
        if sz > LARGE_FILE and not any(p.endswith(os.path.splitext(a)[1]) for p in lfs):
            R.add("FILE_OVER_100MB_NOT_LFS", "Version control", "High", "Asset over 100 MB not covered by LFS (GitHub rejects it)", a, 0, f"{sz / 1e6:.0f} MB")
        elif sz > 200e6:
            R.add("VERY_LARGE_ASSET", "Assets", "Medium", "Very large asset (check source resolution, embedded data, or World Partition for maps)", a, 0, f"{sz / 1e6:.0f} MB")
    if assets:
        R.facts["assets_with_type_prefix_pct"] = round(100 * (1 - unprefixed / max(1, sum(1 for a in assets if not a.endswith('.umap')))))

    # ---- Source / C++
    src = os.path.join(root, "Source")
    cpp = []
    for d, ds, fs in os.walk(src):
        ds[:] = [x for x in ds if x not in SKIP_DIRS]
        for f in fs:
            if f.endswith((".h", ".hpp", ".cpp", ".inl", ".cs")):
                cpp.append(os.path.join(d, f))
    headers = [f for f in cpp if f.endswith((".h", ".hpp"))]
    sources = [f for f in cpp if f.endswith(".cpp")]
    build_cs = [f for f in cpp if f.endswith(".Build.cs")]
    R.facts.update({"cpp_headers": len(headers), "cpp_sources": len(sources), "build_cs": len(build_cs), "blueprint_only": not sources})
    if not sources:
        R.add("BLUEPRINT_ONLY", "Code", "Info", "No C++ source: logic lives in Blueprints, which this static review can't read (use the editor tools listed in the checklist)")
    total, todo, tick_on = 0, 0, 0
    tests = sum(1 for f in cpp if re.search(r"(?i)tests?/|Test\.cpp$|Spec\.cpp$", f.replace("\\", "/")))
    R.facts["test_files"] = tests
    if sources and tests == 0:
        R.add("NO_AUTOMATION_TESTS", "Code", "Low", "No automation/spec tests found (Automation Test Framework / Functional Tests)")
    for f in cpp:
        t = read(f)
        lines = t.count("\n") + 1
        total += lines
        todo += len(re.findall(r"//\s*(TODO|FIXME|HACK)", t))
        if lines > 1000:
            R.add("LARGE_SOURCE_FILE", "Code", "Medium", "Source file over 1000 lines (split responsibilities)", f, 0, f"{lines} lines")
        if f.endswith((".h", ".hpp")):
            for m in re.finditer(r'#include\s+"(Engine\.h|EngineMinimal\.h)"', t):
                R.add("HEAVY_INCLUDE_IN_HEADER", "Code", "Low", "Monolithic engine header included (slow compiles; include what you use)", f, t.count("\n", 0, m.start()) + 1, m.group(1))
            if re.search(r"\bU(CLASS|STRUCT)\s*\(", t):
                lines_list = t.splitlines()
                for i, ln in enumerate(lines_list):
                    if re.match(r"\s*(class\s+)?[UA][A-Z]\w*\s*\*\s*\w+\s*(=\s*nullptr\s*)?;", ln):
                        prev = next((lines_list[j].strip() for j in range(i - 1, max(-1, i - 4), -1) if lines_list[j].strip()), "")
                        if not prev.startswith("UPROPERTY"):
                            R.add("RAW_UOBJECT_POINTER", "Code", "High", "UObject pointer member without UPROPERTY (garbage collector can't see it; dangling pointer risk). Use UPROPERTY + TObjectPtr, or TWeakObjectPtr", f, i + 1, ln.strip())
        for m in re.finditer(r"PrimaryActorTick\.bCanEverTick\s*=\s*true|PrimaryComponentTick\.bCanEverTick\s*=\s*true", t):
            tick_on += 1
        for m in re.finditer(r"::Tick(Component)?\s*\(", t):
            body = body_after(t, m.end())
            for pat, what in [(r"GetAllActorsOf|TActorIterator|UGameplayStatics::GetActorOfClass", "actor search"),
                              (r"FindComponentByClass|GetComponents\s*\(|GetComponentByClass", "component lookup"),
                              (r"LoadObject|StaticLoadObject|LoadSynchronous|TryLoad\(", "synchronous load"),
                              (r"SpawnActor|NewObject\s*<", "spawning/allocation"), (r"FindObject\s*<", "FindObject")]:
                if re.search(pat, body):
                    R.add("EXPENSIVE_IN_TICK", "Code", "Medium", "Tick does expensive work (cache, use events/timers, or move off Tick)", f, t.count("\n", 0, m.start()) + 1, what)
        for m in re.finditer(r'TEXT\(\s*"/Game/[^"]+"\s*\)', t):
            R.add("HARDCODED_ASSET_PATH", "Code", "Low", "Hard-coded asset path in C++ (breaks on rename; use soft references, data assets or settings)", f, t.count("\n", 0, m.start()) + 1, m.group(0))
        for m in re.finditer(r"ConstructorHelpers::FObjectFinder", t):
            R.add("CONSTRUCTOR_HARD_REFERENCE", "Code", "Low", "ConstructorHelpers::FObjectFinder creates hard references loaded with the class (prefer soft refs / Blueprint defaults)", f, t.count("\n", 0, m.start()) + 1)
        for m in re.finditer(r"GEngine\s*->\s*AddOnScreenDebugMessage", t):
            before = t[:m.start()]
            if before.count("#if !UE_BUILD_SHIPPING") <= before.count("#endif") and "WITH_EDITOR" not in before[-300:]:
                R.add("DEBUG_MESSAGE_IN_SHIPPING", "Code", "Low", "On-screen debug message not compiled out of Shipping builds", f, t.count("\n", 0, m.start()) + 1)
    R.facts.update({"cpp_lines": total, "todo_fixme_hack": todo, "tick_enabled_classes": tick_on})
    if tick_on >= 10:
        R.add("MANY_TICKING_CLASSES", "Code", "Medium", f"{tick_on} classes enable Tick (prefer events/timers; disable Tick by default)")
    return finish(R)


def finish(R):
    results = sorted(R.rules.values(), key=lambda r: (SEV_ORDER[r["severity_hint"]], -r["count"]))
    return {"root": os.path.abspath(R.root), "facts": R.facts, "results": results,
            "note": "Leads only: confirm each in context. Blueprints, .uasset contents, materials, shaders and runtime performance aren't inspected."}


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
