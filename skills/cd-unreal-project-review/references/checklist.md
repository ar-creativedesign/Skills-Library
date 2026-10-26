# Unreal project review checklist

A starting point. Add the team's standards here over time: naming prefixes, folder layout, coding standard, approved plugins, per-platform budgets. **(scan)** means `scripts/project_scan.py` checks it. Everything else is manual.

## 1. Project setup

| Check | Good looks like |
| --- | --- |
| Engine version (scan) | `EngineAssociation` set to one engine version the whole team uses (or a documented source build); upgrades planned, not drifted into |
| Modules and plugins (scan) | Modules named and typed sensibly (Runtime vs Editor); only needed plugins enabled; project plugins under `Plugins/` with clear ownership; marketplace plugins pinned to tested versions |
| Default maps (scan) | `GameDefaultMap` and `EditorStartupMap` exist and are light (a bootstrap or front-end map, not the heaviest level) |
| Rendering features (scan: facts) | Lumen, Nanite, virtual shadow maps and ray tracing chosen deliberately for the target platforms and performance budget; scalability settings defined |
| Input | Enhanced Input for new projects; input actions and mapping contexts as assets |

## 2. Version control

| Check | Good looks like |
| --- | --- |
| .gitignore (scan) | Standard Unreal `.gitignore`: `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`, `.vs/`, generated solution files |
| Generated folders (scan) | Never committed |
| LFS (scan) | `*.uasset` and `*.umap` (plus source art and audio) in Git LFS, marked `lockable`; locking used so two people don't edit the same binary asset |
| Large files (scan) | Nothing over 100 MB outside LFS |
| Other VCS | Perforce: typemap with `+l` (exclusive lock) for binary assets, and a `.p4ignore`. Plastic/Unity VCS: checkout-and-lock for binary assets. |

## 3. Content structure and naming

| Check | Good looks like |
| --- | --- |
| Top-level layout (scan: root clutter) | Project assets under `Content/<ProjectName>/`, separate from marketplace packs and plugins; nothing loose in `Content/` |
| Grouping | By feature or area (e.g. `Characters/`, `Environment/`, `UI/`, `Core/`), with consistent sub-folders |
| Asset names (scan: prefixes, spaces) | Type prefix + PascalCase descriptive name + optional variant suffix, e.g. `SM_Rock_Large_01`, `T_Rock_D`, `MI_Rock_Wet`, `BP_PlayerCharacter`, `WBP_MainMenu`. No spaces or special characters. Prefix list: see below. |
| Leftovers (scan) | StarterContent removed once real content exists; `Developers/` excluded from cooking and never referenced by shipping content |
| Redirectors | No leftover redirectors (run Fix Up Redirectors after moves). Check in the editor. |

**Common prefixes** (from the widely used UE style guide; extend for the team):

| Type | Prefixes |
| --- | --- |
| Blueprints | `BP_` Blueprint, `BPI_` interface, `BPC_` component, `ABP_` Animation Blueprint, `WBP_` Widget Blueprint |
| Meshes and animation | `SM_` Static Mesh, `SK_`/`SKM_` Skeletal Mesh, `SKEL_` Skeleton, `A_`/`AS_` Animation Sequence, `AM_` Montage, `BS_` Blend Space |
| Materials and textures | `M_` Material, `MI_` Material Instance, `MF_` Material Function, `MPC_` Material Parameter Collection, `T_` Texture, `RT_` Render Target |
| Effects and audio | `NS_` Niagara System, `NE_` Niagara Emitter, `SC_`/`MS_` Sound Cue / MetaSound |
| Data and input | `DA_` Data Asset, `DT_` Data Table, `E_` Enum, `F_` Struct, `IA_` Input Action, `IMC_` Input Mapping Context |
| AI and gameplay | `BT_` Behaviour Tree, `BB_` Blackboard, `GA_`/`GE_` Gameplay Ability/Effect |

## 4. Assets (mostly editor checks)

| Check | Good looks like |
| --- | --- |
| Size (scan: very large) | Source resolution matched to use; texture groups and LOD bias set per platform; World Partition or level streaming for big maps |
| Textures | Correct compression settings (normal maps, masks, HDR); sRGB off for data textures; texture streaming on; mip generation set appropriately |
| Meshes | Nanite where appropriate; LODs or Nanite fallback; collision simple where possible; lightmap UVs only if baked lighting is used |
| Materials | Master materials + instances (not one-off materials); shader permutations kept in check; quality switches for low-end platforms |
| References | No accidental hard references pulling huge chains into memory (check Size Map and Reference Viewer); soft references for optional content |

## 5. C++ quality and architecture

| Check | Good looks like |
| --- | --- |
| UObject lifetime (scan) | Every UObject pointer member is a `UPROPERTY()` (with `TObjectPtr` in UE5), or a `TWeakObjectPtr` for non-owning references; no raw pointers the garbage collector can't see |
| Tick (scan) | Tick off by default; events, timers or delegates instead of polling; no actor/component searches, sync loads or spawning in Tick |
| References (scan: hard-coded paths, FObjectFinder) | Asset references exposed as `UPROPERTY` (EditDefaultsOnly) or soft references / Data Assets / Developer Settings; no `TEXT("/Game/...")` strings in code |
| Includes (scan) | Include what you use; no `Engine.h`/`EngineMinimal.h` in headers; forward declarations in headers |
| Size (scan: large files) | Focused classes; components and subsystems instead of huge Actors or GameModes |
| Debug code (scan) | On-screen debug, `DrawDebug*` and verbose logs compiled out of Shipping (`#if !UE_BUILD_SHIPPING`) |
| Blueprint/C++ split | Core systems and performance-critical logic in C++; Blueprints for content, tuning and glue; `BlueprintCallable`/`BlueprintImplementableEvent` APIs designed deliberately |
| Coding standard | Follows Epic's coding standard (naming prefixes `U`/`A`/`F`/`E`/`I`/`T`, `bBool` naming, `const` correctness); a `.clang-format` or agreed style |
| Tests (scan) | Automation Spec / Functional Tests for core logic; run in CI via `RunUAT BuildCookRun` or Gauntlet |

## 6. Packaging and build

| Check | Good looks like |
| --- | --- |
| Cook (scan) | Explicit maps and directories to cook; no cook-everything; `Developers/` excluded |
| Shipping (scan) | Debug files excluded from distribution builds; `ForDistribution` for store builds; Shipping configuration for release |
| Pipeline | Reproducible builds via RunUAT/BuildGraph in CI; DDC shared where the team is large |

## Not covered by a static review (use the editor)

- **Blueprint logic and errors:** compile all Blueprints; Data Validation (`Tools → Validate Data`), or the `DataValidation` commandlet in CI.
- **Asset references and memory:** Reference Viewer, Size Map, Asset Audit.
- **Redirectors:** Fix Up Redirectors.
- **Performance:** Unreal Insights, `stat unit` / `stat gpu`, GPU Visualizer, Memory Insights.
- **Shader permutations and material cost:** shader compile stats, material stats.
- **Packaging size:** the cook and pak reports (`-CreateReleaseVersion`, `UnrealPak -List`).
