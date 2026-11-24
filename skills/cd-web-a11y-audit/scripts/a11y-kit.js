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
