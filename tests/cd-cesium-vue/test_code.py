"""Builds a small Vue-Cesium project with deliberate problems and checks scripts/cesium_scan.py."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

CLEAN_COMPOSABLE = """import { shallowRef, markRaw, onUnmounted } from 'vue'
import { Viewer } from 'cesium'

export function useMap(el: { value: HTMLElement | null }) {
  const viewer = shallowRef<Viewer | null>(null)
  function init() {
    if (el.value) viewer.value = markRaw(new Viewer(el.value))
  }
  onUnmounted(() => viewer.value?.destroy())
  return { viewer, init }
}
"""


def w(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def git(root, *args):
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        env={
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
            "PATH": os.environ["PATH"],
            "HOME": str(root),
        },
    )


def scan(skill, root, *extra):
    out = root.parent / f"scan-{len(extra)}-{'b' if '--branch' in extra else 'f'}.json"
    r = subprocess.run(
        [sys.executable, str(skill / "scripts/cesium_scan.py"), str(root), "--json", str(out), *extra],
        capture_output=True,
        text=True,
    )
    data = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"meta": {}, "leads": []}
    return r, data


def has(data, rule, file_part, tier=None):
    return any(
        ld["rule"] == rule and file_part in ld["file"] and (tier is None or ld["tier"] == tier)
        for ld in data["leads"]
    )


def run(skill, check):
    if not shutil.which("git"):
        print("SKIP cesium-vue: git not installed")
        return
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d) / "cesium-app"
        w(root, "package.json", '{"name":"cesium-app","dependencies":{"cesium":"^1.120.0","vue":"^3.5.0"}}')
        w(root, "vite.config.ts", "import { defineConfig } from 'vite'\nexport default defineConfig({})\n")
        w(root, "src/composables/useCleanMap.ts", CLEAN_COMPOSABLE)
        w(root, "src/composables/useLeakyMap.ts",
          "import { ref } from 'vue'\nimport { Viewer } from 'cesium'\n"
          "export const v = ref<Viewer | null>(null)\n"
          "export function boot(el: HTMLElement) { v.value = new Viewer(el) }\n")
        git(root, "init", "-q", "-b", "main")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "chore: base")
        git(root, "checkout", "-q", "-b", "develop")
        git(root, "checkout", "-q", "-b", "feature/globe")

        r, full = scan(skill, root)
        check(r.returncode == 0, "cesium-vue: full scan runs")
        check(has(full, "vite cesium config", "vite.config.ts", "high"), "cesium-vue: missing CESIUM_BASE_URL flagged")
        check(has(full, "deep reactivity", "useLeakyMap.ts", "high"), "cesium-vue: ref<Viewer> flagged as high")
        check(has(full, "missing destroy", "useLeakyMap.ts", "high"), "cesium-vue: new Viewer without destroy flagged")
        check(not has(full, "deep reactivity", "useCleanMap.ts"), "cesium-vue: shallowRef/markRaw not flagged")
        check(not has(full, "missing destroy", "useCleanMap.ts"), "cesium-vue: viewer.destroy() not flagged")

        w(root, "src/composables/useEvents.ts",
          "import { Ion, ScreenSpaceEventHandler } from 'cesium'\n"
          "Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9_fake_token_value'\n"
          "export function bind(canvas: HTMLCanvasElement) { return new ScreenSpaceEventHandler(canvas) }\n")
        r, br = scan(skill, root, "--branch")
        check(r.returncode == 0, "cesium-vue: branch scan runs")
        check(br["meta"].get("base") == "develop", "cesium-vue: feature branch compares against develop")
        check(has(br, "hardcoded ion token", "useEvents.ts", "high"), "cesium-vue: hardcoded Ion token flagged")
        check(has(br, "handler leak", "useEvents.ts", "high"), "cesium-vue: uncleaned ScreenSpaceEventHandler flagged")
        check(not has(br, "deep reactivity", "useLeakyMap.ts"), "cesium-vue: untouched file not reported in branch mode")
