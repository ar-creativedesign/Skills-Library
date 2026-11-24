---
name: cd-cesium-vue
description: Build, configure, debug, or audit Vue 3 + TypeScript + Vite applications using CesiumJS or vue-cesium. Covers Vite asset bundling (CESIUM_BASE_URL, vite-plugin-static-copy), Ion/tile-server token security, non-reactive viewer/entity refs (shallowRef, markRaw), WebGL and event listener cleanup, render-loop performance (requestRenderMode, 3D Tiles LOD), and read-only codebase audits. Use when setting up Cesium in Vue, using vue-cesium, fixing Cesium performance/memory leaks, or reviewing a Vue-Cesium repo.
metadata:
  version: "1.0.0"
---

# Vue Cesium (CesiumJS / vue-cesium)

Build and audit Vue 3 + Vite + TypeScript applications that embed CesiumJS directly or via `vue-cesium`. Prevents the most common Vue-Cesium failure modes: Vue `Proxy` wrapping of `Cesium.Viewer` / `Entity` / `DataSource` instances, leaked WebGL contexts and `ScreenSpaceEventHandler`s, broken production asset paths (`CESIUM_BASE_URL`), hardcoded Ion tokens, and unthrottled frame-loop allocations.

Files in this skill (paths relative to this folder):

| File | Use it for |
| --- | --- |
| `references/cesium-patterns.md` | Vite setup, `shallowRef`/`markRaw` rules, cleanup patterns, `vue-cesium` vs raw `cesium` guidance, and audit severity checklist. Read before building or auditing. |
| `scripts/cesium_scan.py` | Lead finder, standard-library Python. Full: `python scripts/cesium_scan.py <repo> --json <file>`. Branch: add `--branch [--base auto\|<branch>]`. |
| `assets/report-template.md` | Audit report structure and action plan format (used in **Audit** mode). |

## Show that this skill is in use (required)

1. **First line of your first reply:** `Skill: cd-cesium-vue v1.0.0`, on its own line, then one sentence saying whether you are in **Setup/Build** mode or **Audit** mode.
2. **Project / report output:** in **Audit** mode, include `skill: cd-cesium-vue v1.0.0` in the report byline; in **Setup/Build** mode, note `cd-cesium-vue v1.0.0` in the summary.
3. **Final message:** end with `Skill: cd-cesium-vue v1.0.0`.

## 1. Choose the mode

| Mode | When | What happens |
| --- | --- | --- |
| **Setup / Build** | Adding CesiumJS or `vue-cesium` to a Vue project, writing a Cesium composable/component, or fixing a specific bug/config | Read `references/cesium-patterns.md`, follow the project's `AGENTS.md`, and implement/fix cleanly. |
| **Audit** | Reviewing or auditing an existing Vue-Cesium repo or branch ("audit Cesium", "review our vue-cesium code", "check Cesium performance") | Read-only scan (`scripts/cesium_scan.py`) + manual review against `references/cesium-patterns.md`, writing `reports/cd-cesium-vue/report.md`. |

## 2. Rules

1. **Never wrap Cesium objects in deep Vue reactivity.** `Viewer`, `Scene`, `Camera`, `DataSource`, `Cesium3DTileset`, `Entity`, and `ScreenSpaceEventHandler` must use `shallowRef` or `markRaw` (or live in a plain non-reactive module/composable closure), never `ref()` or `reactive()`.
2. **Always clean up WebGL and listeners.** In `onUnmounted` / `onScopeDispose`, destroy `ScreenSpaceEventHandler`, remove `postRender` / `preRender` / `clock.onTick` listeners, destroy custom `Primitive`s / `DataSource`s, and call `viewer.destroy()` when the owning component unmounts.
3. **No hardcoded tokens or credentials.** `Cesium.Ion.defaultAccessToken` and tile-server API keys must come from `import.meta.env.VITE_*` (or runtime config), never literal strings in source files. Secrets go in Azure DevOps pipeline variables (or CI secret store), never committed `.env` files.
4. **Configure `CESIUM_BASE_URL` for Vite builds.** Raw `cesium` requires `vite-plugin-static-copy` (or `vite-plugin-cesium-build` / `vite-plugin-cesium`) copying `Workers`, `Assets`, `Widgets`, and `ThirdParty` plus `define: { CESIUM_BASE_URL: ... }` so `vite build` works identically to `vite dev`.
5. **Rule precedence (Audit mode).** The project's `AGENTS.md` comes first; `references/cesium-patterns.md` applies on top. Where they conflict, `AGENTS.md` wins.
6. **Read-only in Audit mode.** Empty `reports/cd-cesium-vue/` before writing `report.md` and `evidence/scan.json`, and do not edit source files unless the user asks after the audit.

## 3. Procedure

### Setup / Build mode
1. Read `AGENTS.md` (if present), `package.json`, `vite.config.*`, and `references/cesium-patterns.md`.
2. Verify whether the project uses `vue-cesium` (`VcViewer`, `VcConfigProvider`) or raw `cesium` (`new Viewer(...)`), and match its approach.
3. Ensure Vite static asset copying and `CESIUM_BASE_URL` are configured, `VITE_CESIUM_ION_TOKEN` (if Ion is used) is read from `import.meta.env` with `.env.example` placeholder, and composables use `shallowRef`/`markRaw` + `onUnmounted` cleanup.
4. Run the project's lint/type-check/build if requested or standard for the task, and summarise changes. End with `Skill: cd-cesium-vue v1.0.0`.

### Audit mode
1. **Orient.** Read `AGENTS.md` (if present), `package.json`, `vite.config.*`, and `references/cesium-patterns.md`.
2. **Scan.** Empty `reports/cd-cesium-vue/`, then run:
   - Full: `python scripts/cesium_scan.py <repo> --json reports/cd-cesium-vue/evidence/scan.json`
   - Branch: `python scripts/cesium_scan.py <repo> --branch --json reports/cd-cesium-vue/evidence/scan.json`
3. **Review & Triage.** Inspect every scanner lead in context, drop false positives, merge repeats, and assign severity (`Critical`, `High`, `Medium`, `Low`, `Info`) and confidence (`Confirmed`, `Likely`, `Suspected`) with IDs `CES-01`….
4. **Report.** Read `assets/report-template.md`, build the prioritised **Action plan** last, and write `reports/cd-cesium-vue/report.md`.
5. **Summarise.** Tell the user the verdict/overall health, severity counts, top three actions, and report path. End with `Skill: cd-cesium-vue v1.0.0`.
