(() => {
  const S = {};
  const cap = (arr, n = 20) => ({ count: arr.length, samples: arr.slice(0, n) });
  const host = u => { try { return new URL(u, location.href).host; } catch (e) { return '?'; } };
  const sameSite = u => { try { const h = new URL(u, location.href).hostname, me = location.hostname; const base = d => d.split('.').slice(-2).join('.'); return base(h) === base(me); } catch (e) { return false; } };
  const redact = s => s.length <= 10 ? s.slice(0, 2) + '…' : s.slice(0, 6) + '…[' + s.length + ' chars]';
  const SECRET_PATTERNS = [
    ['AWS access key', /AKIA[0-9A-Z]{16}/g],
    ['Google API key (often public by design: check restrictions)', /AIza[0-9A-Za-z_\-]{35}/g],
    ['Stripe secret key', /sk_(live|test)_[0-9a-zA-Z]{20,}/g],
    ['Slack token', /xox[baprs]-[0-9A-Za-z-]{10,}/g],
    ['GitHub token', /gh[pousr]_[0-9A-Za-z]{30,}/g],
    ['Private key block', /-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----/g],
    ['JWT', /eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g],
    ['Bearer token literal', /Bearer\s+[A-Za-z0-9\-._~+/]{20,}=*/g],
    ['Generic secret assignment', /(api[_-]?key|secret|client[_-]?secret|access[_-]?token|auth[_-]?token|password)["']?\s*[:=]\s*["'][^"'\s]{12,}["']/gi],
  ];
  const findSecrets = (text, where) => { const out = []; for (const [label, re] of SECRET_PATTERNS) { const m = text.match(re) || []; [...new Set(m)].slice(0, 5).forEach(v => out.push(`${label} in ${where}: ${redact(v)}`)); } return out; };

  S.headers = async (url = location.href) => {
    const r = await fetch(url, { cache: 'no-store', credentials: 'same-origin', redirect: 'follow' });
    const h = {}; r.headers.forEach((v, k) => { h[k] = v; });
    const want = ['strict-transport-security', 'content-security-policy', 'content-security-policy-report-only', 'x-content-type-options', 'x-frame-options', 'referrer-policy', 'permissions-policy', 'cross-origin-opener-policy', 'cross-origin-resource-policy', 'cross-origin-embedder-policy', 'cache-control', 'server', 'x-powered-by', 'x-aspnet-version', 'via', 'access-control-allow-origin', 'access-control-allow-credentials'];
    const present = {}, missing = [];
    want.forEach(k => { if (h[k] !== undefined) present[k] = h[k].slice(0, 300); else missing.push(k); });
    const metaCsp = document.querySelector('meta[http-equiv="Content-Security-Policy" i]')?.content || null;
    return { url: r.url, status: r.status, present, missing, metaCsp: metaCsp && metaCsp.slice(0, 1500), note: 'Browser fetch hides some headers (e.g. set-cookie). Confirm with curl -sSI.' };
  };

  S.csp = (policy) => {
    const p = policy || document.querySelector('meta[http-equiv="Content-Security-Policy" i]')?.content || '';
    if (!p) return 'No CSP passed or found in a meta tag. Pass the header value: __sec.csp("<policy>")';
    const dirs = {}; p.split(';').map(s => s.trim()).filter(Boolean).forEach(d => { const [k, ...v] = d.split(/\s+/); dirs[k.toLowerCase()] = v; });
    const issues = [];
    const scriptSrc = dirs['script-src'] || dirs['default-src'] || [];
    if (!dirs['default-src']) issues.push('No default-src fallback');
    if (!dirs['script-src'] && !dirs['default-src']) issues.push('No script-src: scripts unrestricted');
    if (scriptSrc.includes("'unsafe-inline'") && !scriptSrc.some(s => /^'(nonce|sha\d{3})-/.test(s))) issues.push("script-src allows 'unsafe-inline' without nonce/hash (XSS mitigation largely lost)");
    if (scriptSrc.includes("'unsafe-eval'")) issues.push("script-src allows 'unsafe-eval'");
    Object.entries(dirs).forEach(([k, v]) => {
      v.forEach(s => {
        if (s === '*' || /^(https?:|data:|blob:)$/.test(s) && /script|default|object|frame/.test(k)) issues.push(`${k} allows broad source ${s}`);
        if (/^http:\/\//.test(s)) issues.push(`${k} allows insecure http source ${s}`);
        if (/localhost|127\.0\.0\.1|0\.0\.0\.0|\.local\b/.test(s)) issues.push(`${k} allows development host ${s} (leftover from development)`);
        if (/^\*\./.test(s) || /\/\/\*\./.test(s)) issues.push(`${k} allows wildcard subdomain ${s}`);
      });
    });
    if (!dirs['object-src'] && !(dirs['default-src'] || []).includes("'none'")) issues.push("object-src not set to 'none'");
    if (!dirs['base-uri']) issues.push('base-uri not set');
    if (!dirs['frame-ancestors']) issues.push('frame-ancestors not set (clickjacking protection relies on X-Frame-Options). Note: frame-ancestors is ignored in a <meta> CSP');
    if (!dirs['form-action']) issues.push('form-action not set');
    return { directives: Object.keys(dirs), issues };
  };

  S.scan = async (opts = {}) => {
    const R = { url: location.href, protocol: location.protocol, origin: location.origin };
    const scripts = [...document.scripts];
    R.inlineScripts = scripts.filter(s => !s.src && s.textContent.trim()).length;
    R.inlineEventHandlers = document.querySelectorAll('[onclick],[onload],[onerror],[onmouseover],[onsubmit],[onchange]').length;
    R.externalScripts = scripts.filter(s => s.src).map(s => ({ src: s.src.slice(0, 120), thirdParty: !sameSite(s.src), sri: !!s.integrity, crossorigin: s.crossOrigin || null }));
    R.thirdPartyScriptsWithoutSRI = cap(R.externalScripts.filter(s => s.thirdParty && !s.sri).map(s => s.src));
    R.stylesheetsThirdPartyNoSRI = cap([...document.querySelectorAll('link[rel=stylesheet][href]')].filter(l => !sameSite(l.href) && !l.integrity).map(l => l.href.slice(0, 120)));
    const res = performance.getEntriesByType('resource').map(e => e.name);
    const origins = {}; res.concat(R.externalScripts.map(s => s.src)).forEach(u => { const h = host(u); origins[h] = (origins[h] || 0) + 1; });
    R.requestOrigins = Object.entries(origins).sort((a, b) => b[1] - a[1]).map(([h, n]) => `${h} (${n})${sameSite('https://' + h) ? '' : ' [third party]'}`);
    R.mixedContent = cap(res.filter(u => location.protocol === 'https:' && /^http:\/\//.test(u)).concat([...document.querySelectorAll('[src^="http:"],[href^="http:"]')].filter(e => e.tagName !== 'A').map(e => e.outerHTML.slice(0, 120))));
    R.cookiesVisibleToJS = document.cookie ? document.cookie.split(';').map(c => c.trim().split('=')[0]) : [];
    R.sessionLikeCookiesVisibleToJS = R.cookiesVisibleToJS.filter(n => /sess|sid|auth|token|jwt|login|remember/i.test(n));
    const storage = [];
    for (const [label, st] of [['localStorage', localStorage], ['sessionStorage', sessionStorage]]) { try { for (let i = 0; i < st.length; i++) { const k = st.key(i), v = st.getItem(k) || ''; const tokeny = /token|jwt|auth|session|secret|password|bearer/i.test(k) || /^eyJ[A-Za-z0-9_-]{10,}\./.test(v); storage.push(`${label}.${k} (${v.length} chars)${tokeny ? ' TOKEN-LIKE: ' + redact(v) : ''}`); } } catch (e) { storage.push(label + ' not readable'); } }
    R.webStorage = cap(storage, 40);
    R.forms = [...document.forms].map(f => { const pw = f.querySelector('input[type=password]'); const hidden = [...f.querySelectorAll('input[type=hidden]')].map(i => i.name); return { action: (f.getAttribute('action') || '(same page)').slice(0, 100), method: (f.method || 'get').toUpperCase(), insecureAction: /^http:\/\//.test(f.action), hasPassword: !!pw, passwordAutocomplete: pw ? (pw.getAttribute('autocomplete') || '(none)') : null, passwordOverGET: !!pw && (f.method || 'get').toLowerCase() === 'get', csrfLikeField: hidden.some(n => /csrf|xsrf|token|authenticity|__requestverification/i.test(n)), hiddenFields: hidden.slice(0, 8) }; });
    R.blankTargetsWithoutNoopener = cap([...document.querySelectorAll('a[target=_blank]')].filter(a => !/noopener|noreferrer/.test(a.rel)).map(a => a.href.slice(0, 100)), 10);
    R.iframes = [...document.querySelectorAll('iframe')].map(f => ({ src: (f.src || '').slice(0, 100), sandbox: f.getAttribute('sandbox'), thirdParty: f.src ? !sameSite(f.src) : false }));
    const lib = {};
    try { if (window.jQuery?.fn?.jquery) lib.jquery = window.jQuery.fn.jquery; } catch (e) {}
    try { const app = document.querySelector('[data-v-app]')?.__vue_app__ || document.querySelector('#app')?.__vue_app__; if (app?.version) lib.vue = app.version; else if (window.Vue?.version) lib.vue = window.Vue.version; } catch (e) {}
    try { const ng = document.querySelector('[ng-version]'); if (ng) lib.angular = ng.getAttribute('ng-version'); else if (window.angular?.version) lib.angularjs = window.angular.version.full; } catch (e) {}
    try { const hook = window.__REACT_DEVTOOLS_GLOBAL_HOOK__; if (hook?.renderers?.size) lib.react = [...hook.renderers.values()].map(r => r.version).join(','); else if (window.React?.version) lib.react = window.React.version; } catch (e) {}
    try { if (window.next?.version) lib.next = window.next.version; if (window.__NUXT__) lib.nuxt = 'present'; } catch (e) {}
    try { if (window.bootstrap?.Tooltip?.VERSION) lib.bootstrap = window.bootstrap.Tooltip.VERSION; else if (window.jQuery?.fn?.tooltip?.Constructor?.VERSION) lib.bootstrap = window.jQuery.fn.tooltip.Constructor.VERSION; } catch (e) {}
    try { if (window._?.VERSION) lib.lodash = window._.VERSION; if (window.moment?.version) lib.moment = window.moment.version; if (window.DOMPurify?.version) lib.dompurify = window.DOMPurify.version; } catch (e) {}
    const gen = document.querySelector('meta[name=generator]')?.content; if (gen) lib.generator = gen;
    R.libraryVersions = lib;
    const secrets = [];
    for (const g of ['__NEXT_DATA__', '__NUXT__', '__INITIAL_STATE__', '__APOLLO_STATE__', '__ENV__', 'env', 'config', 'APP_CONFIG']) { try { if (window[g]) secrets.push(...findSecrets(JSON.stringify(window[g]).slice(0, 2e6), 'window.' + g)); } catch (e) {} }
    scripts.filter(s => !s.src).forEach((s, i) => secrets.push(...findSecrets(s.textContent, 'inline script #' + i)));
    secrets.push(...findSecrets(document.documentElement.outerHTML.replace(/<script[\s\S]*?<\/script>/gi, ''), 'page HTML'));
    const sourceMaps = [];
    if (opts.fetchScripts !== false) {
      for (const s of R.externalScripts.filter(x => !x.thirdParty).slice(0, 25)) {
        try { const t = await (await fetch(s.src, { cache: 'no-store' })).text(); secrets.push(...findSecrets(t, s.src.split('/').pop())); const m = t.match(/\/\/[#@]\s*sourceMappingURL=([^\s'"]+)\s*$/m); if (m && !/^data:/.test(m[1])) sourceMaps.push(new URL(m[1], s.src).href); const urls = t.match(/https?:\/\/[a-z0-9.-]+\.[a-z]{2,}(?::\d+)?(?:\/[^\s"'`)]*)?/gi) || []; urls.filter(u => /api|graphql|graphcms|hygraph|firebase|supabase|amazonaws|azure|internal|staging|dev\.|test\.|localhost/i.test(u)).forEach(u => (R.endpointsInBundles = R.endpointsInBundles || new Set()).add(u.slice(0, 120))); } catch (e) {}
      }
    }
    R.endpointsInBundles = R.endpointsInBundles ? [...R.endpointsInBundles].slice(0, 30) : [];
    R.possibleSecrets = cap([...new Set(secrets)], 30);
    R.sourceMapReferences = cap(sourceMaps, 10);
    R.note = 'Secrets are redacted. Never copy full values into the report. Google/Firebase browser keys are often public by design: report as Informational unless unrestricted.';
    return R;
  };

  S.sourceMapsExposed = async (urls) => { const out = []; for (const u of (urls || []).slice(0, 10)) { try { const r = await fetch(u, { method: 'GET', cache: 'no-store' }); out.push(`${u} -> ${r.status} ${r.headers.get('content-type') || ''}`); } catch (e) { out.push(`${u} -> blocked/error`); } } return out; };

  window.__sec = S;
  return 'security kit loaded: await __sec.headers(), __sec.csp(policy), await __sec.scan(), await __sec.sourceMapsExposed(urls)';
})();
