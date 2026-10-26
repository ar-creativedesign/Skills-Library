"""Runs scripts/a11y-kit.js against fixture.html, a page with deliberate accessibility faults."""


def run(browser, base, skill, check):
    kit = (skill / "scripts/a11y-kit.js").read_text(encoding="utf-8")
    pg = browser.new_page(viewport={"width": 640, "height": 400})
    pg.goto(f"{base}/fixture.html")
    pg.evaluate(kit)
    r = pg.evaluate("__a11y.scan()")
    check(r["imgNoAlt"]["count"] == 1, "a11y: missing alt detected")
    check(r["textContrastFails"]["count"] >= 1, "a11y: low contrast detected")
    check(bool(r["horizontalScroll"]), "a11y: horizontal scroll detected")
    check(r["fieldsNoLabel"]["count"] == 1, "a11y: unlabelled field detected")
    check(any("HIDDEN CONTROLS" in c for c in r["clipped"]["samples"]), "a11y: clipped control detected")
    check(any("inside interactive" in h for h in r["headingIssues"]["samples"]), "a11y: heading inside button detected")
    check(pg.evaluate("__a11y.sticky()")["coveredPct"] >= 50, "a11y: sticky coverage measured")
    check(pg.evaluate("__a11y.obscured()")["fullyHidden"] >= 1, "a11y: obscured focus detected")
    check(any("ffd800" in x.lower() or "255, 216, 0" in x for x in pg.evaluate("__a11y.focusRules()")["rules"]), "a11y: focus rule found")
    pg.close()
