# Code mode: reviewing the codebase for accessibility

Used by `SKILL.md` when you have the project's source code. Code mode finds the **cause** of issues: which component, which CSS rule, which router hook. It also catches issues in states the live audit didn't reach. It does not replace the live audit: many failures (contrast over real content, sticky panels at zoom, focus order) only show up in the rendered page.

## 1. Get oriented (read-only)

1. Find the app root(s): `package.json`, framework config (`vite.config.*`, `nuxt.config.*`, `next.config.*`, `angular.json`), `index.html`, app shell/layout component, router, global styles, design-system or theme tokens.
2. Note the component library (Bootstrap, PrimeVue, Vuetify, MUI, Headless UI…). Many issues come from how its components are configured. Check the library's accessibility docs for the version in use.
3. Check what accessibility tooling already exists:
   - **Linters:** `eslint-plugin-vuejs-accessibility`, `eslint-plugin-jsx-a11y`, `@angular-eslint` template a11y rules.
   - **Test tools:** `@axe-core/playwright`, `jest-axe`, `cypress-axe`, Lighthouse CI.
   - **CI steps** that run any of them.

   Missing tooling is a process issue, not a WCAG one. Add it to the action plan as a P4 action.

## 2. Run the scanner

```bash
python scripts/code_scan.py <repo-root> --json reports/cd-web-a11y-audit/evidence/a11y-code-scan.json
```

It's standard-library Python only. It flags **leads** grouped by rule, with WCAG reference, file and line. Rules cover:
- images without alt
- click handlers on non-interactive elements
- `role=button` without key handling
- positive tabindex
- removed focus outlines
- zoom-blocking viewport, missing `lang`, autoplay
- placeholder-only inputs, suspicious `aria-label`s ("Disabled", "Icon", "Click me")
- `aria-hidden` on focusable elements, `href="#"`, headings inside buttons or links
- fixed height + `overflow:hidden`, `word-break`, sticky/fixed elements
- tooltip libraries, buttons that navigate, new tabs without warning, dialogs, autofocus

It also flags repo-wide gaps:
- a router without per-route titles or focus management
- no `prefers-reduced-motion`
- no skip link, no `<main>`
- global focus styles

**Read each hit in context before keeping it.** Typical false positives:
- `alt` set by a child component prop
- `role` and key handling added by a wrapper component
- `outline:none` with a visible `box-shadow` replacement in the same rule
- `height` with `overflow:hidden` on a purely decorative element

## 3. Run existing project tooling (if present, without changing the project)

- An existing lint script: `npm run lint`. Report accessibility-rule hits.
- Existing tests that include axe: run them and report the results.
- Don't add dependencies, change config or commit anything unless the user asks. If tooling is missing, recommend it with the exact package and a config snippet.

## 4. Manual code review checklist

Work through these, guided by the scanner output and by what the live audit found:

| Area | Look for | WCAG |
| --- | --- | --- |
| App shell / layout | `<html lang>`, `<main>`, skip link as first focusable element, landmarks, one `<h1>` per route | 3.1.1, 1.3.1, 2.4.1 |
| Router | Per-route `document.title` (or `useHead`/Helmet); after navigation, focus moves to the `<h1>` or main, or an `aria-live` announcement | 2.4.2, 2.4.3, 4.1.3 |
| Interactive components | Native `<button>`/`<a>` used, or full keyboard support (Enter/Space/Escape/arrows) with role and state (`aria-expanded`, `aria-checked`, `aria-current`, `aria-selected`) bound to component state | 2.1.1, 4.1.2 |
| Navigation | Things that navigate are links (`<router-link>`, `<a href>`), not buttons with `router.push` | 4.1.2 |
| Forms | Each control has a `<label for>` or `aria-labelledby`; errors rendered in text, linked with `aria-describedby`, announced; `autocomplete` on personal fields | 1.3.1, 1.3.5, 3.3.1–3.3.3 |
| Dialogs / menus / tooltips | Focus moved in, trapped, Escape closes, focus restored. Tooltips hoverable and dismissible, or replaced with a disclosure. `aria-modal` only when the background is truly inert. | 2.1.2, 2.4.3, 1.4.13 |
| Global CSS | Focus-visible style reaches 3:1 on every background; no `outline:none` without replacement; text in `rem`; no fixed heights with `overflow:hidden` on text containers; sticky/fixed UI sized for short and zoomed viewports (`@media (max-height: …)`); `scroll-padding-top` matches sticky header height | 2.4.7, 1.4.11, 1.4.4, 1.4.10, 1.4.12, 2.4.11 |
| Design tokens | Compute contrast of text/background token pairs and UI/focus tokens (e.g. with `__a11y.contrast()` or a quick script) | 1.4.3, 1.4.11 |
| Content from a CMS | Rich-text renderer: non-breaking spaces, headings levels, image alt fields required in the CMS schema, link text | 1.4.10, 1.3.1, 1.1.1, 2.4.4 |
| Motion / media | `prefers-reduced-motion` respected; carousels pausable; captions/track files for video | 2.2.2, 1.2.x |
| Tests / CI | axe in end-to-end tests, a11y lint rules, Lighthouse CI budgets | (process) |

## 5. Tie live and code findings together

For every live finding, try to locate its source:
- Search for the class names, `id`s or text in the live evidence (e.g. `.heroesContainer`, `section-nav-item`).
- Search for the CSS property values `focusRules()` reported.
- Find the component that renders the failing widget.

Put the file and line in the finding's **Source** column. When a code lead has no live counterpart, either confirm it in the browser or mark it **Found by: code** with confidence **Likely**. A finding confirmed in both places is **Found by: both**.
