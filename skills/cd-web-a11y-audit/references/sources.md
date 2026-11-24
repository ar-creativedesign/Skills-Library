# Official sources (accessibility)

The checklist in this skill is self-contained, so audits work without web access. Use these sources to:

1. **Check standards are current** at the start of a run (SKILL.md Phase 0).
2. **Link every finding** to the official explanation in the report's **Reference** column.
3. **Resolve doubt.** When unsure whether something fails, read the Understanding page and its sufficient techniques and failures before deciding.

Sources last reviewed: 2026-10-26.

## Standards status (as of the date above)

| Standard | Status | What we use it for |
| --- | --- | --- |
| [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | Current W3C Recommendation | The audit target: Level A + AA |
| [WCAG 3.0](https://www.w3.org/TR/WCAG3/) | Working Draft (latest seen: March 2026). **Not** a standard yet. | Watch only. Don't audit against it. Mention it if the user asks about future-proofing. |
| EN 301 549 v4.1.1 | Published September 2026. Adopts WCAG 2.2 AA for web content. Expected to become the European Accessibility Act harmonised standard around the end of November 2026. | The legal basis for EU/EAA conformance claims ([summary](https://www.deque.com/blog/en-301-549-v4-1-1-is-final-what-changed-what-it-means-and-what-you-should-do/)) |
| UK Public Sector Bodies Accessibility Regulations 2018 | In force. GOV.UK guidance points public sector sites to WCAG 2.2 AA. | Public-sector sites need an accessibility statement and must meet WCAG 2.2 AA ([sample statement guidance](https://guidance.publishing.service.gov.uk/accessibility-statement)) |
| Equality Act 2010 | In force | Duty to make reasonable adjustments, for all UK service providers |

**Standards check (Phase 0):** if you can search the web, confirm:
- WCAG 2.2 is still the latest Recommendation, and WCAG 3.0 is still a draft
- the current EN 301 549 version

If anything has changed, say so in the report's Scope section and tell the user. Don't silently switch target.

## WCAG 2.2: per-criterion links

- **Understanding pages** explain intent, examples and how to test: `https://www.w3.org/WAI/WCAG22/Understanding/<slug>.html`
- **Techniques index:** https://www.w3.org/WAI/WCAG22/Techniques/
- **Quick Reference** (filterable): https://www.w3.org/WAI/WCAG22/quickref/

| SC | Slug | SC | Slug |
| --- | --- | --- | --- |
| 1.1.1 | `non-text-content` | 2.4.1 | `bypass-blocks` |
| 1.2.1 | `audio-only-and-video-only-prerecorded` | 2.4.2 | `page-titled` |
| 1.2.2 | `captions-prerecorded` | 2.4.3 | `focus-order` |
| 1.2.3 | `audio-description-or-media-alternative-prerecorded` | 2.4.4 | `link-purpose-in-context` |
| 1.2.4 | `captions-live` | 2.4.5 | `multiple-ways` |
| 1.2.5 | `audio-description-prerecorded` | 2.4.6 | `headings-and-labels` |
| 1.3.1 | `info-and-relationships` | 2.4.7 | `focus-visible` |
| 1.3.2 | `meaningful-sequence` | 2.4.11 | `focus-not-obscured-minimum` |
| 1.3.3 | `sensory-characteristics` | 2.5.1 | `pointer-gestures` |
| 1.3.4 | `orientation` | 2.5.2 | `pointer-cancellation` |
| 1.3.5 | `identify-input-purpose` | 2.5.3 | `label-in-name` |
| 1.4.1 | `use-of-color` | 2.5.4 | `motion-actuation` |
| 1.4.2 | `audio-control` | 2.5.7 | `dragging-movements` |
| 1.4.3 | `contrast-minimum` | 2.5.8 | `target-size-minimum` |
| 1.4.4 | `resize-text` | 3.1.1 | `language-of-page` |
| 1.4.5 | `images-of-text` | 3.1.2 | `language-of-parts` |
| 1.4.10 | `reflow` | 3.2.1 | `on-focus` |
| 1.4.11 | `non-text-contrast` | 3.2.2 | `on-input` |
| 1.4.12 | `text-spacing` | 3.2.3 | `consistent-navigation` |
| 1.4.13 | `content-on-hover-or-focus` | 3.2.4 | `consistent-identification` |
| 2.1.1 | `keyboard` | 3.2.6 | `consistent-help` |
| 2.1.2 | `no-keyboard-trap` | 3.3.1 | `error-identification` |
| 2.1.4 | `character-key-shortcuts` | 3.3.2 | `labels-or-instructions` |
| 2.2.1 | `timing-adjustable` | 3.3.3 | `error-suggestion` |
| 2.2.2 | `pause-stop-hide` | 3.3.4 | `error-prevention-legal-financial-data` |
| 2.3.1 | `three-flashes-or-below-threshold` | 3.3.7 | `redundant-entry` |
| | | 3.3.8 | `accessible-authentication-minimum` |
| | | 4.1.2 | `name-role-value` |
| | | 4.1.3 | `status-messages` |

Example: 2.4.11 → https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html

## Patterns for remediation

Link these in fixes for custom widgets.

- **ARIA Authoring Practices Guide (APG):** https://www.w3.org/WAI/ARIA/apg/
  - Patterns: `https://www.w3.org/WAI/ARIA/apg/patterns/<pattern>/`, e.g. `dialog-modal`, `disclosure`, `menu-button`, `tabs`, `accordion`, `combobox`, `tooltip`, `carousel`, `listbox`, `switch`, `breadcrumb`
  - Landmarks: https://www.w3.org/WAI/ARIA/apg/practices/landmark-regions/
- **WAI-ARIA 1.2 spec:** https://www.w3.org/TR/wai-aria-1.2/
- **GOV.UK Design System:** https://design-system.service.gov.uk/. Accessible, well-tested component patterns (skip link, error summary, cookie banner, pagination).

## Method and tools

- **WCAG-EM** (how to scope and sample an evaluation): https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/
- **Easy Checks** (quick manual checks): https://www.w3.org/WAI/test-evaluate/preliminary/
- **axe-core rule descriptions:** https://dequeuniversity.com/rules/axe/
- **Accessibility statement guidance (UK):** https://guidance.publishing.service.gov.uk/accessibility-statement

## How to cite in the report

- **Reference column:** the Understanding page for each WCAG criterion broken, plus an APG pattern when the fix is a widget pattern. Example: `[2.4.11](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)`.
- **Sources section:** the standards actually used, with the date you checked they were current.
