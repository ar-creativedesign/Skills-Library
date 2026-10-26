"""Runs scripts/code_scan.py against code-fixture/, a small Vue app with deliberate accessibility faults."""
import importlib.util


def run(skill, check):
    spec = importlib.util.spec_from_file_location("a11y_code_scan", skill / "scripts/code_scan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    res = mod.scan(str(skill.parent.parent / "tests" / skill.name / "code-fixture"), 25)
    rules = {r["rule"] for r in res["results"]}
    for rid in ["IMG_NO_ALT", "CLICK_ON_NON_INTERACTIVE", "FOCUS_OUTLINE_REMOVED", "VIEWPORT_ZOOM_BLOCKED", "HTML_NO_LANG",
                "INPUT_PLACEHOLDER_ONLY", "SPA_NO_TITLE_UPDATE", "SPA_NO_FOCUS_MANAGEMENT", "POSITIVE_TABINDEX",
                "ARIA_LABEL_LITERAL_SUSPECT", "HREF_HASH", "HEADING_INSIDE_INTERACTIVE", "FIXED_HEIGHT_OVERFLOW_HIDDEN",
                "TOOLTIP_LIBRARY", "NO_SKIP_LINK", "NO_MAIN_LANDMARK", "WORD_BREAK", "NAV_VIA_BUTTON", "STICKY_OR_FIXED",
                "GLOBAL_FOCUS_STYLE", "VISUALLY_HIDDEN_NOISE"]:
        check(rid in rules, f"a11y code: {rid} detected")
