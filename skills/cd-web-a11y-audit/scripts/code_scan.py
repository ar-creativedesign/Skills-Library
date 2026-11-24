#!/usr/bin/env python3
"""Static accessibility scan of a web codebase (Vue, React/JSX, Angular, Svelte, plain HTML, CSS/SCSS).

Produces LEADS, not findings: every hit must be confirmed by reading the code in context
(and, where possible, in the running app) before it goes in a report.

    python code_scan.py <repo-root> [--json out.json] [--max-per-rule 25]

Standard library only. Skips node_modules, build output, vendored and generated folders.
"""
import argparse
import json
import os
import re
import sys

SKIP_DIRS = {".git", "node_modules", "dist", "build", "out", ".next", ".nuxt", ".output", "coverage",
             "vendor", "bower_components", ".venv", "venv", "__pycache__", "Library", "Temp", ".cache",
             "storybook-static", "public/build"}
MARKUP = (".vue", ".html", ".htm", ".jsx", ".tsx", ".svelte", ".astro", ".hbs", ".njk", ".twig", ".cshtml", ".php")
STYLE = (".css", ".scss", ".sass", ".less", ".vue", ".svelte")
SCRIPT = (".js", ".ts", ".mjs", ".jsx", ".tsx", ".vue")
MAX_BYTES = 1_500_000
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?|mocks?|e2e)(/|$)|\.(test|spec)\.")

RULES = {
    "IMG_NO_ALT": ("1.1.1", "High", "<img> without alt / :alt"),
    "CLICK_ON_NON_INTERACTIVE": ("2.1.1, 4.1.2", "High", "Click handler on a non-interactive element without role + tabindex (keyboard users can't reach it)"),
    "ROLE_BUTTON_NO_KEY": ("2.1.1", "Medium", "role=button/link on a non-native element: check Enter/Space handling"),
    "POSITIVE_TABINDEX": ("2.4.3", "Medium", "Positive tabindex changes focus order"),
    "FOCUS_OUTLINE_REMOVED": ("2.4.7", "High", "outline: none/0 on a :focus rule (check a visible replacement exists)"),
    "VIEWPORT_ZOOM_BLOCKED": ("1.4.4", "High", "meta viewport blocks zoom (user-scalable=no / maximum-scale=1)"),
    "HTML_NO_LANG": ("3.1.1", "High", "<html> without lang"),
    "MEDIA_AUTOPLAY": ("1.4.2, 2.2.2", "Medium", "Autoplaying video/audio"),
    "INPUT_PLACEHOLDER_ONLY": ("3.3.2, 4.1.2", "High", "Input with placeholder but no aria-label/aria-labelledby/id (likely placeholder used as the label)"),
    "ARIA_LABEL_LITERAL_SUSPECT": ("4.1.2, 2.5.3", "Medium", "Suspicious aria-label text (e.g. 'Disabled', 'Icon', 'Click me', 'Button')"),
    "VISUALLY_HIDDEN_NOISE": ("2.4.6", "Low", "Visually hidden filler text such as 'Click me' / 'Click here'"),
    "ARIA_HIDDEN_ON_FOCUSABLE": ("4.1.2", "High", "aria-hidden=true on a focusable element"),
    "HREF_HASH": ("4.1.2", "Medium", "href='#' used as a button"),
    "HEADING_INSIDE_INTERACTIVE": ("1.3.1", "Medium", "Heading inside <button>/<a> (heading semantics lost)"),
    "FIXED_HEIGHT_OVERFLOW_HIDDEN": ("1.4.10, 1.4.12", "Medium", "Fixed height + overflow:hidden in one rule: clips content at zoom / text spacing"),
    "WORD_BREAK": ("1.4.10", "Low", "word-break: break-all/break-word splits words mid-word"),
    "STICKY_OR_FIXED": ("1.4.10, 2.4.11", "Info", "position: sticky/fixed: check coverage at 200%/400% zoom and focus obscuring"),
    "TOOLTIP_LIBRARY": ("1.4.13", "Medium", "Tooltip/popover library usage: check hoverable, dismissible (Esc), keyboard reachable"),
    "NAV_VIA_BUTTON": ("4.1.2", "Low", "Button whose click navigates (router.push / location): should usually be a link"),
    "NEW_TAB_NO_WARNING": ("3.2.5 (AAA, advisory)", "Low", "target=_blank without a visible/hidden 'opens in new tab' hint"),
    "DIALOG_ARIA_MODAL": ("2.4.3, 4.1.2", "Info", "aria-modal / role=dialog: check focus moves in, is trapped, Esc closes, focus returns"),
    "AUTOFOCUS": ("3.2.1", "Low", "autofocus can move users unexpectedly"),
}
REPO_RULES = {
    "SPA_NO_TITLE_UPDATE": ("2.4.2", "High", "Client router found but no per-route document.title / head management found"),
    "SPA_NO_FOCUS_MANAGEMENT": ("2.4.3, 4.1.3", "Medium", "Client router found but no focus management / announcement after navigation"),
    "NO_REDUCED_MOTION": ("2.3.3 (AAA, advisory)", "Low", "Animations/transitions present but no prefers-reduced-motion handling"),
    "GLOBAL_FOCUS_STYLE": ("2.4.7, 1.4.11", "Info", "Global focus-visible style: check its contrast against light AND dark backgrounds"),
    "NO_SKIP_LINK": ("2.4.1", "Medium", "No skip link found in layout/app shell"),
    "NO_MAIN_LANDMARK": ("1.3.1, 2.4.1", "Medium", "No <main> / role=main found in layout/app shell"),
}

TAG_RE = re.compile(r"<\s*([a-zA-Z][\w-]*)(\s[^<>]*?)?/?>", re.S)
CSS_BLOCK_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)


def parse_json_relaxed(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    pattern = r'("(?:\\.|[^"\\])*")|//.*?$|/\*.*?\*/'
    cleaned = re.sub(pattern, lambda m: m.group(1) if m.group(1) else "", text, flags=re.MULTILINE | re.DOTALL)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return json.loads(cleaned)


def walk(root):
    for d, dirs, files in os.walk(root):
        rel = os.path.relpath(d, root).replace("\\", "/")
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and f"{rel}/{x}".lstrip("./") not in SKIP_DIRS]
        for f in files:
            p = os.path.join(d, f)
            if f.endswith(".min.js") or f.endswith(".map"):
                continue
            try:
                if os.path.getsize(p) > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield p


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def snippet(text, idx, n=110):
    s = text[idx: idx + n].replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def scan(root, max_per_rule):
    hits = {k: [] for k in list(RULES) + list(REPO_RULES)}
    repo = {"router": False, "title": False, "focus_after_nav": False, "motion": False, "reduced_motion": False,
            "skip_link": False, "main": False, "global_focus": [], "stack": set()}

    def add(rule, path, text, idx, extra=""):
        if len(hits[rule]) < max_per_rule:
            relp = os.path.relpath(path, root).replace("\\", "/")
            hits[rule].append({"file": relp, "line": line_of(text, idx), "in_test_path": bool(TEST_PATH.search(relp)),
                               "snippet": snippet(text, idx) + (f"  [{extra}]" if extra else "")})

    pkg = os.path.join(root, "package.json")
    if os.path.exists(pkg):
        try:
            deps = parse_json_relaxed(open(pkg, encoding="utf-8", errors="ignore").read())
            alld = {**deps.get("dependencies", {}), **deps.get("devDependencies", {})}
            for k in ["vue", "react", "@angular/core", "svelte", "nuxt", "next", "vue-router", "react-router-dom",
                      "bootstrap", "primevue", "vuetify", "@mui/material", "tailwindcss", "eslint-plugin-vuejs-accessibility",
                      "eslint-plugin-jsx-a11y", "@axe-core/playwright", "axe-core", "@unhead/vue", "@vueuse/head", "react-helmet"]:
                if k in alld:
                    repo["stack"].add(f"{k}@{alld[k]}")
        except Exception:
            pass

    for path in walk(root):
        low = path.lower()
        if not low.endswith(MARKUP + STYLE + SCRIPT):
            continue
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue

        if low.endswith(SCRIPT + (".vue",)):
            if re.search(r"createRouter\(|new VueRouter|createBrowserRouter|<BrowserRouter|from ['\"]react-router|@angular/router|next/navigation|useRouter\(", text):
                repo["router"] = True
            if re.search(r"document\.title\s*=|useHead\(|useSeoMeta\(|<Helmet|<title>\{|Title\.setTitle|metaInfo|<svelte:head>", text):
                repo["title"] = True
            if re.search(r"afterEach\([\s\S]{0,400}?(focus\(|aria-live|announce)", text) or re.search(r"(routeChange|navigation)[\s\S]{0,200}focus\(", text, re.I):
                repo["focus_after_nav"] = True
            for m in re.finditer(r"\.(tooltip|popover)\(|new\s+(bootstrap\.)?(Tooltip|Popover)\(|v-tooltip|tippy\(|@floating-ui|vTooltip", text):
                add("TOOLTIP_LIBRARY", path, text, m.start())
            for m in re.finditer(r"<button[^>]*@click\s*=\s*\"[^\"]*(router\.push|\$router\.push|navigateTo|location\.href|window\.open)", text):
                add("NAV_VIA_BUTTON", path, text, m.start())

        if low.endswith(MARKUP):
            if re.search(r"skip[- ]?(to)?[- ]?(main|content)|class=\"[^\"]*skip-link", text, re.I):
                repo["skip_link"] = True
            if re.search(r"<main[\s>]|role=[\"']main[\"']", text):
                repo["main"] = True
            for m in TAG_RE.finditer(text):
                tag, attrs = m.group(1).lower(), (m.group(2) or "")
                a = attrs.lower()
                if tag == "img" and not re.search(r"(^|\s)(:?alt|v-bind:alt|\[alt\]|alt=\{)", attrs):
                    add("IMG_NO_ALT", path, text, m.start())
                if tag in ("div", "span", "li", "td", "p", "section", "article", "img", "svg", "i", "tr") and re.search(r"(@click|v-on:click|onclick=|onClick=|\(click\)=|on:click)", attrs):
                    if "role=" not in a or "tabindex" not in a:
                        add("CLICK_ON_NON_INTERACTIVE", path, text, m.start())
                if re.search(r"role=[\"'](button|link|checkbox|switch|tab|menuitem)[\"']", a) and tag not in ("button", "a", "input") and not re.search(r"(@keydown|@keyup|@keypress|onkeydown|onKeyDown|\(keydown\)|on:keydown)", attrs):
                    add("ROLE_BUTTON_NO_KEY", path, text, m.start(), "no key handler on the element itself")
                if re.search(r"tabindex=[\"']?\s*[1-9]", a):
                    add("POSITIVE_TABINDEX", path, text, m.start())
                if tag == "meta" and "viewport" in a and re.search(r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b", a):
                    add("VIEWPORT_ZOOM_BLOCKED", path, text, m.start())
                if tag == "html" and "lang" not in a:
                    add("HTML_NO_LANG", path, text, m.start())
                if tag in ("video", "audio") and re.search(r"\bautoplay\b", a):
                    add("MEDIA_AUTOPLAY", path, text, m.start())
                if tag in ("input", "textarea") and "placeholder" in a and not re.search(r"aria-label|aria-labelledby|\bid=|:id=|type=[\"'](hidden|submit|button)", a):
                    add("INPUT_PLACEHOLDER_ONLY", path, text, m.start())
                lab = re.search(r"aria-label=[\"']([^\"']+)[\"']", attrs)
                if lab and re.fullmatch(r"\s*(disabled|icon|.*\bicon|click me|click here|button|link|image|img|close icon|search icon)\s*", lab.group(1), re.I):
                    add("ARIA_LABEL_LITERAL_SUSPECT", path, text, m.start(), f'aria-label="{lab.group(1)}"')
                if re.search(r"aria-hidden=[\"']true[\"']", a) and (tag in ("button", "a", "input", "select", "textarea") or re.search(r"tabindex=[\"']?0", a)):
                    add("ARIA_HIDDEN_ON_FOCUSABLE", path, text, m.start())
                if tag == "a" and re.search(r"href=[\"']#[\"']", a):
                    add("HREF_HASH", path, text, m.start())
                if tag == "a" and "_blank" in a and not re.search(r"new (tab|window)|opens", text[m.start(): m.start() + 600], re.I):
                    add("NEW_TAB_NO_WARNING", path, text, m.start())
                if re.search(r"aria-modal|role=[\"']dialog[\"']", a):
                    add("DIALOG_ARIA_MODAL", path, text, m.start())
                if re.search(r"data-(bs-)?toggle=[\"'](tooltip|popover)", a) or "v-tooltip" in a:
                    add("TOOLTIP_LIBRARY", path, text, m.start())
                if re.search(r"(^|\s)autofocus(\s|=|$)", a):
                    add("AUTOFOCUS", path, text, m.start())
            for m in re.finditer(r"class=[\"'][^\"']*(visually-hidden|sr-only)[^\"']*[\"'][^>]*>\s*(click me|click here|button)\s*<", text, re.I):
                add("VISUALLY_HIDDEN_NOISE", path, text, m.start())
            for m in re.finditer(r"<(button|a)\b[^>]*>(?:(?!</\1>).){0,1500}?<h[1-6]\b", text, re.S | re.I):
                add("HEADING_INSIDE_INTERACTIVE", path, text, m.start())

        if low.endswith(STYLE):
            css = text
            if low.endswith((".vue", ".svelte")):
                css = "\n".join(re.findall(r"<style[^>]*>([\s\S]*?)</style>", text))
                offset_text = text
            else:
                offset_text = text
            if re.search(r"animation\s*:|transition\s*:|@keyframes", css):
                repo["motion"] = True
            if "prefers-reduced-motion" in css:
                repo["reduced_motion"] = True
            for m in CSS_BLOCK_RE.finditer(css):
                sel, body = m.group(1).strip(), m.group(2)
                idx = offset_text.find(m.group(0)[:60]) if css is not text else m.start()
                idx = max(idx, 0)
                if ":focus" in sel and re.search(r"outline\s*:\s*(none|0)\b", body):
                    add("FOCUS_OUTLINE_REMOVED", path, offset_text, idx, sel[-80:])
                if ":focus-visible" in sel and re.search(r"outline|box-shadow", body) and len(sel) < 40:
                    flat = re.sub(r"\s+", " ", body.strip())[:120]
                    repo["global_focus"].append(f"{os.path.relpath(path, root)}: {sel} {{{flat}}}")
                if re.search(r"(^|;|\s)height\s*:\s*\d+(px|rem|em|vh)", body) and re.search(r"overflow(-y)?\s*:\s*hidden", body):
                    add("FIXED_HEIGHT_OVERFLOW_HIDDEN", path, offset_text, idx, sel[-80:])
                if re.search(r"word-break\s*:\s*break-(all|word)", body):
                    add("WORD_BREAK", path, offset_text, idx, sel[-80:])
                if re.search(r"position\s*:\s*(sticky|fixed)", body):
                    add("STICKY_OR_FIXED", path, offset_text, idx, sel[-80:])

    if repo["router"] and not repo["title"]:
        hits["SPA_NO_TITLE_UPDATE"].append({"file": "(repo)", "line": 0, "snippet": "router present; no document.title/useHead/Helmet found"})
    if repo["router"] and not repo["focus_after_nav"]:
        hits["SPA_NO_FOCUS_MANAGEMENT"].append({"file": "(repo)", "line": 0, "snippet": "router present; no focus()/live-region after navigation found"})
    if repo["motion"] and not repo["reduced_motion"]:
        hits["NO_REDUCED_MOTION"].append({"file": "(repo)", "line": 0, "snippet": "animations/transitions found; no prefers-reduced-motion"})
    for g in repo["global_focus"][:5]:
        hits["GLOBAL_FOCUS_STYLE"].append({"file": g.split(":")[0], "line": 0, "snippet": g})
    if not repo["skip_link"]:
        hits["NO_SKIP_LINK"].append({"file": "(repo)", "line": 0, "snippet": "no skip link pattern found"})
    if not repo["main"]:
        hits["NO_MAIN_LANDMARK"].append({"file": "(repo)", "line": 0, "snippet": "no <main> or role=main found"})

    allrules = {**RULES, **REPO_RULES}
    out = []
    for rule, items in hits.items():
        if items:
            wcag, sev, desc = allrules[rule]
            if all(h.get("in_test_path") for h in items) and sev in ("High", "Medium"):
                sev, desc = "Low", desc + " (only in test/fixture paths)"
            out.append({"rule": rule, "wcag": wcag, "severity_hint": sev, "description": desc, "count": len(items), "hits": items})
    order = {"High": 0, "Medium": 1, "Low": 2, "Info": 3}
    out.sort(key=lambda r: (order[r["severity_hint"]], -r["count"]))
    return {"root": os.path.abspath(root), "stack": sorted(repo["stack"]), "results": out,
            "note": "Leads only. Confirm each in context (and in the running app) before reporting. Counts are capped per rule."}


def to_sarif(tool_name, tool_version, results, root=""):
    level_map = {
        "Critical": "error",
        "High": "error",
        "Medium": "warning",
        "Low": "note",
        "Info": "note",
    }
    sarif_rules = []
    sarif_results = []
    seen_rules = set()

    for item in results:
        rid = item.get("rule")
        if not rid:
            continue
        if rid not in seen_rules:
            seen_rules.add(rid)
            sarif_rules.append({
                "id": rid,
                "name": rid,
                "shortDescription": {
                    "text": item.get("description", rid)
                },
                "defaultConfiguration": {
                    "level": level_map.get(item.get("severity_hint", "Info"), "note")
                }
            })
        for hit in item.get("hits", []):
            fpath = hit.get("file", "")
            lvl = level_map.get(item.get("severity_hint", "Info"), "note")
            if fpath in ("(git history)", "(repo)", "unknown"):
                sarif_results.append({
                    "ruleId": rid,
                    "level": lvl,
                    "message": {
                        "text": f"{item.get('description', '')}: {hit.get('snippet', '')}".strip()
                    }
                })
                continue
            ln = max(1, hit.get("line", 1))
            sarif_results.append({
                "ruleId": rid,
                "level": lvl,
                "message": {
                    "text": hit.get("snippet") or item.get("description", "")
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": fpath.replace("\\", "/"),
                                "uriBaseId": "%SRCROOT%"
                            },
                            "region": {
                                "startLine": ln
                            }
                        }
                    }
                ]
            })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": tool_version,
                        "rules": sarif_rules
                    }
                },
                "results": sarif_results
            }
        ]
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--json")
    ap.add_argument("--sarif")
    ap.add_argument("--max-per-rule", type=int, default=25)
    a = ap.parse_args()
    res = scan(a.root, a.max_per_rule)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
    if a.sarif:
        with open(a.sarif, "w", encoding="utf-8") as f:
            json.dump(to_sarif("cd-web-a11y-audit", "1.3.0", res["results"], a.root), f, indent=1)
    print(f"Stack: {', '.join(res['stack']) or 'unknown'}")
    for r in res["results"]:
        print(f"\n[{r['severity_hint']}] {r['rule']} ({r['wcag']}): {r['description']} — {r['count']} hit(s)")
        for h in r["hits"][:5]:
            print(f"   {h['file']}:{h['line']}  {h['snippet']}")
    print("\n" + res["note"])


if __name__ == "__main__":
    sys.exit(main())
