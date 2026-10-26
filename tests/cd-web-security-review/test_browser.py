"""Runs scripts/sec-kit.js against fixture.html (+ a generated app.js), a page with deliberate security weaknesses."""
import re


def run(browser, base, skill, check):
    kit = (skill / "scripts/sec-kit.js").read_text(encoding="utf-8")
    here = skill.parent.parent / "tests" / skill.name
    (here / "app.js.map").write_text('{"version":3}')
    # Fake secrets are assembled at test time so no secret-shaped literal is committed
    # (GitHub push protection rightly blocks those).
    fake_stripe = "sk_" + "live_" + "51Habcdefghijklmnopqrstuv" + "WXYZ"
    (here / "app.js").write_text(
        'var cfg = { endpoint: "https://api-eu-west-2.graphcms.com/v2/abc/master", client_secret: "' + fake_stripe + '" };\n'
        "console.log(cfg);\n//# sourceMappingURL=app.js.map\n"
    )
    pg = browser.new_page()
    pg.goto(f"{base}/fixture.html")
    pg.evaluate(kit)
    s = pg.evaluate("__sec.scan()")
    check(s["possibleSecrets"]["count"] >= 3, "sec: possible secrets detected")
    check(not any(re.search(r"sk_live_\w{20,}|eyJ[\w-]{20,}\.eyJ", x) for x in s["possibleSecrets"]["samples"]), "sec: secrets are redacted")
    check(s["webStorage"]["count"] == 1 and "TOKEN-LIKE" in s["webStorage"]["samples"][0], "sec: token in localStorage detected")
    check(any(f["passwordOverGET"] for f in s["forms"]), "sec: password over GET detected")
    check(s["sessionLikeCookiesVisibleToJS"] == ["sessionid"], "sec: JS-readable session cookie detected")
    check(len(s["blankTargetsWithoutNoopener"]["samples"]) == 1, "sec: target=_blank without noopener detected")
    check(any("graphcms" in e for e in s["endpointsInBundles"]), "sec: API endpoint in bundle detected")
    csp = pg.evaluate("__sec.csp()")["issues"]
    check(any("localhost" in i for i in csp) and any("unsafe-eval" in i for i in csp), "sec: CSP weaknesses detected")
    maps = pg.evaluate("(u)=>__sec.sourceMapsExposed(u)", s["sourceMapReferences"]["samples"])
    check(any("200" in m for m in maps), "sec: exposed source map detected")
    pg.close()
    (here / "app.js.map").unlink(missing_ok=True)
    (here / "app.js").unlink(missing_ok=True)
