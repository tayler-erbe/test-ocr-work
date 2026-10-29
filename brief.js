/* Interactive parts of the decision brief: headline-result tabs, hardware tier picker, rounds stepper. Content only, no data calls. */
'use strict';
(function () {
  const $ = id => document.getElementById(id);
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html !== undefined) e.innerHTML = html; return e; };

  function tabs(buttons, show) {
    buttons.forEach((b, i) => {
      b.addEventListener('click', () => show(i));
      b.addEventListener('keydown', e => {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft' && e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
        e.preventDefault();
        const n = (i + (e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length;
        show(n); buttons[n].focus();
      });
    });
  }

  // Headline results in the hero figure
  const hb = [...document.querySelectorAll('.hero-tabs button')];
  tabs(hb, n => hb.forEach((b, i) => { b.setAttribute('aria-selected', i === n); b.tabIndex = i === n ? 0 : -1; $(b.getAttribute('aria-controls')).hidden = i !== n; }));

  // Hardware tiers
  const TIERS = [
    { id: 'none', name: 'Existing computer, no GPU', short: 'Existing PC', price: '$0 extra', mem: 'Uses what you have', status: ['Not benchmarked', 'est'],
      runs: ['Read text and spreadsheets directly when the original file exists', 'Basic OCR and the review screens'],
      models: 'No AI models for scanned pages or charts.', basis: 'A starting point for native files, not a scanned-document solution.' },
    { id: 'ws16', name: '16 GB GPU workstation', short: '16 GB workstation', price: '$1,500 to $2,500', mem: 'One small model at a time', status: ['Estimated fit', 'est'],
      runs: ['Either recommended parser (about 1 to 2 GB of weights)', 'Qwen3-VL 8B for charts and text regions (about 10 GB)'],
      models: 'Tables and pages with the small parsers, charts with the 8B. Contract models do not fit comfortably.', basis: 'Fit from weight sizes; not tested. Planning allowance from the hardware guide.' },
    { id: 'laptop', name: '12 GB mobile workstation', short: 'Laptop, 12 GB · tested', price: 'About $4,650 new', mem: 'RTX 4000 Ada Laptop GPU, 64 GB system memory', status: ['Measured', ''],
      runs: ['Qwen3-VL 8B and Qwen2.5-VL 7B on tables, charts, chart-to-table, text regions and whole pages, one model at a time'],
      models: 'The 8B matched the 32B on text regions (1.2% character error) and tables (0.818 similarity).', basis: 'Retail list price for a comparable configuration, October 2026. Refurbished units cost far less.' },
    { id: 'desktop', name: '32 GB desktop, RTX 5090', short: 'Desktop, 32 GB · tested', price: 'About $3,600 to $5,300', mem: 'Where every final-round model was measured', status: ['Measured', ''],
      runs: ['All parsers and vision models, the 32B models and gpt-oss-20b', 'The two recommended parsers: 73 to 140 items a minute; the 32B vision model: 9'],
      models: 'Everything in this study except the hosted API ran here.', basis: 'Complete prebuilt systems listed in 2026. Graphics-card shortages move these prices.' },
    { id: 'l4', name: 'Single NVIDIA L4 server', short: 'L4 server, 24 GB · target', price: '$6,000 to $10,000', mem: '24 GB data-centre card, low power', status: ['Estimated fit · not benchmarked', 'est'],
      runs: ['Both recommended parsers, with room to spare', 'Qwen3-VL 8B for charts and text regions', 'gpt-oss-20b for contract questions'],
      models: 'Covers every document-reading route. Any 32B model is tight.', basis: 'Fit from weight sizes. Dated planning allowance, not a quote.' },
    { id: 'l40s', name: 'Single NVIDIA L40S server', short: 'L40S server, 48 GB · target', price: '$16,000 to $21,000', mem: '48 GB: room for a large model beside a parser', status: ['Estimated fit · not benchmarked', 'est'],
      runs: ['Everything recommended, including Qwen3 32B for contract questions', 'Qwen3-VL 32B with voting for charts', 'Headroom for several requests at once'],
      models: 'Buys the best contract result (18 of 30 on ContractNLI) and concurrency.', basis: 'Fit from weight sizes. Dated planning allowance, not a quote.' }
  ];
  const picker = $('tier-picker'), detail = $('tier-detail');
  if (picker && detail) {
    const btns = TIERS.map(t => { const b = el('button', '', `<span>${t.short}<small>${t.mem}</small></span><b>${t.price}</b>`); b.type = 'button'; b.setAttribute('role', 'tab'); picker.append(b); return b; });
    const show = n => {
      const t = TIERS[n];
      btns.forEach((b, i) => { b.setAttribute('aria-selected', i === n); b.tabIndex = i === n ? 0 : -1; });
      detail.innerHTML = `<p class="eyebrow">${t.name.toUpperCase()}</p><p class="price">${t.price}</p><p class="mem">${t.mem}</p>`
        + `<span class="measured ${t.status[1]}">${t.status[0]}</span><h4>What it runs</h4><ul>${t.runs.map(r => `<li>${r}</li>`).join('')}</ul>`
        + `<h4>What that means</h4><p>${t.models}</p><p class="basis">${t.basis}</p>`;
    };
    tabs(btns, show); show(4);
    const pt = $('print-tiers');
    if (pt) pt.innerHTML = '<table class="fit-table"><thead><tr><th>Tier</th><th>Price</th><th>Runs</th><th>Basis</th></tr></thead><tbody>' + TIERS.map(t => `<tr><td>${t.name}</td><td>${t.price}</td><td>${t.runs.join('; ')}</td><td>${t.status[0]}. ${t.basis}</td></tr>`).join('') + '</tbody></table>';
  }

  // Rounds stepper
  const ROUNDS = [
    ['Round 1', 'Vision models', 'Which local vision model reads each part of a document, on a 12 GB laptop and a 32 GB desktop?', 'Five vision models and several prompting methods on frozen public sets for text, tables, charts and pages.', 'The 8B model matched the 32B on text and tables. Prompting methods helped some models and hurt others.', 'Route by model and task. Test the promising methods properly.'],
    ['Round 2', 'Pre-registered', 'Do the chosen methods hold on data no model has seen?', 'Three-answer voting on 1,322 new chart questions and layout masking on 80 new pages, with the pass rules written first.', 'Voting helped the 7B and 32B, not the 8B. Masking cleaned up text but lost numbers.', 'Keep voting optional, keep masking experimental, and look for specialist tools.'],
    ['Contract track', 'Text models', 'Can models answer contract questions with evidence a reviewer can check?', 'CUAD and ContractNLI public contracts, quoting versus selecting evidence by ID, and a controlled reassessment of a hosted model.', 'Selecting evidence by ID removed copy failures. The hosted model\'s poor first score was a configuration problem.', 'Compare every candidate on the same 60 documents.'],
    ['Round 3', 'New candidates', 'Do specialist document parsers or gpt-oss-20b beat the incumbents?', 'Three parsers on every earlier page and table set, and gpt-oss-20b on the contract sets.', 'Leads emerged: PaddleOCR-VL for tables, Nemotron Parse for pages. They were found by looking, so they were not yet proof.', 'Write the two hypotheses down and test them on fresh data.'],
    ['Rounds 3b and 3c', 'Confirmation', 'Do the leads hold on unseen data, with the same output limit for every model?', '100 new financial tables and 80 new pages, the parsers\' official pipelines, budget checks, and Qwen3 32B on the 60 contract documents. 3c reran two arms that had failed for software reasons.', 'The table lead was confirmed. The page lead held on text but was inconclusive on numbers. Official pipelines did not beat a single pass.', 'Close the evaluation, route by task, and validate on real documents.']
  ];
  const rt = document.querySelector('#rounds .round-tabs'), rp = $('round-panels');
  if (rt && rp) {
    const panels = ROUNDS.map(r => { const p = el('div', 'round-panel', ['Question', 'Test', 'Finding', 'Decision'].map((h, i) => `<div><b>${h}</b><p>${r[i + 2]}</p></div>`).join('')); p.setAttribute('role', 'tabpanel'); rp.append(p); return p; });
    const btns = ROUNDS.map(r => { const b = el('button', '', `${r[0]}<small>${r[1]}</small>`); b.type = 'button'; b.setAttribute('role', 'tab'); rt.append(b); return b; });
    const show = n => { btns.forEach((b, i) => { b.setAttribute('aria-selected', i === n); b.tabIndex = i === n ? 0 : -1; }); panels.forEach((p, i) => { p.hidden = i !== n; }); };
    tabs(btns, show); show(4);
  }
})();
