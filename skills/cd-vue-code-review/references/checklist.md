# Vue code review checklist

**Precedence:**
1. The project's `AGENTS.md` comes first.
2. This checklist adds general good practice on top.
3. If an item here disagrees with `AGENTS.md`, skip it.

**(scan)** means `scripts/vue_scan.py` raises leads for it. Everything else is your judgement. The team's standards grow here.

## Tiers

| Tier | Severity | Means | Branch verdict | Action plan |
| --- | --- | --- | --- | --- |
| **Fix now** | High (Critical for user-facing bugs or data loss) | Wrong, not just untidy: a bug, a broken architecture rule, lost type safety, a silent failure | Blocks merge (**Fix first**) | P1 |
| **Should fix** | Medium | Works, but makes the code harder to maintain or breaks a house convention | Doesn't block; fix soon | P2 |
| **Tidy-up** | Low | Cleanliness and polish | Doesn't block; fix when passing | P3 |
| **Info** | - | Context: template drift, missing tests, sampling notes | - | Not an action unless the user wants it |

When unsure between two tiers, pick the lower one and say why. Over-calling Fix now trains people to ignore it.

## 1. Architecture and layering

| Check | Typical tier |
| --- | --- |
| Network/API calls only in `src/services/` (scan) | Fix now |
| Stores are per domain, setup-style, no mega-store (scan: size, options style) | Fix now for a mega-store; Should fix for options style |
| Components don't reach into other components' internals; data flows down by props and up by events | Fix now if props are mutated (scan); Should fix otherwise |
| Logic over ~50 lines in a component's script moved to composables (scan, if `AGENTS.md` says so) | Should fix |
| Business logic not in templates (long inline expressions, logic in `v-if`) | Should fix |
| No circular imports; shared code in `utils/` or `composables/`, not copied between features | Should fix |
| Router: lazy-loaded views (scan), route names and meta consistent, guards in one place | Should fix |

## 2. Correctness and Vue practice

| Check | Typical tier |
| --- | --- |
| `v-for` has a stable `:key` (not the index for lists that reorder); no `v-if` on the same element (scan) | Fix now |
| Errors are never swallowed: async errors are logged **and** the user sees feedback (scan: empty catch) | Fix now |
| Store state destructured with `storeToRefs()` (scan) | Fix now if state loses reactivity; actions-only destructuring is fine |
| Listeners, timers and observers cleaned up in `onUnmounted`/`onScopeDispose` | Fix now if it leaks |
| Watchers: specific sources, no `deep: true` unless needed (scan), no watcher doing what a `computed` should | Should fix |
| `await` not missing on promises whose result or failure matters | Fix now |
| `ref()` preferred over `reactive()` (scan, if house rule) | Should fix |

## 3. TypeScript

| Check | Typical tier |
| --- | --- |
| No explicit `any` (scan); `unknown` plus narrowing for untyped data | Fix now |
| Typed props and emits with compiler macros (scan) | Should fix |
| API responses typed at the service boundary; shared types in `src/types/` or next to the feature | Should fix |
| No non-null assertions (`!`) or `as` casts hiding real nullability | Should fix |

## 4. Readability

| Check | Typical tier |
| --- | --- |
| Names say what things are or do; no `data`, `temp`, `handleClick2` | Should fix if misleading; Tidy-up otherwise |
| Functions do one thing; deep nesting flattened with early returns | Should fix |
| Components under ~300 lines and files under ~400 (scan) | Should fix |
| No magic numbers or strings repeated across files; use constants or config | Tidy-up |
| Exported functions have the one-line JSDoc "why" (scan, if house rule) | Tidy-up |
| Comments explain *why*, not *what*. Commented-out code only flagged when excessive (scan: 6+ line blocks, comment-heavy files) | Tidy-up |
| No leftover debug code: `console.*` outside the logger (scan), `debugger` | Should fix |
| TODO/FIXME have context (who or what, or a ticket) (scan) | Tidy-up |

## 5. Styling (Tailwind)

| Check | Typical tier |
| --- | --- |
| Logical properties, not physical (scan, if house rule) | Should fix |
| Semantic theme tokens, no hard-coded colours or arbitrary colour values (scan) | Should fix |
| Repeated utility chains extracted to `@layer components` classes (scan: same chain 3+ times) | Should fix |
| Very long utility lists on one element (scan: 15+) | Tidy-up |
| Motion guarded with `motion-safe:` (scan, if house rule) | Tidy-up |
| No scoped CSS that fights the design system; no `!important` without a reason | Tidy-up |

## 6. Folder structure and tidiness

| Check | Typical tier |
| --- | --- |
| Files in the right folder: stores in `stores/`, services in `services/`, no components in `utils/` (scan) | Should fix |
| Naming: `*.store.ts`, `*.service.ts`, `useThing.ts`, PascalCase components, `*View.vue` views (scan) | Should fix (views: Tidy-up) |
| Nothing loose in the `src/` root beyond `App.vue`, `main.ts` and type shims (scan) | Should fix |
| No dumping-ground folders (25+ files flat) (scan); group by feature | Should fix |
| Non-standard top-level `src/` folders are deliberate and consistent (scan) | Tidy-up |
| No unused components, composables, stores or services (scan, **full mode only**) | Should fix |
| No stray files: `.bak`, `copy`, `old`, `(1)`, `.log`, `.DS_Store` (scan) | Tidy-up |
| No empty folders (scan) | Tidy-up |

## 7. Tests and docs

| Check | Typical tier |
| --- | --- |
| Tests exist for stores, services and composables with logic (scan: none at all → Info) | Info in full mode; Should fix if a branch adds complex logic with no tests and the project has a test setup |
| README updated when behaviour, setup or scripts change (house rule) | Tidy-up |
| Conventional commit messages (commitlint enforces this; only note if bypassed) | Info |

## 8. Template drift (full mode, advisory)

The scanner compares against the latest template `main` (`--template`):
- **Config files:** ESLint, Stylelint, Prettier, tsconfig, commitlint, lint-staged, husky hooks, `health-check.js` and `AGENTS.md`.
- **Scripts** in `package.json`.
- **Quality-tool dependencies.**

| Situation | Tier |
| --- | --- |
| A quality gate weakened or removed: husky hooks, lint/type scripts, `strict` off, lint tools missing | Should fix |
| Config differs from the template | Info: list it, and suggest adopting deliberate template improvements |
| Project predates a template feature | Info |

## Not this skill

- Accessibility → `cd-web-a11y-audit`.
- Security (secrets, `v-html` with user data, auth, CSP) → `cd-web-security-review`.
- Lint, format, types, build size, dependency audit → `npm run health-check`.
