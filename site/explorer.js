/* Results explorer, in the original design: dependent dropdown filters over the named comparisons in
   data/comparisons.json (built by tools/build_site.py from committed results). Each filter offers only choices that
   have recorded results, so no combination leads to an empty view. Aggregates only. */
'use strict';
(function () {
  const $ = id => document.getElementById(id);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
  const NR = 'not reported';
  const TASKS = [['table', 'Tables'], ['page_text', 'Whole-page text'], ['chart_qa', 'Chart questions'], ['chart_table', 'Chart to table'],
    ['ocr_crop', 'Cropped text regions'], ['layout', 'Finding tables and figures'], ['legal', 'Contract questions']];
  const MACHINE = { desktop: 'Desktop · RTX 5090, 32 GB', laptop: 'Laptop · RTX 4000 Ada, 12 GB', mixed: 'Laptop (7B, 8B) and desktop (32B)' };
  let comps = [], cur = null, method = 'all', legalView = 'nli';

  const isPct = c => c.task === 'chart_qa' || c.task === 'ocr_crop';
  const fmtScore = (c, v) => !Number.isFinite(v) ? NR : isPct(c) ? (100 * v).toFixed(1) + '%' : v.toFixed(3);
  const fmtPct = v => Number.isFinite(v) ? (100 * v).toFixed(1) + '%' : NR;
  const fmtSec = v => Number.isFinite(v) ? v.toFixed(2) + ' s' : NR;
  const num = v => (v === null || v === undefined || v === '') ? NaN : Number(v);
  const label = r => r.method ? r.model + ', ' + r.method : r.model;
  const machineOf = c => c.task === 'legal' ? 'Desktop and hosted API' : (MACHINE[c.side] || c.side);

  // Old explorer links (#explorer?task=..&side=..&split=..) land on the closest comparison.
  const LEGACY = { 'table|confirmation v3': 'tables-final', 'table|confirmation v1': 'tables-heldout-r1', 'table|development|laptop': 'tables-dev-laptop', 'table|development': 'tables-dev-desktop',
    'page_text|confirmation v3': 'pages-final', 'page_text|confirmation v2|laptop': 'pages-masking-laptop', 'page_text|confirmation v2': 'pages-masking-desktop', 'page_text|development': 'pages-dev-desktop',
    'chart_qa|confirmation v1': 'charts-heldout-r1', 'chart_qa|development|laptop': 'charts-dev-laptop', 'chart_qa|development': 'charts-dev-desktop',
    'chart_table|development|laptop': 'charttable-dev-laptop', 'chart_table|development': 'charttable-dev-desktop', 'ocr_crop|development|laptop': 'crops-dev-laptop', 'ocr_crop': 'crops-dev-desktop' };
  function legacyId(q) {
    const p = new URLSearchParams(q), t = p.get('task'), s = p.get('split'), side = p.get('side');
    return LEGACY[[t, s, side].join('|')] || LEGACY[[t, s].join('|')] || LEGACY[t] || ({ table: 'tables-final', page_text: 'pages-final', chart_qa: 'charts-r2', chart_table: 'charttable-dev-laptop' })[t] || null;
  }

  function fillSelect(sel, opts, value) {
    sel.replaceChildren(...opts.map(([v, t]) => { const o = el('option', '', t); o.value = v; return o; }));
    sel.value = value;
  }
  function choice(wrapId, selId, opts, value) {
    const wrap = $(wrapId), sel = $(selId), stat = wrap.querySelector('.static-choice');
    if (opts.length === 1) { sel.hidden = true; stat.hidden = false; stat.textContent = opts[0][1]; }
    else { sel.hidden = false; stat.hidden = true; fillSelect(sel, opts, value); }
  }

  function renderFilters() {
    const c = cur;
    fillSelect($('f-task'), TASKS.filter(([t]) => comps.some(x => x.task === t)), c.task);
    const sameTask = comps.filter(x => x.task === c.task);
    const machines = [...new Map(sameTask.map(x => [x.side, machineOf(x)])).entries()];
    choice('w-machine', 'f-machine', machines, c.side);
    const sets = comps.filter(x => x.task === c.task && x.side === c.side).map(x => [x.id, x.stage + ' · ' + x.rows[0].cases.toLocaleString() + ' ' + x.items]);
    choice('w-set', 'f-set', sets, c.id);
    const lm = $('w-method').querySelector('label span');
    if (c.task === 'legal') {
      lm.textContent = 'Show';
      choice('w-method', 'f-method', [['nli', 'ContractNLI'], ['cuad', 'CUAD']], legalView);
    } else {
      lm.textContent = 'Method';
      const ms = [...new Set(c.rows.map(r => r.method).filter(Boolean))];
      if (method !== 'all' && !ms.includes(method)) method = 'all';
      choice('w-method', 'f-method', ms.length > 1 ? [['all', 'All recorded methods'], ...ms.map(m => [m, m[0].toUpperCase() + m.slice(1)])] : [['all', ms[0] ? ms[0][0].toUpperCase() + ms[0].slice(1) : 'One method']], method);
    }
  }

  function glance(c, rows) {
    const g = el('div', 'glance-row');
    const add = (h, t, cls) => { const d = el('div', cls); d.append(el('b', '', h), document.createTextNode(t)); g.append(d); };
    if (c.task === 'legal') {
      const best = [...c.rows].sort((a, b) => b.nli_n - a.nli_n)[0];
      add('Most ContractNLI correct', best.model + ' · ' + best.nli_n + '/30');
      add('CUAD', 'None beat answering "absent" every time (15/30)');
      add('Most cut off', [...c.rows].sort((a, b) => b.truncated - a.truncated)[0].model);
      add('Recommended here', c.recommend, 'rec');
      return g;
    }
    const by = [...rows].sort((a, b) => c.lower_is_better ? a.score - b.score : b.score - a.score);
    add(c.lower_is_better ? 'Lowest error' : 'Highest score', label(by[0]) + ' · ' + fmtScore(c, by[0].score));
    const wn = rows.filter(r => Number.isFinite(num(r.numbers)));
    add('Most numbers recovered', wn.length && c.task !== 'chart_table' ? (n => label(n) + ' · ' + fmtPct(num(n.numbers)))(wn.sort((a, b) => num(b.numbers) - num(a.numbers))[0]) : 'not measured here');
    const wt = rows.filter(r => Number.isFinite(num(r.seconds)));
    add('Fastest per item', wt.length ? (f => label(f) + ' · ' + fmtSec(num(f.seconds)))(wt.sort((a, b) => num(a.seconds) - num(b.seconds))[0]) : 'not reported here');
    const rec = c.rows.find(r => r.key === c.recommend);
    add('Recommended here', rec ? label(rec) : 'no single choice', 'rec');
    return g;
  }

  function chart(c, rows) {
    const box = $('cmp-chart'); box.replaceChildren();
    if (c.task === 'legal') {
      const k = legalView === 'cuad' ? 'cuad' : 'nli_n';
      [...rows].sort((a, b) => b[k] - a[k]).forEach(r => {
        const row = el('div', 'chart-row' + (r.key === c.recommend ? ' rec' : '')), lab = el('div', 'chart-label', r.model), tr = el('div', 'bar-track'), f = el('div', 'bar-fill');
        f.style.setProperty('--width', (r[k] / 30 * 100) + '%'); tr.append(f);
        if (k === 'cuad') { const m = el('span', 'base-mark'); m.style.left = '50%'; m.title = 'Always answering "absent": 15/30'; tr.append(m); }
        lab.append(el('small', '', r.truncated ? r.truncated + ' of 60 answers cut off' : 'no answers cut off'));
        row.append(lab, tr, el('div', 'chart-value', r[k] + '/30')); box.append(row);
      });
      return;
    }
    const sorted = [...rows].sort((a, b) => c.lower_is_better ? a.score - b.score : b.score - a.score);
    const max = c.lower_is_better ? Math.max(...sorted.map(r => r.score), 0.001) : 1;
    sorted.forEach(r => {
      const row = el('div', 'chart-row' + (r.key === c.recommend ? ' rec' : '')), lab = el('div', 'chart-label', r.model), tr = el('div', 'bar-track'), f = el('div', 'bar-fill' + (r.key === c.recommend ? '' : ' alt'));
      lab.append(el('small', '', (r.method || '') + (r.machine ? ' · ' + r.machine : '') + (r.key === c.recommend ? ' · recommended' : '')));
      f.style.setProperty('--width', Math.max(0.5, r.score / max * 100) + '%'); tr.append(f);
      row.append(lab, tr, el('div', 'chart-value', fmtScore(c, r.score))); box.append(row);
    });
  }

  function table(c, rows) {
    const head = $('cmp-head'), body = $('cmp-body'); head.replaceChildren(); body.replaceChildren();
    const cols = c.task === 'legal' ? ['Configuration', 'CUAD correct /30', 'ContractNLI correct /30', 'Cut off (of 60)']
      : ['Configuration', c.metric, c.items[0].toUpperCase() + c.items.slice(1) + ' tested', 'Processing failures', 'Reference numbers recovered', 'Median time per item'];
    cols.forEach(h => { const th = el('th', '', h); th.scope = 'col'; head.append(th); });
    const list = c.task === 'legal' ? rows : [...rows].sort((a, b) => c.lower_is_better ? a.score - b.score : b.score - a.score);
    list.forEach(r => {
      const tr = el('tr', r.key === c.recommend ? 'rec' : ''), td = el('td', '', r.model);
      if (r.method) td.append(el('small', '', r.method));
      if (r.machine) td.append(el('small', '', r.machine));
      if (r.key === c.recommend) td.append(el('span', 'tag', 'Recommended'));
      tr.append(td);
      const vals = c.task === 'legal' ? [r.cuad, r.nli_n, r.truncated]
        : [fmtScore(c, r.score), r.cases.toLocaleString(), r.failed === null || r.failed === undefined ? NR : r.failed, fmtPct(num(r.numbers)), fmtSec(num(r.seconds))];
      vals.forEach(v => tr.append(el('td', '', String(v))));
      body.append(tr);
    });
  }

  function render(push) {
    const c = cur;
    renderFilters();
    const rows = c.task === 'legal' || method === 'all' ? c.rows : c.rows.filter(r => r.method === method);
    $('cmp-eyebrow').textContent = c.track.toUpperCase() + ' · ' + machineOf(c).toUpperCase();
    $('cmp-title').textContent = c.title;
    const pills = $('cmp-pills'); pills.replaceChildren(el('span', 'stage-pill' + (c.confirmatory ? ' conf' : ''), c.stage));
    $('cmp-question').textContent = c.question;
    $('cmp-stage').textContent = c.stage_note + ' ' + c.metric + ': ' + c.metric_note + (c.lower_is_better ? '' : ' Higher is better.');
    const g = $('cmp-glance'); g.replaceChildren(glance(c, rows));
    chart(c, rows); table(c, rows);
    $('cmp-meaning').textContent = c.meaning;
    const lim = $('cmp-limits'); lim.replaceChildren(el('b', '', 'Limits: '), document.createTextNode(c.limits + ' '));
    if (c.task !== 'legal') lim.append(document.createTextNode('Failed or cut-off attempts score zero and stay in the averages. Zero processing failures does not mean zero mistakes. Median time is per request on the stated machine, excluding model loading. "Not reported" means the source did not record it. '));
    (c.sources || []).forEach((s, i) => { if (i === 0) lim.append(el('b', '', 'Sources: ')); const a = el('a', '', s.label); a.href = s.url; lim.append(a); if (i < c.sources.length - 1) lim.append(document.createTextNode(' · ')); });
    const hash = '#cmp=' + c.id + (method !== 'all' && c.task !== 'legal' ? '&method=' + encodeURIComponent(method) : '') + (c.task === 'legal' && legalView === 'cuad' ? '&show=cuad' : '');
    if (push) history.pushState(null, '', hash); else if (location.hash !== hash && location.hash.startsWith('#cmp=')) history.replaceState(null, '', hash);
  }

  function go(id, push) { cur = comps.find(x => x.id === id) || comps[0]; render(push); }

  function fromHash(scroll) {
    const h = decodeURIComponent(location.hash.slice(1));
    let id = null, moved = false;
    if (h.startsWith('cmp=')) { const p = new URLSearchParams(h); id = p.get('cmp'); method = p.get('method') || 'all'; legalView = p.get('show') === 'cuad' ? 'cuad' : 'nli'; }
    else if (h.startsWith('explorer?')) { id = legacyId(h.split('?')[1]); moved = true; }
    else return false;
    const known = comps.some(x => x.id === id);
    go(known ? id : 'tables-final', false);
    $('cmp-redirect').textContent = moved || !known ? 'That link pointed to an older view, so the closest recorded comparison is shown.' : '';
    if (moved || !known) history.replaceState(null, '', '#cmp=' + cur.id);
    if (scroll) $('explorer').scrollIntoView();
    return true;
  }

  function wire() {
    $('f-task').addEventListener('change', e => { const first = comps.find(x => x.task === e.target.value && x.confirmatory) || comps.find(x => x.task === e.target.value); method = 'all'; go(first.id, true); });
    $('f-machine').addEventListener('change', e => { const first = comps.find(x => x.task === cur.task && x.side === e.target.value); method = 'all'; go(first.id, true); });
    $('f-set').addEventListener('change', e => { method = 'all'; go(e.target.value, true); });
    $('f-method').addEventListener('change', e => { if (cur.task === 'legal') legalView = e.target.value; else method = e.target.value; render(true); });
    $('f-reset').addEventListener('click', () => { method = 'all'; legalView = 'nli'; go('tables-final', true); });
    $('cmp-csv').addEventListener('click', () => {
      const c = cur, cols = c.task === 'legal' ? ['model', 'cuad', 'nli_n', 'truncated'] : ['model', 'method', 'machine', 'score', 'cases', 'failed', 'numbers', 'seconds'];
      const q = v => '"' + String(v ?? '').replaceAll('"', '""') + '"';
      const text = [['comparison', ...cols].map(q).join(','), ...c.rows.map(r => [c.id, ...cols.map(k => r[k])].map(q).join(','))].join('\r\n');
      const a = el('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' })); a.download = c.id + '.csv'; a.click();
    });
    window.addEventListener('popstate', () => fromHash(false));
    window.addEventListener('hashchange', () => fromHash(false));
  }

  fetch('data/comparisons.json').then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(d => {
    comps = d.comparisons; wire();
    if (!fromHash(true)) go('tables-final', false);
  }).catch(() => { $('cmp-title').textContent = 'The comparison data did not load. Open this page from the website, or use the reports below.'; });
})();
