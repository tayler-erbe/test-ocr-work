# Website revision status

Revision of 29 October 2026 against `docs/website-review-notes.md` (28 sections). Verified by `python -X utf8 tools/build_site.py --check` (part of `tools/check_project.py` through `tests/test_site.py`), a browser click-through of every comparison, phone-width overflow checks (390 px, mobile emulation), PDF checks (page numbers, links), and the full project checks.

## What changed

- **`index.html`** is the decision brief. In the owner's order: findings, hardware and budget, results, method, next steps, reports. It opens with the answer and the author.
- **`technical.html`** is the evidence page. It covers what was tested, the hardware fit, the results explorer, what each task looks like, the contract track, the methods, the service design and the resources.
- **The explorer** now offers 18 named comparisons, each populated by construction, instead of four free filters. It has machine filters, deep links (`#cmp=…`), working back and forward, and old links mapped to the nearest comparison.
- **Reports** are seven readable pages under `site/reports/`, each with a matching PDF in `site/downloads/`. The decision brief is also a PDF.
- **The previous detailed page** is preserved as `technical-archive.html`.
- **Build and checks**: `tools/build_site.py` generates the comparisons, report pages and PDFs, and validates them. `tests/test_site.py` runs that validation in the project checks.

## Section by section

| # | Requirement | Status | Where |
|---|---|---|---|
| 1 | No empty explorer views | Done. Every comparison has rows. Old empty paths redirect, with a note. | Explorer; `build_site.py` check |
| 2 | Final advisory as a real PDF | Done. All reports have PDFs with page numbers and links. | Resources, `downloads/*.pdf` |
| 3 | Replace activity counters | Done. Counters removed. Scope is explained in "What was tested". | Evidence page, findings |
| 4 | Name hardware and cost | Done. Tested machines, targets, and six tiers with dated complete-system prices. CPU and system memory for the desktop were not recorded, so none is stated. | Brief, hardware; evidence page, hardware |
| 5 | Chart sample context | Done. Source, construction (validation split, chart-level hash split), skills, correlation and limits. | Evidence page, methods |
| 6 | Why several rounds | Done. Question, test, finding and decision per round, plus why the work stopped. | Brief, method |
| 7 | Lead with supported recommendations | Done. Six job cards (model, why, evidence, limit, next), plus why the top score is not always the recommendation. | Brief, findings |
| 8 | Translate metrics and labels | Done. Plain names at the point of use and a glossary. No hypothesis labels in headlines. | Explorer; methods glossary |
| 9 | Show inputs and outputs | Done with labelled illustrations, not benchmark items or recorded outputs. Real public examples need the owner to choose them and confirm licences. | Evidence page, "What each task looks like" |
| 10 | Links land on their evidence | Done. Each card links to its own comparison. | Brief cards; explorer deep links |
| 11 | Preserve the explorer and the original | Done. Explorer kept and rebuilt; previous page archived. | `technical-archive.html` |
| 12 | Meaningful evaluation stages | Done. Stage names are plain, and each comparison explains its own stage. | Explorer panel |
| 13 | Explain methods, columns and the recommendation together | Done. Plain column names, "not reported" distinct from zero, median and failure definitions, at-a-glance best text, best numbers, fastest and recommended. | Explorer panel |
| 14 | Actionable page-text advice | Done. A per-comparison "What this means". Round-2 failures and timings are restored from the audit. | Page comparisons |
| 15 | Rename and populate crop OCR | Done. Now "Text-region OCR" and "Cropped text regions", with existing development results. | Explorer, findings |
| 16 | Explain tables; replace the hardware filter | Done. Machine is shown on every comparison, and machine filters only narrow the list. | Explorer |
| 17 | Laptop results discoverable | Done. The laptop filter shows 6 comparisons covering all five laptop task types. No single-option selectors. | Explorer |
| 18 | Resolve the perceived absence of laptop work | Done. Coverage is in `docs/website-data-audit.md`. Laptop work is listed on both pages. | Evidence page, hardware; explorer |
| 19 | Hardware led by capability and budget | Done. Each tier says what it runs, then the price, and whether it was measured or estimated. | Brief, hardware |
| 20 | GPT-OSS discoverable | Done. Findings card, model list, contract section and explorer. | Brief; evidence page |
| 21 | Reports as web pages and PDFs | Done. Seven report pages, each with "Download PDF". No reader link opens Markdown (checked by script). | `site/reports/` |
| 22 | Leadership-first writing | Done. Each section and card opens with the takeaway. Detail follows. | Both pages |
| 23 | Vote3, percentage points, task winners | Done. Absolute scores, the meaning of a point, and that a larger gain is not a better final score. | Evidence page, methods |
| 24 | Multi-model pipeline and batching | Done. Six-step service, batching, backlog versus intake, and design requirements, marked as proposed. | Brief and evidence page, next steps |
| 25 | Explain the contract track first | Done. Purpose, datasets, denominators, cut-off answers, and settings versus models. | Evidence page, contract track |
| 26 | Visualise the contract findings | Done. Chart with the CUAD always-absent baseline, plus a conclusion: recommended, alternative, what failed, next. | Brief results; evidence page |
| 27 | Full story in findings; resources by audience | Done. Contract work is in the findings. Resources are ordered reports, then data, then code. | Both pages |
| 28 | Complete budget tiers | Done. Laptop and desktop class prices added (October 2026 listings, marked to refresh). L4 versus L40S reasoning is given as a question for the pilot. | Brief, hardware |

## For the owner

- The new prose was written directly, not drafted through the ChatGPT helper, because its ledger is near the cap. Approve it or ask for a ChatGPT pass.
- Laptop and desktop prices are retail listings found in October 2026. The retailer pages could not be opened to confirm them, so refresh them before quoting.
- Dataset licences were not stated on the site. Confirm them before adding any real benchmark images.
