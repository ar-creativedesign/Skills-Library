# Browser tools: Claude and Antigravity

Work out which browser you have, then map each action onto its tools.

| Action | Claude in Chrome / Claude desktop built-in browser | Claude Code (terminal) | Antigravity browser subagent |
| --- | --- | --- | --- |
| Open page | `navigate` | Playwright MCP `browser_navigate`, or a headed Playwright script | `browser_navigate` / `open_browser_url` |
| Run page JavaScript | `javascript_tool` | `browser_evaluate` / `page.evaluate` | `execute_browser_javascript` |
| Screenshot | `computer` → screenshot / zoom | `browser_take_screenshot` | `capture_browser_screenshot` (interactions are also recorded automatically) |
| Resize viewport | `resize_window` (custom sizes or presets) | `browser_resize` / `setViewportSize` | `browser_resize_window` |
| Key presses (Tab, Shift+Tab, Enter, Space, Escape, arrows) | `computer` → key | `browser_press_key` / `keyboard.press` | `browser_press_key` |
| Hover / click | `computer` → hover / left_click | `browser_hover` / `browser_click` | `browser_click_element`; hover via JavaScript if no hover tool |
| Read structure | `read_page` / `get_page_text` | `browser_snapshot` (accessibility tree) | `read_browser_page` |
| Network / console | `read_network_requests` / `read_console_messages` | `browser_network_requests` / `browser_console_messages` | `performance.getEntriesByType('resource')` via JavaScript |

Tool names change between releases. If a name here doesn't exist, use the equivalent tool you do have.

## Notes

- **Running the kit:** read the kit file from this skill's `scripts/` folder and pass its **entire contents** as one JavaScript evaluation. It defines a global (`window.__a11y` or `window.__sec`) and returns a confirmation string. `await` the async calls.
- **Antigravity:** the main agent hands browser work to the browser subagent, which may not see this skill. Put the exact steps, the viewport size and the **full kit script** into each delegated task, and ask for the JSON results and screenshot paths back.
- **Terminal only:** use headed Chromium via Playwright (`npx playwright` or Python) and save screenshots to the output folder's `evidence/`. If the site blocks automated browsers, don't evade it; ask the user to use their own browser.
- **Per-site permission prompts:** some browsers ask the user before each page load. Prefer in-app navigation in SPAs to keep prompts down. Ask the user to choose "always allow" for the target site if they're watching.
- **Window vs viewport:** if your tool resizes the window rather than the viewport, check the real size with `document.documentElement.clientWidth/clientHeight` and record it.
