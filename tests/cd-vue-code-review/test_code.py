"""Builds a small Vue project with deliberate problems and checks scripts/vue_scan.py.

Full mode: the planted issues are found in the right tier.
Branch mode: base auto-detects develop for a feature branch; only issues on added/changed lines
(committed, staged, unstaged or untracked) are reported, and issues already on develop are not.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

AGENTS = "# Rules\n- Stores `*.store.ts`, services `*.service.ts`. No console.log. Prefer ref().\n"

OLD_VIEW = """<template>
  <div class="ml-4 text-left">Home</div>
</template>

<script setup lang="ts">
const x = 1
</script>
"""

STORE = """import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', {
  state: () => ({ items: [] as string[] }),
})
"""

LOGGER = "export const logger = { info: (m: string) => console.info(m) }\n"


def w(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@example.com", "PATH": __import__("os").environ["PATH"], "HOME": str(root)})


def scan(skill, root, *extra):
    out = root.parent / f"scan-{len(extra)}-{'b' if '--branch' in extra else 'f'}.json"
    r = subprocess.run([sys.executable, str(skill / "scripts/vue_scan.py"), str(root), "--json", str(out), *extra],
                       capture_output=True, text=True)
    data = json.loads(out.read_text()) if out.exists() else {"meta": {}, "leads": []}
    return r, data


def has(data, rule, file_part, tier=None):
    return any(l["rule"] == rule and file_part in l["file"] and (tier is None or l["tier"] == tier) for l in data["leads"])


def run(skill, check):
    if not shutil.which("git"):
        print("SKIP vue-review: git not installed")
        return
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d) / "app"
        w(root, "AGENTS.md", AGENTS)
        w(root, "package.json", '{"name":"app","scripts":{"dev":"vite"}}')
        w(root, "src/main.ts", "import App from './App.vue'\n")
        w(root, "src/App.vue", "<template><RouterView /></template>\n<script setup lang=\"ts\"></script>\n")
        w(root, "src/utils/logger.ts", LOGGER)
        w(root, "src/views/HomeView.vue", OLD_VIEW)
        w(root, "src/stores/cart.store.ts", STORE)
        w(root, "src/router/index.ts", "import HomeView from '@/views/HomeView.vue'\nexport const routes = [{ path: '/', component: HomeView }]\n")
        w(root, "src/stores/useCart.store.ts.bak", "old\n")
        git(root, "init", "-q", "-b", "main")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "chore: base")
        git(root, "checkout", "-q", "-b", "develop")
        git(root, "checkout", "-q", "-b", "feature/profile")

        # ---- full mode on the base project
        r, full = scan(skill, root)
        check(r.returncode == 0, "vue-review: full scan runs")
        check(has(full, "logical properties (RTL)", "HomeView.vue"), "vue-review: physical Tailwind utilities flagged")
        check(has(full, "setup stores", "cart.store.ts"), "vue-review: options-style Pinia store flagged")
        check(has(full, "lazy routes", "router/index.ts"), "vue-review: static view import in router flagged")
        check(has(full, "stray file", ".bak", "tidy"), "vue-review: stray .bak file flagged as tidy-up")
        check(has(full, "tests", "."), "vue-review: missing tests noted")
        check(not has(full, "logging", "logger.ts"), "vue-review: logger itself not flagged for console")

        # ---- branch changes: one committed, one unstaged edit, one untracked file
        w(root, "src/services/user.service.ts", "/** Loads the user. */\nexport async function getUser() {\n  return fetch('/api/user')\n}\n")
        w(root, "src/components/UserCard.vue",
          "<template>\n  <li v-for=\"u in users\">{{ u }}</li>\n</template>\n\n<script setup lang=\"ts\">\n"
          "const props = defineProps<{ users: any[] }>()\nfetch('/api/x')\n</script>\n")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "feat: user card")
        (root / "src/views/HomeView.vue").write_text(OLD_VIEW.replace("const x = 1", "const x = 1\nconsole.log(x)"))
        w(root, "src/views/ProfileView.vue", "<template>\n  <p>hi</p>\n</template>\n\n<script setup lang=\"ts\">\ntry { go() } catch (e) {}\n</script>\n")

        r, br = scan(skill, root, "--branch")
        m = br["meta"]
        check(r.returncode == 0, "vue-review: branch scan runs")
        check(m.get("base") == "develop", f"vue-review: feature branch compares against develop (got {m.get('base')})")
        check(m.get("commits") == 1 and m.get("uncommitted", 0) >= 2, "vue-review: counts commits and uncommitted changes")
        check(has(br, "v-for key", "UserCard.vue", "fix-now"), "vue-review: committed change: v-for without key is fix-now")
        check(has(br, "no any", "UserCard.vue", "fix-now"), "vue-review: committed change: `any` is fix-now")
        check(has(br, "API calls in services", "UserCard.vue", "fix-now"), "vue-review: network call in a component is fix-now")
        check(not has(br, "API calls in services", "user.service.ts"), "vue-review: network call in a service is fine")
        check(has(br, "logging", "HomeView.vue"), "vue-review: unstaged edit: new console.log flagged")
        check(has(br, "no silent failure", "ProfileView.vue", "fix-now"), "vue-review: untracked file: empty catch flagged")
        check(not has(br, "logical properties (RTL)", "HomeView.vue"), "vue-review: old issue on unchanged line not reported")
        check(not has(br, "setup stores", "cart.store.ts"), "vue-review: untouched file not reported")
        w(root, "src/views/ProfileView.old.vue", "<script>\nconsole.log(1)\n</script>\n")
        r, br2 = scan(skill, root, "--branch", "--base", "develop")
        old = [l for l in br2["leads"] if l["file"].endswith("ProfileView.old.vue")]
        check(len(old) == 1 and old[0]["rule"] == "stray file", "vue-review: a stray copy is one tidy-up, not re-linted")
        (root / "src/views/ProfileView.old.vue").unlink()

        # ---- develop compares against main; main itself refuses branch mode
        git(root, "stash", "-u", "-q")
        git(root, "checkout", "-q", "develop")
        r, dv = scan(skill, root, "--branch")
        check(dv["meta"].get("base") == "main", "vue-review: develop compares against main")
        git(root, "checkout", "-q", "main")
        r, mn = scan(skill, root, "--branch")
        check(r.returncode == 2 and "full project" in mn["meta"].get("error", ""), "vue-review: on main, branch mode says to run a full review")
