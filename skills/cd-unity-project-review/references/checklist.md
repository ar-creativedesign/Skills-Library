# Unity project review checklist

A starting point. Add the team's standards here over time: naming rules, architecture patterns, approved packages, per-platform budgets. **(scan)** means `scripts/project_scan.py` checks it. Everything else is manual.

## 1. Project setup

| Check | Good looks like |
| --- | --- |
| Editor version (scan) | An LTS stream for production; the same exact version across the team (pinned in `ProjectVersion.txt`) |
| Render pipeline (scan) | Chosen deliberately (URP for most cross-platform work, HDRP for high-end). One pipeline asset per quality tier, no unused pipeline packages. |
| Packages (scan) | No preview/experimental packages in production without a reason; git packages pinned to a tag or commit; no packages referenced from outside the repo; `packages-lock.json` committed; unused packages removed |
| Input (scan) | One input system: the new Input System for new work, not "Both" |
| Player settings (scan) | Linear colour space for PBR; incremental GC on; scripting backend suited to the platform (IL2CPP for mobile/console release); managed stripping level set deliberately |

## 2. Version control

| Check | Good looks like |
| --- | --- |
| Serialization (scan) | Force Text, so scenes and prefabs can be diffed and merged |
| Meta files (scan) | Visible Meta Files mode; every asset and folder has a committed `.meta`; no orphan `.meta` files |
| .gitignore (scan) | Standard Unity `.gitignore`: `Library/`, `Temp/`, `Obj/`, `Logs/`, `UserSettings/`, `Build*/`, IDE folders |
| Generated folders (scan) | `Library/` etc. never committed |
| Large files (scan) | Git LFS for binaries (PSD, FBX, textures, audio, video); nothing over 100 MB outside LFS |
| Merge tooling | UnityYAMLMerge (Smart Merge) configured for scenes and prefabs; scene ownership or prefab-heavy workflow to limit conflicts |

## 3. Structure and naming

| Check | Good looks like |
| --- | --- |
| Top-level layout (scan: root clutter) | Project content under one root folder (e.g. `Assets/_Project/` or `Assets/<Game>/`), separate from third-party store assets and plugins; nothing loose in `Assets/` |
| Grouping | By feature (e.g. `Player/`, `UI/`, `Enemies/`), or by type within features. Pick one and be consistent. |
| Names (scan: spaces/symbols) | No spaces or special characters; PascalCase for assets and scripts; script file name = class name |
| Special folders (scan: Resources) | `Resources/` avoided or minimal (prefer Addressables); `Editor/` folders for editor-only code; `StreamingAssets/` only for raw files |
| Scenes (scan: build list) | Build Settings list matches real scenes; a clear bootstrap/startup scene; test/sandbox scenes kept out of builds |

## 4. Assets

| Check | Good looks like |
| --- | --- |
| Textures (scan) | Read/Write off unless the CPU needs the data; mipmaps off for UI and sprites; compression on, with per-platform overrides; max size matched to on-screen use (rarely 8K); power-of-two where compression needs it |
| Audio (scan) | Long music and ambience set to Streaming or Compressed In Memory; short SFX set to Decompress On Load; mono where stereo isn't needed; sample rate matched to the platform |
| Models (scan: Read/Write) | Read/Write off; animation import off for static meshes; sensible scale factor; LODs for distant objects |
| Materials and shaders | Shared materials, not per-object duplicates; shader variant count kept in check (shader stripping); no unused shaders in Always Included |
| Prefabs | Nested prefabs and variants used instead of duplicated hierarchies; no deep "god" prefabs |
| Loading | Addressables (or a deliberate alternative) for large and optional content; no hard references from bootstrap scenes to the whole game |

## 5. Code quality and architecture

| Check | Good looks like |
| --- | --- |
| Assemblies (scan) | Assembly definitions for game, editor and tests once a project is more than small; clear dependency direction |
| Size and responsibility (scan: large scripts) | Small, focused classes; managers that don't become god objects; ScriptableObjects for data and config |
| Editor code (scan) | `UnityEditor` only in `Editor/` folders or behind `#if UNITY_EDITOR` |
| Per-frame work (scan) | No `GetComponent`/`Find*`/LINQ/allocations/`Instantiate`/`Destroy` in `Update`/`FixedUpdate`/`LateUpdate`: cache references, pool objects, prefer events over polling |
| Unity callbacks (scan: empty) | No empty `Update`/`Start` etc. |
| Async (scan: async void) | `async Task`/`Awaitable`/UniTask with cancellation tied to object lifetime; no `async void` except event handlers |
| Serialization (scan: public fields) | `[SerializeField] private` fields with read-only properties; no public mutable fields for the Inspector's sake |
| Coupling (scan: string calls, Find) | Dependencies passed in or injected, not found by name or tag at runtime; no `SendMessage`; string-based `Invoke`/`StartCoroutine` avoided |
| Namespaces (scan) | All project code in a namespace |
| Logging (scan) | A conditional logger or `[Conditional]` wrapper, so release builds don't pay for logs |
| Error handling | Null checks at boundaries; `OnValidate` or validation tools for Inspector data |
| Tests (scan) | Unity Test Framework edit-mode tests for logic, play-mode tests for key flows; tests run in CI |

## 6. Build and tooling

| Check | Good looks like |
| --- | --- |
| Build pipeline | Builds reproducible from the command line or CI (`-batchmode -executeMethod …` or Unity Build Automation / GameCI) |
| Static analysis | Roslyn analyzers or an `.editorconfig` with agreed rules; Unity's Project Auditor where available |
| Profiling discipline | Performance budgets per platform; Profiler and Memory Profiler captures before release |

## Not covered by a static review (use the editor)

- **Frame time and memory:** Profiler, Memory Profiler, Frame Debugger.
- **Shader variants and cost:** shader compilation logs, Frame Debugger.
- **Scene and prefab wiring, missing references:** a missing-references finder, or Project Auditor.
- **Build size breakdown:** the Editor log after a build, or the Build Report Inspector.
- **Runtime behaviour on target devices.**
