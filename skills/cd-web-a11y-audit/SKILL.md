---
name: cd-web-a11y-audit
description: Audit a live website for accessibility against WCAG 2.2 AA by driving a real browser (keyboard, zoom, reflow, text spacing, contrast, screen sizes) and write an evidence-based report with severity, WCAG reference, page, viewport and fix for each issue. Use when asked for an accessibility audit, WCAG or a11y check, or accessibility report of a website or URL.
metadata:
  version: "1.0.0"
---

# Web accessibility audit (WCAG 2.2 AA, live browser)

Audit the site the user names by **driving a real browser**: loading pages, resizing the viewport, pressing keys, hovering, opening menus and measuring the rendered page. Then write a report a development team can act on.

Files in this skill (paths relative to this folder):

| File | Use it for |
| --- | --- |
| `scripts/a11y-kit.js` | The in-page test script. Read the file and run its **entire contents** as one JavaScript evaluation in each page. |
| `references/checklist.md` | The WCAG 2.2 AA criteria: what to test and what passes. Read it before Phase 3. |
| `references/browser-tools.md` | How to map each action onto Claude or Antigravity browser tools. Read it first. |
| `assets/report-template.md` | Report structure and how to write each finding. Read it before Phase 6. |

## Show that this skill is in use (required)

So the team can see which skill produced a result:

1. **First line of your first reply:** `Skill: cd-web-a11y-audit v1.0.0`, on its own line, then one sentence on what you're about to do.
2. **Report byline:** include `skill: cd-web-a11y-audit v1.0.0` (the template already has a slot for it).
3. **Final message:** end with `Skill: cd-web-a11y-audit v1.0.0`.

If you are only partly following this skill (for example the user asked for just one check), still add the stamp and say which parts you ran.

## 1. Read the request (don't make the user fill in a form)

Take what you need from the user's message and use these defaults for the rest. Ask a question **only** if there is no URL. Write the values you used under "Scope and method" in the report.

| Setting | Default | Change it when the request says… |
| --- | --- | --- |
| Target URL | none (required) | the URL given |
| Scope | Up to 15 representative pages: one per template, plus key journeys | specific pages, sections or journeys, or "whole site" |
| Exclude | nothing | paths to avoid, e.g. "skip /admin" |
| Login | none: public pages only | the user will sign in for you. Ask them to do it in the browser; never take passwords in chat. |
| Forms may be submitted | no | named forms, which use obviously fake data |
| Extra guidance | none | an attached checklist, brand guide or design-system notes. Apply it on top of WCAG 2.2 AA. |
| Report file | `reports/a11y-audit-<domain>-<YYYY-MM-DD>.md` | a different path or format |
| Evidence folder | `reports/evidence/a11y-<domain>-<YYYY-MM-DD>/` | a different path |

If your environment has a better place for a shareable report (a document or artifact the user can open), you may publish there as well. The Markdown file stays the default.

## 2. Rules (non-negotiable)

1. **Live browser only.** Every finding must come from the rendered site in a browser you control. Source code, raw HTML from a plain HTTP fetch, or a repo is **not** an audit. Single-page apps often return an empty shell without JavaScript. If you have no browser tool, or the browser cannot load the site, **stop and tell the user**. Never produce a report from code or memory.
2. **Evidence for every finding:** a screenshot path, a measured value (for example contrast ratio, size, `scrollWidth`) or the exact key sequence and what happened.
3. **Confirm before reporting.** Kit results are leads. Confirm each one by looking or by a second measurement. Real key presses beat scripted `.focus()`, which does not show `:focus-visible`.
4. **Do no harm.**
   - No form submissions unless allowed.
   - No accounts, purchases, messages or settings changes.
   - No real personal data or credentials.
5. **Cookie banners.** Record their accessibility. Then choose "Reject all / necessary only", or hide the banner with CSS. Never accept on the user's behalf.
6. **Bot protection.** On a 403, CAPTCHA or challenge, **do not evade** it: no user-agent spoofing, proxies or stealth plugins. Switch to a browser the user controls, or stop and report the block.
7. **Stay in scope.** Don't browse off the target domain.
8. **State what you couldn't test**, for example screen readers, PDFs, other browsers, pages behind login.

## 3. Test matrix

Run every template at **Desktop**. Run the reflow, zoom, landscape and text-spacing rows on at least the home page, one content-heavy page, one search or form page, and every page with sticky or fixed UI.

| Label | Viewport (CSS px) | Criterion |
| --- | --- | --- |
| Desktop | 1280 × 800 | Baseline |
| Tablet | 768 × 1024 | Breakpoint |
| Mobile | 375 × 812 | Phone portrait |
| Landscape | 812 × 375 | 1.3.4 Orientation, short screens |
| 200% zoom | 640 × 400 | 1.4.4 Resize text |
| 400% zoom | 320 × 256, then 320 × 640 | 1.4.10 Reflow |
| Text spacing | Mobile and Desktop, with `__a11y.spacing(true)` | 1.4.12 |

Record the real size you got (`document.documentElement.clientWidth/clientHeight`). Compare `scrollWidth` with `clientWidth`, not `innerWidth`, because mobile emulation widens the layout viewport when content overflows.

## 4. Procedure

**Phase 1: Discover.**
1. Load the URL. Note the title, `lang`, the framework and whether it is an SPA.
2. Build the page list: nav, footer, `/sitemap.xml`, in-page links. Take one page per template, plus home, listing, detail, search results, a form, the 404, and the accessibility statement, cookie and privacy pages.
3. List the interactive components: menus, dropdowns, accordions, tabs, modals, carousels, tooltips, maps, filters, search, pagination, media, cookie banner.

**Phase 2: Automated scan** (each page × required viewports). Inject `scripts/a11y-kit.js`, then:
- `__a11y.scan()`: save the JSON.
- `await __a11y.sticky()` at Desktop, 200% zoom, Landscape and 400% zoom. If `coveredPct` is above about 40%, or `visibleContentPx` is under about 150, it's a problem: screenshot it.
- `__a11y.spacing(true)`, then `__a11y.clipped()` at Mobile and Desktop. Any result listing **HIDDEN CONTROLS** fails 1.4.12. Screenshot it, then run `__a11y.spacing(false)`.
- `await __a11y.obscured('main')` (or `'body'`) on pages with sticky UI. Confirm one sample with real Shift+Tab and a screenshot.
- `__a11y.focusRules()` once, to find the CSS behind focus styles.
- Optional: if the page's CSP allows, inject axe-core (`https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js`) and run `axe.run({runOnly:['wcag2a','wcag2aa','wcag21aa','wcag22aa']})`. Treat the results as extra leads.

In SPAs, state survives in-app navigation, so inject once and move with in-app links or the router. Re-inject after any full page load.

**Phase 3: Interactive checks** (real input). Follow the "Interactive checks" list in `references/checklist.md`:
- keyboard walk
- menus and disclosures
- dialogs and cookie banner
- hover/focus content
- forms
- search, filters and pagination
- SPA route changes
- motion, media and timing
- pointer and drag
- orientation
- consistency
- authentication

Use `__a11y.focusNow()` after real Tab presses to get the ring contrast and to see where focus went after a route change.

**Phase 4: Triage.**
- **Merge duplicates.** One component failing on many pages is **one site-wide issue** that lists those pages.
- **Ignore known false positives:**
  - `.sr-only` / `.visually-hidden` text counted as clipped
  - `svg role="img"` with `aria-hidden`
  - decorative `alt=""`
  - scripted focus not showing `:focus-visible`
- **Check text over images by eye.**
- **Assign severity and IDs.** Use the rubric below. IDs are `SW-01` for site-wide, then a short prefix per page (`HM-01` home, `PR-01` product…).

| Severity | Use when |
| --- | --- |
| Critical | Blocks a core task for a group of users at a common setting. Examples: unreachable by keyboard, content fully covered at 200% zoom, keyboard trap, a modal that can't be closed. |
| High | A clear WCAG A/AA failure with a significant barrier. Examples: unnamed key control, failed text contrast on core content, no page titles, reflow failure on main content, hover content that can't be dismissed. |
| Medium | A WCAG A/AA failure with a workaround or limited reach. Examples: heading skips, missing `aria-expanded`, weak focus ring, unannounced status messages, buttons used as navigation. |
| Low | Best practice, AAA, or a borderline pass. Examples: new tab without warning, 22px targets passing via spacing, verbose names. |

**Phase 5: Verify.**
1. Re-test **every** issue on a fresh page load at the viewport where it was found, using the targeted check or interaction that proves it.
2. Drop anything you can't reproduce, or mark it **Unconfirmed** with the reason.
3. Correct details or root causes the re-test changes.
4. In the report, say this was a re-test of known issues, not an independent second audit.

**Phase 6: Report.**
1. Read `assets/report-template.md`.
2. Write the report file and save screenshots in the evidence folder.
3. Tell the user, in two or three sentences: the verdict, the counts by severity, and the top fixes. Then give the report location.

## 5. Independent runs (only if asked)

If the user wants to know whether results repeat, explain that each run must happen in a **separate, fresh session** that hasn't seen earlier reports. Then merge the reports by component and behaviour. Add a "Seen in" column (e.g. 2/3), and re-test single-run findings before keeping them. A re-test inside one session is validation, not an independent run.
