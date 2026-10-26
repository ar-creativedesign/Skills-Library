---
title: Live-browser accessibility audit prompt (WCAG 2.2 AA)
version: 1.0
updated: 2026-10-26
works_with: Claude (Claude in Chrome, Claude desktop built-in browser, Claude Code + Playwright) and Google Antigravity (browser subagent)
tags: [accessibility, wcag, audit, prompt]
---

# Live-browser accessibility audit (WCAG 2.2 AA)

Copy everything below the line into a new agent session. Fill in the **Inputs** block first. Nothing else needs attaching: the checklist, test scripts and report format are all included.

---

## Inputs

```yaml
TARGET_URL: https://example.com/            # start page
SCOPE: whole site, up to 15 representative pages   # or a list of URLs / user journeys
EXCLUDE: []                                 # paths not to touch, e.g. /admin, /checkout
LOGIN: none                                 # or "I will sign in for you in the browser" (never paste passwords here)
FORMS_MAY_BE_SUBMITTED: no                  # yes = only the forms listed here, with obviously fake data
EXTRA_GUIDANCE: none                        # e.g. brand colours, design-system name, known exceptions
REPORT_FILE: a11y-audit-{domain}-{YYYY-MM-DD}.md
EVIDENCE_DIR: a11y-evidence/
```

## Your role

You are a senior accessibility auditor. Audit `TARGET_URL` against **WCAG 2.2 level AA**, using the checklist in this prompt, by **driving a real browser**: loading pages, resizing the viewport, pressing keys, hovering, opening menus and measuring the rendered page. Then write a report that a development team can act on.

## Non-negotiable rules

1. **Live browser only.** Every finding must come from the rendered site in a browser you control. Reading source code, HTML from a plain HTTP fetch or a repo is **not** an audit. Single-page apps often return an empty shell without JavaScript. If you have no browser tool, or the browser cannot load the site, **stop and say so**. Do not produce a report from code or memory.
2. **Evidence for every finding.** Each issue needs at least one of: a screenshot path, a measured value (for example a contrast ratio, element size or `scrollWidth`), or the exact keyboard sequence and what happened. No evidence means no finding.
3. **Confirm before reporting.** Automated results are leads, not findings. Confirm each one by looking (screenshot) or by a second, different measurement. Real keyboard presses beat scripted `.focus()`.
4. **Do no harm.**
   - Do not submit forms unless `FORMS_MAY_BE_SUBMITTED` names them. Trigger validation by leaving fields and using invalid values instead.
   - Do not create accounts, make purchases, send messages or change settings.
   - Do not enter real personal data or credentials. If a login is needed, ask the user to sign in themselves in the browser.
5. **Cookie/consent banners.** Record their accessibility first. Then either choose "Reject all / necessary only", or hide the banner with CSS (`display:none`) for the rest of the audit. Never accept on the user's behalf.
6. **Bot protection.** If the site returns 403, a CAPTCHA or a challenge page, **do not try to evade it**: no user-agent spoofing, proxies or stealth plugins. Switch to a browser the user controls (for example their own Chrome via an extension), or stop and report the block.
7. **Stay in scope.** Do not follow links off the target domain, except to check that a link exists or opens in a new tab.
8. **Be honest about coverage.** List what you could not test, for example screen readers, PDFs, real devices or pages behind login.

## Use your browser tools (Claude or Antigravity)

Work out which browser you have, then map the actions below onto its tools.

| Action | Claude in Chrome / Claude desktop built-in browser | Claude Code (terminal) | Antigravity browser subagent |
| --- | --- | --- | --- |
| Open page | `navigate` | Playwright MCP `browser_navigate`, or a headed Playwright script | `browser_navigate` / `open_browser_url` |
| Run page JavaScript | `javascript_tool` | `browser_evaluate` / `page.evaluate` | `execute_browser_javascript` |
| Screenshot | `computer` → screenshot / zoom | `browser_take_screenshot` | `capture_browser_screenshot` (interactions are also recorded automatically) |
| Resize viewport | `resize_window` (custom sizes or presets) | `browser_resize` / `setViewportSize` | `browser_resize_window` |
| Key presses (Tab, Shift+Tab, Enter, Space, Escape, arrows) | `computer` → key | `browser_press_key` / `keyboard.press` | `browser_press_key` |
| Hover / click | `computer` → hover / left_click | `browser_hover` / `browser_click` | `browser_click_element`; hover via JavaScript if no hover tool |
| Read structure | `read_page` / `get_page_text` | `browser_snapshot` (accessibility tree) | `read_browser_page` |

**Antigravity:** the main agent hands browser work to the browser subagent. The subagent may not see this prompt, so put the exact steps, the viewport size and the **full Audit Kit script** into each delegated task. Ask it to return the JSON results and screenshot paths.

**If you only have a terminal:** use headed Chromium via Playwright (`npx playwright` or Python). Save screenshots into `EVIDENCE_DIR`. If the site blocks automated browsers, follow rule 6.

**Viewport sizes:** if your tool resizes the *window* rather than the viewport, check the real size with `document.documentElement.clientWidth/clientHeight` and record that. Mobile emulation can widen the layout viewport when content overflows, so always compare `scrollWidth` with `clientWidth`, not `innerWidth`.

**SPAs:** single-page apps keep JavaScript state between route changes. Injecting the Audit Kit once and then navigating with in-app links (or the app's router) is faster. Re-inject it after any full page load.

## Test matrix

Run every template page at **Desktop**. Run the **reflow, zoom, landscape and text-spacing** rows on at least the home page, one content-heavy page, one page with forms or search, and any page with sticky or fixed UI.

| Label | Viewport (CSS px) | Represents / criterion |
| --- | --- | --- |
| Desktop | 1280 × 800 | Baseline |
| Tablet | 768 × 1024 | Breakpoint check |
| Mobile | 375 × 812 | Phone portrait |
| Landscape | 812 × 375 | 1.3.4 Orientation, short screens |
| 200% zoom | 640 × 400 | 1.4.4 Resize text (1280 × 800 at 200%) |
| 400% zoom | 320 × 256, then 320 × 640 | 1.4.10 Reflow (1280 wide at 400%) |
| Text spacing | Mobile and Desktop with `__a11y.spacing(true)` | 1.4.12 Text spacing |

## Procedure

### Phase 1: Discover

1. Load `TARGET_URL`. Note the page title, `lang`, the framework if obvious (Vue/React/Next etc.), and whether it is an SPA (does the URL change without a full reload?).
2. Build the page list. Use the main nav, footer, sitemap (`/sitemap.xml`) and in-page links. Pick **one page per template** plus key journeys: home, a listing, a detail/article, search results, a form, the 404 page, and the accessibility statement, cookie and privacy pages. Stay within `SCOPE`.
3. List the interactive components you can see: menus, dropdowns, accordions, tabs, modals, carousels, tooltips, maps, filters, search, pagination, media players, cookie banner. Each one gets the interaction tests in Phase 3.

### Phase 2: Automated scan (every page × required viewports)

1. Inject the **Audit Kit** (bottom of this prompt) with your JavaScript tool.
2. Run `__a11y.scan()` and save the JSON.
3. Run `await __a11y.sticky()` at Desktop, 200% zoom, Landscape and 400% zoom. If `coveredPct` is above about 40%, or `visibleContentPx` is under about 150, that is a reflow/zoom problem: screenshot it.
4. Run `__a11y.spacing(true)` and then `__a11y.clipped()` at Mobile and Desktop. Any result listing **HIDDEN CONTROLS** is a 1.4.12 failure. Screenshot it, then run `__a11y.spacing(false)`.
5. Run `await __a11y.obscured('main')` (or `'body'`) on pages with sticky or fixed UI. Confirm one sample with real **Shift+Tab** and a screenshot.
6. Run `__a11y.focusRules()` once, to find the CSS behind focus styles and quote the root cause in remediation.
7. *Optional:* if the page's Content-Security-Policy allows it, also inject axe-core (`https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js`) and run `axe.run({runOnly:['wcag2a','wcag2aa','wcag21aa','wcag22aa']})`. Treat its output as extra leads. If CSP blocks it, carry on with the kit.

### Phase 3: Interactive checks (real input, not scripts)

Do these with real key presses and pointer actions. Take a screenshot of anything that fails.

1. **Keyboard walk (2.1.1, 2.1.2, 2.4.1, 2.4.3, 2.4.7, 2.4.11).** Start from the address bar or the top of the page and press Tab through the whole page.
   - Is a skip link first, and does it work?
   - Does focus order follow the visual order?
   - Is focus visible at every stop? Run `__a11y.focusNow()` at a few stops on light and on dark backgrounds to get the ring contrast.
   - Is focus ever hidden behind sticky or fixed UI?
   - Are there any traps?
   - Repeat part of the page with Shift+Tab.
2. **Menus and disclosures (4.1.2, 2.1.1).** Open each with Enter or Space.
   - Does `aria-expanded` change? Does Escape close it?
   - Does focus return to the trigger?
   - Can the sub-menu items be reached?
3. **Dialogs, modals and the cookie banner (2.4.3, 4.1.2, 2.1.2).**
   - Does focus move into the dialog and stay trapped there?
   - Is the background inert? Does Escape close it?
   - Does focus return to where it was?
   - If it claims `aria-modal="true"`, does it behave like a modal?
4. **Hover and focus content (1.4.13).** For tooltips, popovers and mega-menus: open them by hover *and* by keyboard focus.
   - Can you move the pointer onto the content without it disappearing?
   - Does Escape dismiss it?
   - Does it stay open until dismissed?
   - Are any buttons inside it reachable?
5. **Forms (1.3.1, 1.3.5, 3.3.1–3.3.4, 3.3.7, 4.1.2).** Check that labels are visible and programmatic, that required fields are marked, and that personal fields have `autocomplete`.
   - Trigger errors without submitting real data. Is each error in text, linked to its field, and announced or given focus? Does it suggest a fix?
   - For multi-step forms, is information re-asked?
   - For legal, financial or data submissions, can the user review or undo?
6. **Search, filters and pagination (4.1.3, 4.1.2, 1.4.1).**
   - Are result counts and changes announced through a status/live region?
   - Is the current page marked with `aria-current` and with more than colour?
7. **Route changes in SPAs (2.4.2, 2.4.3, 4.1.3).** After each in-app navigation:
   - Did `document.title` change to describe the page?
   - Where is focus (`__a11y.focusNow()`)?
   - Is the new page announced?
8. **Motion, media and timing (1.2.x, 1.4.2, 2.2.1, 2.2.2, 2.3.1).**
   - Carousels and auto-moving content need pause/stop.
   - Video needs captions and audio description or an alternative; audio needs a transcript.
   - Autoplay audio over 3 seconds needs a control.
   - Session timeouts need a warning and a way to extend.
   - Nothing should flash more than three times a second.
9. **Pointer and drag (2.5.1, 2.5.2, 2.5.4, 2.5.7, 2.5.8).**
   - Maps, sliders, carousels and drag-and-drop need single-pointer, keyboard alternatives.
   - Gestures and motion need alternatives.
   - Targets should be at least 24 × 24px or meet the spacing exception.
10. **Orientation (1.3.4).** At Landscape, is anything locked, lost or unusable?
11. **Consistency (3.2.3, 3.2.4, 3.2.6, 2.4.5).**
    - Is navigation in the same order on every page, and are components named the same way?
    - Is help or contact in a consistent place?
    - Is there more than one way to find pages (nav plus search or sitemap)?
    - Is the accessibility statement linked from every page?
12. **Authentication (3.3.8)** if `LOGIN` is in scope. Check for no cognitive tests without an alternative, paste allowed, and password managers working.

### Phase 4: Triage and de-duplicate

- Merge duplicates. One component failing on 12 pages is **one site-wide issue** listing those pages, not 12 issues.
- Ignore known false positives:
  - visually hidden (`.sr-only`, `.visually-hidden`) text counted as "clipped"
  - `svg role="img"` that also has `aria-hidden="true"`
  - decorative images with `alt=""`
  - text over images, which the script can't measure (check by eye)
  - scripted `.focus()` not showing `:focus-visible` (always re-check with real Tab)
- Give each issue a severity (rubric below) and an ID: `SW-01` for site-wide, then a short prefix per page, for example `HM-01` (home) or `PR-01` (product).

### Phase 5: Verify

Before writing, re-test **every** issue on a fresh page load at the viewport it was found at. Use the targeted check or interaction that proves it. Drop anything you cannot reproduce, or mark it **Unconfirmed** with the reason. Correct details or root causes the re-test changes.

### Phase 6: Report

Write `REPORT_FILE` in Markdown (Obsidian-friendly) and save screenshots in `EVIDENCE_DIR`, using the template below. If your environment offers a shareable document or artifact, you may publish it there too.

## Severity rubric

| Severity | Use when |
| --- | --- |
| Critical | Blocks a core task for a group of users at a common setting. Examples: content unreachable by keyboard, content fully covered at 200% zoom, a keyboard trap, a modal that can't be closed. |
| High | A clear WCAG A/AA failure with a significant barrier. Examples: no accessible name on a key control, failed text contrast on core content, no page titles, reflow failure on main content, hover content that can't be dismissed. |
| Medium | A WCAG A/AA failure with a workaround, or limited reach. Examples: heading-level skips, missing `aria-expanded`, a weak focus ring, unannounced status messages, navigation built from buttons. |
| Low | Best practice, AAA, or a borderline pass. Examples: links opening a new tab without warning, 22px targets that pass via spacing, verbose names. |

## Checklist: what to test and what passes (WCAG 2.2 AA)

Process items (accessibility in the definition of done, design annotations, a WCAG 2.2 AA target in the backlog) can't be checked in a browser. Mention them only if `EXTRA_GUIDANCE` gives you documents to check.

### Perceivable

| Item (WCAG) | Test in the browser | Passes when |
| --- | --- | --- |
| Images and alt text (1.1.1, 1.4.5) | `scan()` image results; inspect informative images, icons, image links, maps and charts | Informative images have concise alt that conveys purpose; decorative ones `alt=""`; no "image of"; no text baked into images except logos |
| Audio and video (1.2.1–1.2.5) | Play media; look for captions, transcripts and audio description | Captions synchronised and accurate, including sounds; transcript for audio; audio description or alternative for visual-only information; live captions for live media |
| Colour and sensory cues (1.3.3, 1.4.1) | Status, errors, links, charts, "current page", instructions | Meaning never relies on colour, shape, position or sound alone; links in text are distinguishable without colour or are 3:1 against surrounding text plus a non-colour cue on hover/focus |
| Contrast (1.4.3, 1.4.11) | `scan().textContrastFails`; check UI borders, icons, focus rings and selected states with `__a11y.contrast()`; check text over images by eye | Text 4.5:1 (large text ≥ 24px or ≥ 18.66px bold: 3:1); UI component boundaries, icons and focus/selected indicators 3:1 against adjacent colours; disabled controls exempt |
| Resize and reflow (1.4.4, 1.4.10) | 200% and 400% rows: `scan().horizontalScroll`, `overflowingElements`, `clipped`, `sticky()`, screenshots | No horizontal scrolling at 320px (except tables, maps, diagrams); nothing clipped, truncated or overlapping; sticky/fixed UI leaves the content readable; all functionality still available |
| Text spacing (1.4.12) | `spacing(true)` then `clipped()` and screenshots | No text or control lost, clipped or overlapped |
| Orientation (1.3.4) | Landscape row; look for orientation locks or "rotate your device" messages | Works in both orientations |
| Flashing (2.3.1) | Watch animations and video | No more than three flashes per second |
| Info and relationships (1.3.1) | `scan().headingOutline` and `headingIssues`, landmarks, lists, tables (`th`, `scope`, caption), form grouping | Structure visible on screen is in the markup: one descriptive H1, no skipped levels, headings not inside buttons/links, `main`/`nav`/`header`/`footer`, data tables marked up, related controls grouped with a label |
| Meaningful sequence (1.3.2) | Compare DOM order (`read_page`) with the visual order | Reading order matches the meaning |

### Operable

| Item (WCAG) | Test in the browser | Passes when |
| --- | --- | --- |
| Keyboard (2.1.1, 2.1.4) | Phase 3.1–3.4 | Everything works by keyboard; custom widgets respond to Enter/Space/arrows/Escape as their pattern expects; single-key shortcuts can be turned off or remapped |
| No keyboard trap (2.1.2) | Tab into and out of every widget, iframe and modal | You can always leave with Tab, Shift+Tab or Escape |
| Focus visible (2.4.7) | Real Tab; `focusNow()`; `focusRules()` | A visible indicator on every focusable element, at least 3:1 against what is next to it (checklist standard) |
| Focus not obscured (2.4.11) | `obscured()` plus real Shift+Tab at Desktop, 200% zoom and Landscape | The focused element is never *entirely* hidden by sticky headers, banners or overlays |
| Focus order and reading order (2.4.3, 1.3.2) | Keyboard walk; overlays; route changes | Logical order; focus moves into, through and out of overlays; after an SPA navigation focus goes somewhere sensible |
| Bypass blocks (2.4.1) | First Tab stop; landmarks | A skip link, visible on focus, that moves focus to main; or landmarks/headings on every template |
| Timing (2.2.1) | Session timeouts, timed content | Can be turned off, adjusted or extended (at least 20 seconds' warning) |
| Pause, stop, hide; audio control (2.2.2, 1.4.2) | Carousels, tickers, autoplay | Controls for anything moving automatically for more than 5 seconds; audio over 3 seconds can be stopped |
| Pointer (2.5.1, 2.5.2, 2.5.4, 2.5.7) | Maps, sliders, swipe, drag-and-drop | Single-pointer, non-drag alternatives; activation on up-event or cancellable; motion has alternatives |
| Target size (2.5.8) | `scan().smallTargets`; measure with padding | At least 24 × 24px, or the spacing, inline, equivalent-control or essential exception applies (say which) |
| Page titled (2.4.2) | `document.title` on every page and after every route change | Unique and descriptive per page |
| Link purpose; headings and labels (2.4.4, 2.4.6) | `vagueLinks`, `linksNoName`, `controlsNoName`, `newWindowNoWarning` | Purpose clear from the link text or its context; headings and labels describe their content |
| Multiple ways (2.4.5) | Nav, search, sitemap | At least two ways to find pages |

### Understandable

| Item (WCAG) | Test in the browser | Passes when |
| --- | --- | --- |
| Language (3.1.1, 3.1.2) | `scan().lang`; passages in another language | `<html lang>` correct; other-language passages have `lang` |
| Labels and instructions (3.3.2) | `fieldsNoLabel`; look at every form | Visible, programmatically associated labels; required fields marked; placeholder isn't the only label |
| Errors (3.3.1, 3.3.3) | Trigger validation without submitting real data | The error is described in text, linked to its field, announced or focused, with a suggested fix |
| Error prevention (3.3.4) | Legal, financial or data-changing submissions | Can be reviewed, checked or undone |
| On focus, on input; hover/focus content (3.2.1, 3.2.2, 1.4.13) | Focus and change controls; Phase 3.4 | No unexpected context change; extra content is dismissible, hoverable and persistent |
| Consistent navigation, identification, help (3.2.3, 3.2.4, 3.2.6) | Compare templates | Same order and names; help in the same place |
| Redundant entry (3.3.7) | Multi-step flows | Information already given is filled in or selectable |
| Accessible authentication (3.3.8) | Login, if in scope | No cognitive function test without an alternative; paste and password managers allowed |

### Robust

| Item (WCAG) | Test in the browser | Passes when |
| --- | --- | --- |
| Name, role, value (4.1.2) | `controlsNoName`, `customRoleTabindex`, `expandableNoState`, `clickableNonSemantic`, `focusableInsideAriaHidden`, `duplicateIds`; Phase 3.2–3.3 | Native elements where possible; custom widgets expose correct role, name and state (`aria-expanded`, `aria-checked`, `aria-current`); links navigate, buttons act |
| Label in name (2.5.3) | `fieldLabelMismatch`; compare visible text with `aria-label` | The accessible name contains the visible label text, ideally at the start |
| Input purpose (1.3.5) | `autocompleteMissing` | Personal-data fields have correct `autocomplete` tokens |
| Status messages (4.1.3) | Search, filters, cart, form success, pagination; `scan().liveRegions` | Announced through `role=status`/`alert` or `aria-live` without moving focus |
| Assistive tech compatibility | Note as not tested unless you have a screen reader | List as a limitation; recommend NVDA and VoiceOver checks |

## Report template

```markdown
# {Site name} – Accessibility Audit

{date} · audited against WCAG 2.2 AA · {agent/model}

## Summary
{One-sentence verdict.} {N} issues: {c} critical, {h} high, {m} medium, {l} low.

| Severity | Count |
| --- | --- |

Fix these first: {3–5 numbered items with IDs, one line each}

## Scope and method
Pages tested: {list}. Browser: {name/version}. Date and time.
| Label | Viewport (CSS px) | Represents |   ← the test matrix rows you actually ran
Automated checks and interactive checks performed. Re-test: {what was confirmed or dropped}.

## Site-wide issues
| ID | Issue | Severity | Guidance broken | Pages | Size / zoom | Evidence | Remediation |

## {Page name} ({path})
| ID | Issue | Severity | Guidance broken | Size / zoom | Evidence | Remediation |
(one section per page or template; "No page-specific issues" if none)

## Evidence
{Screenshots embedded or linked, each captioned with ID, page, viewport and what it shows}

## What passed
{Bulleted list of notable passes}

## Not covered
{Screen readers, PDFs, other browsers/devices, pages behind login, contrast over images, etc.}
```

**How to write each finding:**
- **Issue:** what happens, where and with what value, for example "Active pill white on #A8A8A8 = 2.38:1" or "At 640 × 400 sticky header and filters cover 100% of the viewport".
- **Guidance broken:** the WCAG number and name, plus the checklist item in brackets.
- **Size / zoom:** the matrix label(s) where it fails, or "All".
- **Evidence:** a screenshot file and/or the measurement.
- **Remediation:** a concrete fix aimed at the component or CSS rule, for example "Replace `height` with `min-height` on `.hero`; remove `overflow:hidden`". Quote the root-cause rule from `focusRules()` or computed styles where you found it.
- Keep sentences short, use specifics rather than adjectives, use UK English, and never pad.

## Audit Kit (inject into each page with your JavaScript tool)

Paste the whole block as one JavaScript evaluation. It defines `window.__a11y` and returns a confirmation string. Results are plain JSON. `sticky()` and `obscured()` are async: `await` them.

```javascript
(() => {
  const A = {};
  const vis = e => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0 && !e.closest('[aria-hidden="true"]'); };
  const srOnly = e => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return (s.position === 'absolute' && (s.clip !== 'auto' || s.clipPath === 'inset(50%)')) || (r.width <= 2 && r.height <= 2); };
  const sel = e => { const p = []; while (e && e.nodeType === 1 && p.length < 4) { let s = e.tagName.toLowerCase(); if (e.id) { p.unshift(s + '#' + e.id); break; } const c = [...e.classList].slice(0, 2); if (c.length) s += '.' + c.join('.'); p.unshift(s); e = e.parentElement; } return p.join(' > '); };
  const txt = e => (e.textContent || '').trim().replace(/\s+/g, ' ');
  const byIds = ids => ids.split(/\s+/).map(i => document.getElementById(i)?.textContent || '').join(' ').trim();
  const name = e => {
    if (e.getAttribute('aria-labelledby')) { const n = byIds(e.getAttribute('aria-labelledby')); if (n) return n; }
    if (e.getAttribute('aria-label')?.trim()) return e.getAttribute('aria-label').trim();
    if (e.labels && e.labels.length) return [...e.labels].map(txt).join(' ');
    if (!/^(INPUT|SELECT|TEXTAREA)$/.test(e.tagName)) {
      const t = txt(e); if (t) return t;
      const im = [...e.querySelectorAll('img[alt]')].map(i => i.alt.trim()).filter(Boolean).join(' '); if (im) return im;
      const st = e.querySelector('svg title'); if (st?.textContent.trim()) return st.textContent.trim();
    }
    return (e.getAttribute('title') || '').trim();
  };
  const P = c => { const m = String(c).match(/[\d.]+/g); return m ? m.map(Number).concat(m.length === 3 ? [1] : []) : [0, 0, 0, 0]; };
  const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  A.contrast = (fg, bg) => +ratio(P(fg), P(bg)).toFixed(2);
  const bgOf = e => { const layers = []; while (e) { const s = getComputedStyle(e); if (s.backgroundImage !== 'none' && !/gradient/.test(s.backgroundImage) && e !== document.body && e !== document.documentElement) return { image: true }; const c = P(s.backgroundColor); if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } e = e.parentElement; } let out = [255, 255, 255]; layers.reverse().forEach(c => { out = out.map((v, i) => v * (1 - c[3]) + c[i] * c[3]); }); return { c: out }; };
  const FOCUSABLE = 'a[href],button,input:not([type=hidden]),select,textarea,summary,iframe,[tabindex]:not([tabindex="-1"]),[contenteditable="true"]';
  const cap = (arr, n = 15) => ({ count: arr.length, samples: arr.slice(0, n) });

  A.scan = () => {
    const de = document.documentElement, R = {};
    R.url = location.href; R.viewport = de.clientWidth + 'x' + de.clientHeight; R.title = document.title; R.lang = de.lang || '(none)';
    R.landmarks = { main: document.querySelectorAll('main,[role=main]').length, nav: document.querySelectorAll('nav,[role=navigation]').length, header: document.querySelectorAll('header,[role=banner]').length, footer: document.querySelectorAll('footer,[role=contentinfo]').length };
    const foc = [...document.querySelectorAll(FOCUSABLE)].filter(e => !e.disabled && vis(e));
    R.firstFocusable = foc[0] ? (name(foc[0]) || sel(foc[0])).slice(0, 60) : null;
    R.skipLink = foc.slice(0, 3).some(e => /skip|main content|jump to content/i.test(name(e)));
    const hs = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6,[role=heading]')].filter(vis);
    R.h1 = hs.filter(h => (h.getAttribute('aria-level') || h.tagName[1]) == 1).map(h => txt(h).slice(0, 60));
    let last = 0; const skips = [];
    hs.forEach(h => { const l = +(h.getAttribute('aria-level') || h.tagName[1]); if (last && l > last + 1) skips.push(`h${last}->h${l} "${txt(h).slice(0, 50)}"`); if (!txt(h)) skips.push('EMPTY ' + sel(h)); if (h.closest('button,a,[role=button]')) skips.push(`heading inside interactive element: "${txt(h).slice(0, 40)}"`); last = l; });
    R.headingIssues = cap(skips); R.headingOutline = hs.slice(0, 40).map(h => h.tagName + ': ' + txt(h).slice(0, 50));
    R.imgNoAlt = cap([...document.querySelectorAll('img')].filter(i => !i.hasAttribute('alt') && !i.closest('[aria-hidden="true"]')).map(i => sel(i) + ' src=' + (i.getAttribute('src') || '').split('/').pop().slice(0, 40)));
    R.imgAltSuspect = cap([...document.querySelectorAll('img[alt]')].filter(i => /image of|picture of|photo of|\.(png|jpe?g|svg|webp|gif)$|^(img|image|logo|icon|graphic|banner|interactive map)$/i.test(i.alt.trim())).map(i => sel(i) + ' alt="' + i.alt + '"'));
    R.imgEmptyAltLarge = cap([...document.querySelectorAll('img[alt=""]')].filter(i => vis(i) && i.getBoundingClientRect().width > 150 && i.getAttribute('src')).map(i => sel(i) + ' ' + Math.round(i.getBoundingClientRect().width) + 'px (confirm decorative)'));
    R.svgImgNoName = cap([...document.querySelectorAll('svg[role=img]')].filter(s => !s.closest('[aria-hidden="true"]') && s.getAttribute('aria-hidden') !== 'true' && !name(s)).map(sel));
    const emptyL = [], vague = [], hash = [], newWin = [], emptyB = [];
    document.querySelectorAll('a[href]').forEach(a => { if (a.closest('[aria-hidden="true"]')) return; const n = name(a); if (!n) emptyL.push(sel(a) + ' href=' + a.getAttribute('href') + (vis(a) ? '' : ' (hidden)')); if (/^(read more|more|click here|here|learn more|find out more|view|view more|details|link|download|continue)$/i.test(n)) vague.push(n + ' -> ' + a.getAttribute('href')); if (a.getAttribute('href') === '#') hash.push(n + ' role=' + (a.getAttribute('role') || 'link') + ' aria-expanded=' + a.getAttribute('aria-expanded')); if (a.target === '_blank' && !/new (tab|window)|opens/i.test(n)) newWin.push(n.slice(0, 50) + ' -> ' + a.getAttribute('href').slice(0, 60)); });
    document.querySelectorAll('button,[role=button],[role=link],[role=tab],[role=menuitem],[role=switch],[role=checkbox]').forEach(b => { if (!b.closest('[aria-hidden="true"]') && !name(b)) emptyB.push(sel(b) + (vis(b) ? '' : ' (hidden)') + (b.disabled ? ' (disabled)' : '')); });
    R.linksNoName = cap(emptyL); R.controlsNoName = cap(emptyB); R.vagueLinks = cap(vague); R.hashLinks = cap(hash); R.newWindowNoWarning = cap(newWin);
    const fields = [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image]),select,textarea,[role=combobox],[role=textbox],[role=searchbox]')].filter(vis);
    R.fieldsNoLabel = cap(fields.filter(f => { const lbl = f.getAttribute('aria-labelledby') ? byIds(f.getAttribute('aria-labelledby')) : ''; return !lbl && !f.getAttribute('aria-label') && !(f.labels && f.labels.length) && !f.title; }).map(f => sel(f) + ' placeholder="' + (f.placeholder || '') + '"'));
    R.fieldLabelMismatch = cap(fields.filter(f => { const ph = (f.placeholder || '').trim().toLowerCase(); const n = name(f).toLowerCase(); return n && ph && !n.includes(ph.slice(0, 10)) && !(f.labels && f.labels.length); }).map(f => sel(f) + ` name="${name(f)}" visible placeholder="${f.placeholder}"`));
    R.autocompleteMissing = cap(fields.filter(f => /^(email|tel)$/.test(f.type) || /(^|[-_])(e?mail|phone|tel|first.?name|last.?name|surname|full.?name|postcode|zip|address)/i.test((f.name || '') + ' ' + (f.id || ''))).filter(f => !f.getAttribute('autocomplete') || f.getAttribute('autocomplete') === 'off').map(sel));
    const ids = {}; document.querySelectorAll('[id]').forEach(e => { ids[e.id] = (ids[e.id] || 0) + 1; });
    R.duplicateIds = cap(Object.keys(ids).filter(k => ids[k] > 1));
    R.positiveTabindex = cap([...document.querySelectorAll('[tabindex]')].filter(e => +e.getAttribute('tabindex') > 0).map(sel));
    R.focusableInsideAriaHidden = cap([...document.querySelectorAll('[aria-hidden="true"]')].flatMap(h => [...h.querySelectorAll(FOCUSABLE)]).filter(e => !e.disabled && e.tabIndex >= 0 && getComputedStyle(e).visibility !== 'hidden' && getComputedStyle(e).display !== 'none').map(sel));
    R.clickableNonSemantic = cap([...document.querySelectorAll('div,span,li,img,svg,p,td')].filter(e => getComputedStyle(e).cursor === 'pointer' && !e.closest('a,button,label,summary,[role],[tabindex]') && vis(e) && !(e.parentElement && getComputedStyle(e.parentElement).cursor === 'pointer')).map(e => sel(e) + ' "' + txt(e).slice(0, 30) + '"'));
    R.customRoleTabindex = cap([...document.querySelectorAll('[role=button][tabindex],[role=checkbox][tabindex],[role=link][tabindex],span[tabindex="0"],div[tabindex="0"]')].filter(e => !/^(A|BUTTON|INPUT)$/.test(e.tagName)).map(e => sel(e) + ' role=' + e.getAttribute('role') + ' "' + name(e).slice(0, 40) + '"'));
    R.expandableNoState = cap([...document.querySelectorAll('[data-bs-toggle=collapse],[data-bs-toggle=dropdown],[aria-controls],[aria-haspopup]')].filter(e => vis(e) && !e.hasAttribute('aria-expanded') && e.getAttribute('role') !== 'combobox').map(e => sel(e) + ' "' + name(e).slice(0, 30) + '"'));
    R.tooltipTriggers = document.querySelectorAll('[data-bs-toggle=tooltip],[data-toggle=tooltip],[data-tooltip],[data-tippy-content]').length;
    R.iframes = cap([...document.querySelectorAll('iframe')].map(f => (f.title || 'NO TITLE') + ' ' + (f.src || '').slice(0, 60)));
    R.media = cap([...document.querySelectorAll('video,audio')].map(v => v.tagName + ' captions=' + v.querySelectorAll('track[kind=captions],track[kind=subtitles]').length + ' autoplay=' + v.autoplay + ' controls=' + v.controls + ' muted=' + v.muted));
    R.liveRegions = [...document.querySelectorAll('[aria-live],[role=status],[role=alert],[role=log]')].length;
    R.langParts = document.querySelectorAll('body [lang]').length;
    const low = [], manual = [], seen = new Set();
    document.querySelectorAll('body *').forEach(e => {
      if (!vis(e) || srOnly(e) || /^(SCRIPT|STYLE|NOSCRIPT|svg|path)$/i.test(e.tagName)) return;
      if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
      const s = getComputedStyle(e); const bg = bgOf(e);
      if (bg.image) { if (manual.length < 15) manual.push(`"${txt(e).slice(0, 40)}" ${sel(e)} (text over image: check manually)`); return; }
      const fg = P(s.color); const f = fg[3] < 1 ? fg.slice(0, 3).map((v, i) => v * fg[3] + bg.c[i] * (1 - fg[3])) : fg;
      const r = ratio(f, bg.c); const px = parseFloat(s.fontSize), w = parseInt(s.fontWeight, 10);
      const large = px >= 24 || (px >= 18.66 && w >= 700); const need = large ? 3 : 4.5;
      const disabled = e.closest('[disabled],[aria-disabled="true"]');
      if (r < need && !disabled) { const k = s.color + '|' + bg.c.map(Math.round) + '|' + px; if (seen.has(k)) return; seen.add(k); low.push(`${r.toFixed(2)}:1 (needs ${need}) "${txt(e).slice(0, 40)}" ${sel(e)} fg=${s.color} bg=rgb(${bg.c.map(Math.round)}) ${px}px/${w}`); }
    });
    R.textContrastFails = cap(low, 25); R.contrastManual = cap(manual);
    const small = [];
    foc.forEach(e => { const r = e.getBoundingClientRect(); if (r.width >= 24 && r.height >= 24) return; if (e.tagName === 'A' && getComputedStyle(e).display === 'inline') { const pt = txt(e.parentElement || e); if (pt.length > txt(e).length + 15) return; } small.push(`${Math.round(r.width)}x${Math.round(r.height)} "${name(e).slice(0, 30)}" ${sel(e)}`); });
    R.smallTargets = cap(small, 25);
    const cw = de.clientWidth, sw = de.scrollWidth;
    R.horizontalScroll = sw > cw + 1 ? `scrollWidth ${sw} > clientWidth ${cw}` : false;
    const over = [...document.querySelectorAll('body *')].filter(e => { if (!vis(e) || e.closest('svg')) return false; const r = e.getBoundingClientRect(); return r.right > cw + 2 && r.width < 4000; });
    R.overflowingElements = cap(over.filter(e => !over.some(o => o !== e && e.contains(o))).map(e => sel(e) + ' right=' + Math.round(e.getBoundingClientRect().right) + ' "' + txt(e).slice(0, 40) + '"'));
    R.clipped = cap(A.clipped());
    return R;
  };

  A.clipped = () => [...document.querySelectorAll('body *')].filter(e => {
    if (!vis(e) || srOnly(e) || e.closest('[class*="visually-hidden"],[class*="sr-only"]')) return false;
    const s = getComputedStyle(e);
    if (!/hidden|clip/.test(s.overflow + s.overflowX + s.overflowY) && s.textOverflow !== 'ellipsis' && !/-webkit-box/.test(s.display)) return false;
    return (e.scrollHeight > e.clientHeight + 2 || e.scrollWidth > e.clientWidth + 2) && txt(e).length > 0 && e.clientHeight > 0;
  }).filter((e, i, a) => !a.some(o => o !== e && o.contains(e)))
    .map(e => `${sel(e)} "${txt(e).slice(0, 40)}" content ${e.scrollWidth}x${e.scrollHeight} in box ${e.clientWidth}x${e.clientHeight}` + (() => { const r = e.getBoundingClientRect(); const lost = [...e.querySelectorAll('a,button,input')].filter(c => { const q = c.getBoundingClientRect(); return q.top >= r.bottom - 2 || q.left >= r.right - 2; }).map(c => name(c).slice(0, 30)); return lost.length ? ' HIDDEN CONTROLS: ' + lost.join(', ') : ''; })());

  A.spacing = on => { let s = document.getElementById('__a11y_ts'); if (on && !s) { s = document.createElement('style'); s.id = '__a11y_ts'; s.textContent = '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}'; document.head.appendChild(s); } if (!on && s) s.remove(); return on ? 'text spacing ON' : 'text spacing OFF'; };

  A.sticky = async (scrollToMiddle = true) => {
    const de = document.documentElement;
    if (scrollToMiddle) { const pb = document.body.style.scrollBehavior, ph = de.style.scrollBehavior; de.style.scrollBehavior = document.body.style.scrollBehavior = 'auto'; window.scrollTo(0, Math.max(0, (de.scrollHeight - de.clientHeight) / 2)); await new Promise(r => setTimeout(r, 400)); de.style.scrollBehavior = ph; document.body.style.scrollBehavior = pb; }
    const vh = de.clientHeight, cw = de.clientWidth, row = new Array(vh).fill(0);
    const els = [...document.querySelectorAll('body *')].filter(e => { const p = getComputedStyle(e).position; return (p === 'fixed' || p === 'sticky') && vis(e); });
    const list = els.map(e => { const r = e.getBoundingClientRect(); if (r.width >= cw * 0.5) for (let y = Math.max(0, Math.floor(r.top)); y < Math.min(vh, r.bottom); y++) row[y] = 1; return `${sel(e)} ${getComputedStyle(e).position} y=${Math.round(r.top)}..${Math.round(r.bottom)} w=${Math.round(r.width)}`; });
    const covered = row.reduce((a, b) => a + b, 0);
    return { viewport: cw + 'x' + vh, coveredPct: Math.round(100 * covered / vh), visibleContentPx: vh - covered, elements: list.slice(0, 10), scrollPaddingTop: getComputedStyle(de).scrollPaddingTop };
  };

  A.obscured = async (rootSelector = 'body') => {
    const de = document.documentElement, prev = [de.style.scrollBehavior, document.body.style.scrollBehavior]; de.style.scrollBehavior = document.body.style.scrollBehavior = 'auto';
    const root = document.querySelector(rootSelector) || document.body;
    const foc = [...root.querySelectorAll(FOCUSABLE)].filter(e => !e.disabled && vis(e));
    const hidden = []; let tested = 0;
    for (let i = foc.length - 1; i >= 0; i--) {
      const e = foc[i]; e.focus(); await new Promise(r => setTimeout(r, 20)); if (document.activeElement !== e) continue; tested++;
      const r = e.getBoundingClientRect();
      const pts = [[r.left + r.width / 2, r.top + r.height / 2], [r.left + 2, r.top + 2], [r.right - 2, r.bottom - 2]];
      const covered = pts.every(([x, y]) => { const h = document.elementFromPoint(x, y); return !(h && (h === e || e.contains(h) || h.contains(e))); });
      if (covered) { const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); hidden.push(`"${name(e).slice(0, 30)}" ${sel(e)} covered by ${h ? sel(h) : 'nothing (offscreen)'}`); }
    }
    document.activeElement?.blur(); [de.style.scrollBehavior, document.body.style.scrollBehavior] = prev;
    return { tested, fullyHidden: hidden.length, samples: hidden.slice(0, 10), note: 'Reverse (Shift+Tab-like) pass. Confirm at least one sample with real Shift+Tab and a screenshot.' };
  };

  A.focusRules = () => {
    const out = [];
    const walk = rules => { for (const r of rules) { if (r.cssRules && !r.selectorText) walk(r.cssRules); if (r.selectorText && /:focus/.test(r.selectorText) && /(outline|box-shadow)/.test(r.cssText)) out.push(r.cssText.replace(/\s+/g, ' ').slice(0, 220)); } };
    for (const ss of document.styleSheets) { try { walk(ss.cssRules); } catch (e) { out.push('(cross-origin stylesheet not readable: ' + (ss.href || '') + ')'); } }
    const root = getComputedStyle(document.documentElement);
    const vars = {}; out.join(' ').match(/--[\w-]+/g)?.forEach(v => { vars[v] = root.getPropertyValue(v).trim(); });
    return { rules: out.slice(0, 40), customProperties: vars };
  };

  A.focusNow = () => { const e = document.activeElement; if (!e || e === document.body) return 'focus on BODY'; const s = getComputedStyle(e); const bg = bgOf(e.parentElement || e); return { element: sel(e), name: name(e).slice(0, 50), outline: s.outline, boxShadow: s.boxShadow, ringVsBackground: s.outlineStyle !== 'none' && !bg.image ? A.contrast(s.outlineColor, 'rgb(' + bg.c.join(',') + ')') : 'n/a' }; };

  window.__a11y = A;
  return 'a11y kit loaded: __a11y.scan(), await .sticky(), .spacing(true|false), .clipped(), await .obscured(sel), .focusRules(), .focusNow(), .contrast(fg,bg)';
})();
```

**Kit reference**

| Call | Returns |
| --- | --- |
| `__a11y.scan()` | title, lang, landmarks, skip link, heading outline and issues, image alt problems, unnamed links/controls, vague/`#`/new-window links, unlabelled fields, label/placeholder mismatch, missing `autocomplete`, duplicate IDs, positive tabindex, focusable inside `aria-hidden`, clickable non-semantic elements, custom-role widgets, expandables without `aria-expanded`, tooltip count, iframes, media, live-region count, text contrast failures (+ text over images to check by eye), small targets, horizontal scroll and overflowing elements, clipped content |
| `await __a11y.sticky()` | % of the viewport covered by fixed/sticky UI (measured mid-page), visible content height, `scroll-padding-top` |
| `__a11y.spacing(true/false)` | Applies or removes the WCAG 1.4.12 text-spacing overrides |
| `__a11y.clipped()` | Containers clipping content, including any controls that become hidden |
| `await __a11y.obscured('main')` | Reverse focus pass: controls fully hidden when focused, and what covers them |
| `__a11y.focusRules()` | CSS `:focus` / `:focus-visible` rules and the custom properties they use, for root-causing focus issues |
| `__a11y.focusNow()` | The focused element's outline/box-shadow and ring-to-background contrast (use after a real Tab press) |
| `__a11y.contrast(fg, bg)` | Contrast ratio of two CSS colours |

---

## Optional: comparing independent runs

To see whether results are repeatable, run this prompt **two or more times in separate, fresh sessions**, without giving any run the earlier reports. Then, in a new session, attach the reports and paste:

> Merge these independent accessibility audit reports of the same site into one. Match issues by component and behaviour, not by ID or wording. Keep the clearest description, the most specific evidence and the best remediation. Add a "Seen in" column showing how many runs found each issue (e.g. 2/3). List issues found in only one run separately under "Needs confirmation", and re-test those in the browser before keeping them. Keep the report template and severity rubric unchanged.
