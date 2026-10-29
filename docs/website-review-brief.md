# Website review brief

Instructions for the reviewing agent. Written 29 October 2026. Read this whole file before opening the site.

Your job is to make the Document Intelligence Lab website the strongest possible public demonstration of one skill: choosing and justifying open-weight AI models for private document work under real budget and hardware limits. Review first and report. Do not edit anything until the owner approves your findings.

## 1. What the site must achieve

A reader should leave able to say, in their own words:

1. **The problem.** Organisations have valuable information locked in mixed PDF packets (research proposals and awards, procurement and supplier packets, contracts, financial and technical reports, scanned archives). It sits in tables, charts, scans and clauses that search cannot reach, and often cannot be sent to a cloud service.
2. **The answer.** Which open-weight model to start with for each job (tables, page text, charts, layout, clause extraction), why, and where it falls short.
3. **The cost.** What hardware runs that answer, roughly what it costs, and what remains unmeasured.
4. **The method.** How the decision was made, so the reader trusts it and could commission the same process for their own documents.
5. **The author.** Who did this, and how to reach her.

If any of the five is missing, unclear or buried, that is a high-severity finding.

## 2. The audience, and what each reader needs

Walk the site once as each reader. Time-box each walk. Record where they would stop, get confused or leave.

| Reader | Time they give it | Must come away with | Fails if |
|---|---|---|---|
| Recruiter or hiring manager arriving from LinkedIn | 60 seconds | "She can run a rigorous model evaluation and turn it into a business decision." The author, her role and a way to contact her. | They cannot tell who did the work, or what is impressive about it, from the first screen. |
| Executive or budget holder | 5 minutes | A recommendation per document job, a hardware tier with a dated price range, what is proven, what is not, and the next decision with its cost. | They must read a metric definition, a filter or a table before finding the recommendation and the price. |
| Owner of a document workflow (procurement, research administration, legal operations) | 10 minutes | Whether this applies to their documents, which parts are validated on public stand-ins, what a pilot would involve. | Applications read as validated claims, or nothing connects the tests to their kind of document. |
| Technical reviewer or data science peer | 20 minutes | That the claims hold: frozen protocols, pre-registration, intervals, failures kept, sources downloadable, code available. | A number cannot be traced to a file, or a caveat is missing where the claim needs it. |

The site is public and general. It must never name an employer, team, client, stakeholder, manager or any person other than the author. Organisation-specific versions are produced separately and privately.

## 3. Rules you must follow while reviewing

- **You may not read documents or model outputs.** Do not open, view, describe or judge benchmark page images, table or chart crops, scanned pages, extracted text or any model's answers, including any example images added to the site. Screenshots of the site's own layout, charts of aggregate numbers and text written for the site are fine. If a check needs someone to look at a document or an output, list it for the owner.
- **Run no inference.** Do not start models or use the GPU. The desktop GPU is shared with another session.
- **Never edit the frozen evaluation.** That means `tools/contract.json`, `tools/golden_scores.json`, frozen manifests and scorers.
- **Every public number must trace to a committed file.** Do not round differently from the source rule, and do not invent a number to fill a gap.
- **Do not strengthen a claim beyond its evidence.** Clearer wording must not imply stronger evidence.
- **Run `python -X utf8 tools/check_project.py` and include its result.** It must pass.

## 4. Sources of truth

| What | Where |
|---|---|
| Owner's requirements (28 sections and the acceptance checklist) | `docs/website-review-notes.md` |
| Second opinion and order of work | `docs/website-review-response.md` |
| Data audit and coverage after the first correction pass | `docs/website-data-audit.md`, `site/data/round2-audit.json`, `tools/audit_website_data.py` |
| Final vision results and the two pre-registered verdicts | `results/vision/round3/stats.json` (`holm` block), `parsers.json`, `latency.json`, `vlm_v3.json`, `replay_7b.json`, `docs/round3/RESULTS_3B.md`, `docs/round3/PREREG_3B.md` |
| Legal results | `results/legal/round3/*/summary.json`, `site/downloads/EVALUATION.md` |
| Hardware fit and budget | `docs/round3/TARGET_HARDWARE.md`, `site/downloads/hardware-and-budget.md` |
| Earlier rounds | `site/downloads/ROUTING_REPORT_2026-10-21.md`, `site/downloads/MERGED_REPORT.md`, `results/vision/exports/` |
| Site source | `site/index.html` (leadership briefing), `site/technical.html` (detailed case study), `site/app.js`, `site/data/benchmark.json` |
| Live site | https://tayler-erbe.github.io/test-ocr-work/ (served from `gh-pages`; may lag `main`) |
| Related public pages that must agree | https://taylererbe.com/document-intelligence-evaluation.html and the homepage card on taylererbe.com |

Review `main`, served locally with `python -m http.server` from `site/`. Note any difference from the live deployment separately.

## 5. Facts the site must state correctly

Check every occurrence on both pages, in downloads, and on the portfolio page.

- **Table recommendation.** PaddleOCR-VL-1.6 passed the pre-registered table test on 100 FinTabNet.c tables: 0.852 against 0.762 (32B source value 0.7625). TEDS is table similarity, not the share of correct tables. Numeric recall was 97.4% against 93.2%.
- **Page-text candidate.** Nemotron 3.5 Parse led on word F1 (0.899 against 0.820), but the numeric part of its test was inconclusive (88.2% against 88.3%, interval -0.047 to +0.051). It is a candidate with numeric checks, not a confirmed win.
- **No numeric bar met.** No model reached 99% numeric recall. Amounts need human review.
- **Legal.** The CUAD set has 15 absent fields, so always answering "absent" scores 15/30. No configuration beat it. ContractNLI separates the models: Qwen3 32B with thinking off scored 18/30, the hosted Nemotron configuration 12/30, gpt-oss-20b low reasoning 14/30. gpt-oss-20b high reasoning truncated 19 of 60. Low and high are settings of one model. No cross-model significance claim.
- **Hardware.** Selection ran on an RTX 5090 (32 GB). Earlier rounds also ran on a 12 GB laptop GPU. The deployment targets are one L4 (24 GB) or one L40S (48 GB), and fit is from weight sizes only. Neither card was benchmarked. Budget ranges are dated planning allowances, not quotes.
- **Desktop speeds are relative.** Desktop speeds compare models with each other. Any statement about target-card speed is an estimate and must say so.
- **Rounds.** Rounds 1 and 2 used Qwen vision models and methods (self-check, vote3, masking). Round 2 was pre-registered for vote3. Round 3 added the parsers and gpt-oss and was pre-registered for the two parser hypotheses. 3b and 3c were its confirmation and harness-error reruns. Describe them by the question each answered.

## 6. Review procedure

Work in this order and keep notes as you go.

1. **Baseline.** Run the project checks and the data audit script. Serve `main` locally. Take desktop (1440 px) and phone (390 px) screenshots of every page.
2. **Reader walks.** Do the four time-boxed walks from section 2. For each, write what they learned, where they stalled, and the first thing they would ask.
3. **Owner's requirements.** For each of the 28 sections in `docs/website-review-notes.md`, mark it met, partly met or not met, with the evidence: a screenshot region, a file and line, or a reproduction path.
4. **Explorer.** Test every reachable control combination, including links with old filter states in the URL. There must be no empty view, no option without results, and no caveat describing rows that are not shown. Laptop results must be findable without trial and error. Verify browser back and forward.
5. **Numbers.** List every number shown on either page and in the leadership PDF. Trace each one to its source file, and flag any that is unsourced, rounded inconsistently or used outside its scope. Script this rather than doing it by eye.
6. **Claims.** Check every sentence against the claim limits in section 7.
7. **Links and downloads.** Open every link and download. "Read" links must open a readable page, and "Download" links must deliver a real PDF with page numbers, readable tables and working links. Nothing reader-facing may open raw Markdown.
8. **Consistency.** The leadership page, the detailed case study, the PDFs, the portfolio page and the homepage card must give the same recommendations with the same numbers.
9. **Quality bar.** Check responsive layout, keyboard navigation, contrast, alt text, chart labels and dark-mode or print rendering where offered.

## 7. Claim limits

Flag any sentence that says or implies:

- that a model is production-ready, approved or suitable for unattended extraction;
- that local hosting makes the system secure, or compliant with a named regime;
- cost savings, return on investment, or a total cost of ownership;
- measured speed, capacity or concurrency on an L4 or L40S;
- that a model "understands" documents or gives legal advice;
- that public-benchmark results hold for the reader's own documents;
- that a higher score in one view beats a recommended model measured in a different set;
- a winner where the evidence says inconclusive or noise.

## 8. What "out of the park" looks like

Score each dimension from 1 to 5. The site is ready to share when every dimension scores 4 or more, and the first three score 5.

| Dimension | 5 means |
|---|---|
| First-screen clarity | In 60 seconds a recruiter knows what was done, why it is impressive, and who did it. |
| Decision usefulness | An executive finds the recommendation per job, the hardware tier and dated price, and the next step, without technical reading. |
| Trustworthiness | Every number traces to a file; caveats sit beside the claims they limit; nothing is overstated. |
| Method as credential | The six-step method (define jobs; freeze public stand-ins; shortlist by budget; confirm on unseen data; price the hardware; validate on real documents) is visible, linked to evidence, and reads as a service the author offers. |
| Applicability | Each document type the site names is mapped to the tested capability that stands in for it, with honest limits. |
| Evidence navigation | Named comparisons, never an empty view; each claim's link lands on its evidence. |
| Plain language | No unexplained abbreviation in a headline; metrics explained at the point of use; tone is direct, not simplistic. |
| Craft | Polished on desktop and phone; charts readable; PDFs clean; links work; consistent across all surfaces. |

Also check that the site has a short author block with a contact route, a dated "last updated" line, and one clear call to action for the audience.

## 9. What to deliver

Write `docs/website-review-findings.md` on a branch, not `main`, and give the owner a PDF copy. It should contain:

1. **Summary.** The rubric scores, the three most important problems, and a ready-to-share verdict (yes or no, with what blocks it).
2. **Findings table.** One row per finding: ID, severity (blocker, high, medium, low), page and location, what a reader experiences, evidence, recommended fix, and the source file that settles it.
3. **Requirements status.** Each of the 28 sections marked met, partly met or not met.
4. **Number trace.** Every displayed number with its source, and the mismatches.
5. **For the owner.** Anything that needs a human: choosing examples, licences, approving prose, any purchase-price refresh.
6. **Proposed fix plan.** Grouped and ordered, with what can be done without new evidence and what cannot.

Then stop and wait for approval before changing the site.

## 10. Housekeeping

- One agent owns `site/` at a time. Confirm no other session is editing it before you start.
- Public prose is drafted through the ChatGPT helper (`C:/dev/skyrule-fresh/.opencode/ops/openai_second_grader.py`), whose ledger is near its cap. Ask the owner before any large rewrite.
- Push nothing to `gh-pages` or `main` without the owner's approval.
