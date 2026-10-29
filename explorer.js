/* Results explorer: named comparisons from data/comparisons.json (built by tools/build_site.py from committed results).
   Every listed comparison has recorded rows, so no choice leads to an empty view. Aggregates only. */
'use strict';
(function () {
  const $ = id => document.getElementById(id);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const NR = 'not reported';
  let comps = [], current = null, machine = 'all';

  const isPct = c => c.task === 'chart_qa' || c.task === 'ocr_crop';
  const fmtScore = (c, v) => !Number.isFinite(v) ? NR : isPct(c) ? (100 * v).toFixed(1) + '%' : v.toFixed(3);
  const fmtPct = v => Number.isFinite(v) ? (100 * v).toFixed(1) + '%' : NR;
  const fmtSec = v => Number.isFinite(v) ? v.toFixed(2) + ' s' : NR;
  const num = v => (v === null || v === undefined || v === '') ? NaN : Number(v);

  // Old explorer links (#explorer?task=..&side=..&split=..) land on the closest named comparison.
  const LEGACY = { 'table|confirmation v3': 'tables-final', 'table|confirmation v1': 'tables-heldout-r1', 'table|development|laptop': 'tables-dev-laptop', 'table|development': 'tables-dev-desktop',
    'page_text|confirmation v3': 'pages-final', 'page_text|confirmation v2|laptop': 'pages-masking-laptop', 'page_text|confirmation v2': 'pages-masking-desktop', 'page_text|development': 'pages-dev-desktop',
    'chart_qa|confirmation v1': 'charts-heldout-r1', 'chart_qa|development|laptop': 'charts-dev-laptop', 'chart_qa|development': 'charts-dev-desktop',
    'chart_table|development|laptop': 'charttable-dev-laptop', 'chart_table|development': 'charttable-dev-desktop', 'ocr_crop|development|laptop': 'crops-dev-laptop', 'ocr_crop': 'crops-dev-desktop' };
  function legacyId(q) {
    const p = new URLSearchParams(q), t = p.get('task'), s = p.get('split'), side = p.get('side');
    return LEGACY[[t, s, side].join('|')] || LEGACY[[t, s].join('|')] || LEGACY[t] || ({ table: 'tables-final', page_text: 'pages-final', chart_qa: 'charts-r2', chart_table: 'charttable-dev-laptop' })[t] || null;
  }
  function idFromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    if (h.startsWith('cmp=')) return h.slice(4);
    if (h.startsWith('explorer?')) return legacyId(h.split('?')[1]);
    return null;
  }

  function renderList() {
    const list = $('cmp-list'); list.replaceChildren();
    let track = null;
    comps.filter(c => machine === 'all' || c.side === machine || c.side === 'mixed').forEach(c => {
      if (c.track !== track) { track = c.track; list.append(el('div', 'cmp-group', track)); }
      const b = el('button'); b.type = 'button'; b.dataset.id = c.id; b.textContent = c.title;
      b.append(el('small', '', c.stage + ' · ' + (c.side === 'mixed' ? 'laptop and desktop' : c.side === 'desktop' && c.task === 'legal' ? 'desktop and hosted API' : c.side)));
      b.setAttribute('aria-current', current && current.id === c.id ? 'true' : 'false');
      b.addEventListener('click', () => select(c.id, true));
      list.append(b);
    });
  }

  function glance(c) {
    const g = el('div', 'glance'), rows = c.rows;
    const add = (label, text, cls) => { const d = el('div', cls); d.append(el('b', '', label), document.createTextNode(text)); g.append(d); };
    if (c.task === 'legal') {
      const best = [...rows].sort((a, b) => b.nli - a.nli)[0];
      add('Most ContractNLI correct', best.model + ' (' + best.nli_n + '/30)');
      add('CUAD baseline', 'Answering "absent" every time scores 15/30. No configuration beat it.');
      add('Most truncated', [...rows].sort((a, b) => b.truncated - a.truncated)[0].model);
      add('Recommended here', c.recommend, 'rec');
      return g;
    }
    const sorted = [...rows].sort((a, b) => c.lower_is_better ? a.score - b.score : b.score - a.score);
    add(c.lower_is_better ? 'Lowest error' : 'Highest ' + (c.task === 'chart_qa' ? 'accuracy' : 'score'), label(sorted[0]) + ' · ' + fmtScore(c, sorted[0].score));
    const withNum = rows.filter(r => Number.isFinite(num(r.numbers)));
    if (withNum.length && c.task !== 'chart_table') { const n = withNum.sort((a, b) => num(b.numbers) - num(a.numbers))[0]; add('Most numbers recovered', label(n) + ' · ' + fmtPct(num(n.numbers))); }
    else add('Numbers recovered', 'not measured in this comparison');
    const withT = rows.filter(r => Number.isFinite(num(r.seconds)));
    if (withT.length) { const f = withT.sort((a, b) => num(a.seconds) - num(b.seconds))[0]; add('Fastest per item', label(f) + ' · ' + fmtSec(num(f.seconds))); }
    else add('Speed', 'not reported in this comparison');
    const rec = rows.find(r => r.key === c.recommend);
    add('Recommended here', rec ? label(rec) : 'no single choice: see what it means', 'rec');
    return g;
  }
  const label = r => r.method ? r.model + ', ' + r.method : r.model;

  function bars(c) {
    const box = el('div', 'bars');
    if (c.task === 'legal') {
      const lg = el('p', 'legend'); lg.innerHTML = '<span><i style="background:var(--teal)"></i>CUAD</span><span><i style="background:var(--gray)"></i>ContractNLI</span><span><i style="border-left:2px dashed var(--warn);width:0"></i>CUAD always-"absent" baseline (15/30)</span>';
      box.append(lg);
      c.rows.forEach(r => {
        [['CUAD', r.cuad, ''], ['ContractNLI', r.nli_n, 'alt']].forEach(([t, v, cls], i) => {
          const row = el('div', 'bar'), tr = el('div', 'track'), f = el('div', 'fill ' + cls);
          f.style.width = (v / 30 * 100) + '%'; tr.append(f);
          if (t === 'CUAD') { const m = el('span', 'baseline-mark'); m.style.left = '50%'; m.title = 'Always-absent baseline: 15/30'; tr.append(m); }
          row.append(el('div', '', i === 0 ? r.model + ' · CUAD' : 'ContractNLI'), tr, el('div', 'val', v + '/30'));
          box.append(row);
        });
      });
      return box;
    }
    const sorted = [...c.rows].sort((a, b) => c.lower_is_better ? a.score - b.score : b.score - a.score);
    const max = c.lower_is_better ? Math.max(...sorted.map(r => r.score), 0.001) : 1;
    sorted.forEach(r => {
      const row = el('div', 'bar'), tr = el('div', 'track'), f = el('div', 'fill' + (r.key === c.recommend ? '' : ' alt'));
      f.style.width = Math.max(0.5, r.score / max * 100) + '%'; tr.append(f);
      const name = el('div', '', label(r)); if (r.machine) name.append(el('small', '', ' · ' + r.machine));
      row.append(name, tr, el('div', 'val', fmtScore(c, r.score)));
      box.append(row);
    });
    return box;
  }

  function table(c) {
    const wrap = el('div', 'table-scroll'), t = el('table'), head = el('tr'), body = el('tbody');
    const cols = c.task === 'legal'
      ? ['Configuration', 'CUAD correct /30', 'ContractNLI correct /30', 'Cut off (of 60)']
      : ['Configuration', c.metric, c.items[0].toUpperCase() + c.items.slice(1) + ' tested', 'Processing failures', 'Reference numbers recovered', 'Median seconds per item'];
    cols.forEach((h, i) => { const th = el('th', i ? 'num' : '', h); th.scope = 'col'; head.append(th); });
    const thead = el('thead'); thead.append(head); t.append(thead);
    const rows = c.task === 'legal' ? c.rows : [...c.rows].sort((a, b) => c.lower_is_better ? a.score - b.score : b.score - a.score);
    rows.forEach(r => {
      const tr = el('tr', r.key === c.recommend ? 'recommended' : '');
      const name = el('td', '', label(r)); if (r.machine) name.append(el('div', 'small', r.machine)); if (r.key === c.recommend) name.append(el('div', 'small', 'Recommended in this comparison'));
      tr.append(name);
      const vals = c.task === 'legal' ? [r.cuad, r.nli_n, r.truncated]
        : [fmtScore(c, r.score), r.cases, r.failed === null || r.failed === undefined ? NR : r.failed, fmtPct(num(r.numbers)), fmtSec(num(r.seconds))];
      vals.forEach(v => tr.append(el('td', 'num', String(v))));
      body.append(tr);
    });
    t.append(body); wrap.append(t); return wrap;
  }

  function renderPanel(c) {
    const p = $('cmp-panel'); p.replaceChildren();
    p.append(el('p', 'eyebrow', c.track));
    p.append(el('h3', '', c.title));
    const meta = el('div', 'meta');
    meta.append(el('span', 'badge ' + (c.confirmatory ? 'good' : c.stage === 'Development' ? 'caution' : 'neutral'), c.stage), el('span', 'badge', c.hardware));
    p.append(meta);
    p.append(el('p', 'q', c.question));
    p.append(el('p', 'def', c.stage_note));
    p.append(glance(c));
    const m = el('p', 'def'); m.append(el('b', '', c.metric + ': '), document.createTextNode(c.metric_note + (c.lower_is_better ? '' : ' Higher is better.')));
    p.append(m, bars(c), table(c));
    if (c.task !== 'legal') p.append(el('p', 'def', 'Failed or cut-off attempts score zero and stay in the averages. "Processing failures" counts attempts that returned no usable output; zero failures does not mean zero mistakes. Median seconds is the middle request time per item on the stated machine, excluding model loading. "Not reported" means the source did not record it, not zero.'));
    const mean = el('div', 'callout'); mean.append(el('h4', '', 'What this means'), el('p', '', c.meaning)); p.append(mean);
    const lim = el('p', 'def'); lim.append(el('b', '', 'Limits: '), document.createTextNode(c.limits)); p.append(lim);
    if (c.sources && c.sources.length) {
      const s = el('p', 'def'); s.append(el('b', '', 'Sources: '));
      c.sources.forEach((src, i) => { const a = el('a', '', src.label); a.href = src.url; s.append(a); if (i < c.sources.length - 1) s.append(document.createTextNode(' · ')); });
      p.append(s);
    }
    const btn = el('button', 'button ghost', 'Download this comparison (CSV)'); btn.type = 'button'; btn.addEventListener('click', () => csv(c)); p.append(btn);
  }

  function csv(c) {
    const cols = c.task === 'legal' ? ['model', 'cuad', 'nli_n', 'truncated'] : ['model', 'method', 'score', 'cases', 'failed', 'numbers', 'seconds', 'machine'];
    const q = v => '"' + String(v ?? '').replaceAll('"', '""') + '"';
    const text = [['comparison', ...cols].map(q).join(','), ...c.rows.map(r => [c.id, ...cols.map(k => r[k])].map(q).join(','))].join('\r\n');
    const a = el('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' })); a.download = c.id + '.csv'; a.click();
  }

  function select(id, push) {
    const c = comps.find(x => x.id === id) || comps[0];
    current = c;
    if (push) history.pushState(null, '', '#cmp=' + c.id);
    renderList(); renderPanel(c);
    const note = $('cmp-redirect');
    if (note) note.textContent = '';
  }

  function onHash(scroll) {
    const id = idFromHash();
    if (!id) return false;
    const known = comps.some(c => c.id === id);
    select(known ? id : comps[0].id, false);
    if (!known && $('cmp-redirect')) $('cmp-redirect').textContent = 'That link pointed to a view that no longer exists, so the closest available comparison is shown.';
    if (location.hash.startsWith('#explorer?')) history.replaceState(null, '', '#cmp=' + current.id);
    if (scroll) $('explorer').scrollIntoView();
    return true;
  }

  document.querySelectorAll('[data-machine]').forEach(b => b.addEventListener('click', () => {
    machine = b.dataset.machine;
    document.querySelectorAll('[data-machine]').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
    if (current && machine !== 'all' && current.side !== machine && current.side !== 'mixed') {
      const first = comps.find(c => c.side === machine); if (first) { select(first.id, true); return; }
    }
    renderList();
  }));

  fetch('data/comparisons.json').then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(d => {
    comps = d.comparisons;
    if (!onHash(true)) select('tables-final', false);
    window.addEventListener('hashchange', () => onHash(false));
    window.addEventListener('popstate', () => onHash(false));
  }).catch(() => {
    $('cmp-panel').replaceChildren(el('p', '', 'The comparison data did not load. Open this page from the website (not a saved file), or use the reports listed under Resources.'));
  });
})();
