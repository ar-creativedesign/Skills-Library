# WCAG 2.2 AA checklist for live-browser audits

Used by `SKILL.md`. "scan()", "sticky()" etc. refer to the functions defined by `scripts/a11y-kit.js`.

## Interactive checks (real input, not scripts)

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
12. **Authentication (3.3.8)** if login is in scope. Check for no cognitive tests without an alternative, paste allowed, and password managers working.

## Criteria: what to test and what passes

Process items (accessibility in the definition of done, design annotations, a WCAG 2.2 AA target in the backlog) can't be checked in a browser. Mention them only if the user’s extra guidance gives you documents to check.

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
| Keyboard (2.1.1, 2.1.4) | Interactive checks 1–4 | Everything works by keyboard; custom widgets respond to Enter/Space/arrows/Escape as their pattern expects; single-key shortcuts can be turned off or remapped |
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
| On focus, on input; hover/focus content (3.2.1, 3.2.2, 1.4.13) | Focus and change controls; Interactive check 4 | No unexpected context change; extra content is dismissible, hoverable and persistent |
| Consistent navigation, identification, help (3.2.3, 3.2.4, 3.2.6) | Compare templates | Same order and names; help in the same place |
| Redundant entry (3.3.7) | Multi-step flows | Information already given is filled in or selectable |
| Accessible authentication (3.3.8) | Login, if in scope | No cognitive function test without an alternative; paste and password managers allowed |

### Robust

| Item (WCAG) | Test in the browser | Passes when |
| --- | --- | --- |
| Name, role, value (4.1.2) | `controlsNoName`, `customRoleTabindex`, `expandableNoState`, `clickableNonSemantic`, `focusableInsideAriaHidden`, `duplicateIds`; Interactive checks 2–3 | Native elements where possible; custom widgets expose correct role, name and state (`aria-expanded`, `aria-checked`, `aria-current`); links navigate, buttons act |
| Label in name (2.5.3) | `fieldLabelMismatch`; compare visible text with `aria-label` | The accessible name contains the visible label text, ideally at the start |
| Input purpose (1.3.5) | `autocompleteMissing` | Personal-data fields have correct `autocomplete` tokens |
| Status messages (4.1.3) | Search, filters, cart, form success, pagination; `scan().liveRegions` | Announced through `role=status`/`alert` or `aria-live` without moving focus |
| Assistive tech compatibility | Note as not tested unless you have a screen reader | List as a limitation; recommend NVDA and VoiceOver checks |

## Kit reference

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
