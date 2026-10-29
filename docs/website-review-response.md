# Website review: second opinion

Written 29 October 2026 in response to `docs/website-review-notes.md`. Review only: no website, data or report has been changed. The reviewer read both live pages (the leadership briefing and the detailed case study), the explorer data, the final advisory and the committed results, and ran the read-only checks in section 2.

## 1. Verdict

The notes are right. Of the 28 sections, 25 should be implemented as written, and three should be reshaped (sections 9, 16 to 18 and 28, below). The notes also miss four things that matter for the audience (section 4).

The single biggest improvement is structural, not editorial. The detailed page makes the reader assemble a recommendation from four independent filters, unexplained stage labels and metrics. The fix is to lead with the decision, tell each comparison as a short story, and keep the explorer as the evidence layer underneath. Most of the 28 sections are symptoms of that one problem, so the revision should be designed once, around it, rather than as 28 separate patches.

The new leadership briefing (`site/index.html`) already does much of this well: one recommendation, task-by-task model choices, the clearest result, what is ready and the next decision. It is missing hardware and cost, the method, the legal conclusion, and any sign of who wrote it and why a reader should contact her.

## 2. What the checks showed

These were run against the committed results and the local run records, without new inference.

| Question in the notes | Finding | Consequence |
|---|---|---|
| Are laptop results missing? (16, 17, 18) | No. The dashboard data holds 30 laptop configuration summaries across five tasks. The filters hide them: no laptop row exists for Confirmation v3, and the default split carries over. | A navigation fix, not an evaluation gap. No new runs are needed to show laptop work. |
| Are the dashes for failures and time in Confirmation v2 missing data? (14, 17) | No. The run records hold them: on the desktop the 32B baseline and masking runs each have 1 failed page in 80, with mean times of about 18 s and 15 s. The laptop export holds 320 page rows. The dashboard was built from a report that did not carry those columns. | Re-import from the run exports, with provenance. Do not rerun anything. |
| Is GPT-OSS missing? (20) | No. It is in the legal table on the detailed page, outside the OCR explorer. | Discoverability and explanation only. |
| Do the legal scores mean what the tables suggest? (25, 26) | Only partly. The final advisory records that the 30 CUAD questions include 15 absent fields, so answering "absent" every time scores 15 out of 30. The best CUAD scores (14 and 15) are therefore no better than that trivial baseline. ContractNLI is where the models differ: Qwen3 32B with thinking off scored 18 out of 30. | The legal conclusion must lead with this. See section 5: the drafted article and LinkedIn post say both local models beat the hosted model "on both tasks", which is true in counts but misleading on CUAD. |
| Are numbers consistent across surfaces? | Not quite. The 32B table score shows as 0.763 on the leadership page and 0.762 elsewhere (the source value is 0.7625). | One source file for every displayed number, one rounding rule. |
| Are "roughly half the desktop decode speed" and "the model ranking should hold" supported? (19) | They are estimates from memory-bandwidth ratios (about 0.86 TB/s for an L40S and 0.3 TB/s for an L4, against 1.8 TB/s for the RTX 5090), not measurements. | Keep them only labelled as estimates, or drop them. |

## 3. Section-by-section position

| Sections | Position | Note |
|---|---|---|
| 1, 10, 12, 15 | Agree; solve together | All four come from free-combination filters. One redesign fixes them (section 4.2). |
| 2, 21 | Agree | Real PDFs and readable report pages. Generate both from one source so they cannot drift. |
| 3, 4, 5, 6 | Agree | Replace the activity counters with decision information. The round story (question, test, finding, decision) is the strongest proof of rigor the site has. Use it. |
| 7, 8, 13, 14, 23 | Agree | Plain-language metrics at the point of use. Keep "highest text score", "best numbers", "fastest" and "recommended" visibly separate. |
| 9 | Agree, with a constraint | Examples need care. Under the project's rule, the assistant may not view pages, crops or model outputs, so it cannot pick or check examples. The owner should choose them, or a local script can select them by a fixed rule with the owner checking them. Confirm each dataset's licence before showing its images. Labelled illustrations are the safe fallback. |
| 11, 22, 27 | Agree | Leadership-first writing is the main editorial rule. Preserve the explorer. |
| 16, 17, 18 | Agree with the goal; reshape the design | See section 4.2: replace the four filters with named comparisons, grouped by hardware. That gives hardware-first clarity without a dropdown that can dead-end. |
| 19 | Agree | Lead with what each tier enables, then the price. |
| 20, 25, 26 | Agree, and raise priority | The legal track needs its purpose stated first, the trivial baseline shown on the chart, and a conclusion led by ContractNLI. |
| 24 | Agree | Present the routed pipeline and backfill-versus-intake model as a proposal, clearly separate from measured results. |
| 28 | Agree, and the evidence already answers part of the value question | See section 4.3. |

## 4. What the notes do not yet cover

### 4.1 Show the method as the product

For the intended readers (hiring managers, recruiters, leadership deciding whether to invest), the most valuable thing on the site is not any single score. It is the repeatable way the decision was made. The site should state it as a method a reader could commission:

1. Define the document jobs and the failure that matters for each (for example, numbers in budgets).
2. Build frozen public stand-ins with answer keys, and fixed scoring code.
3. Shortlist candidates that fit the budget and hardware tier.
4. Explore on development data, write the hypotheses down, then confirm on unseen data.
5. Price the fit: which tier runs the winning route, at what dated cost.
6. Validate on representative domain documents before approving anything.

Show it as one short visual, link each step to where this evaluation did it, and say what a reader gets at the end of each step. That turns a case study into a credential.

### 4.2 Replace the filter explorer with named comparisons

Instead of four independent dropdowns (task, hardware, split, method), offer a short list of recorded comparisons, each a self-contained view. For example: "Final table test: 100 financial tables, desktop"; "Whole-page text, round 2: 80 pages, laptop"; "Chart questions, development: 200 questions, laptop and desktop". Group the list by hardware and by track, legal included. Each comparison carries:

- a one-line question it answers,
- the hardware it ran on,
- a chart,
- a three-line reading: best text, best numbers, recommended,
- its limits.

Every option is populated by construction, laptop work is visible at a glance, stage labels become plain descriptions, and old links can map to the nearest named comparison. This satisfies sections 1, 10, 12 and 15 to 18 with one design.

### 4.3 A budget decision the evidence already supports

The owner's value question (is a roughly $21,000 L40S system worth it?) has a partial answer in the existing results, and stating it is the kind of advice leadership needs:

- The recommended document-reading route uses models under 1B parameters plus an 8B model. All of them fit a 24 GB L4 by weight size, with room to spare.
- An L40S buys room for a 32B legal model beside the parsers, and more concurrency.
- On the 60 legal documents, gpt-oss-20b, which fits an L4, scored within noise of Qwen3 32B on CUAD. It was lower on ContractNLI (14 against 18 of 30).

So the evidence supports an L4-class pilot for document reading. Whether the L40S is worth it turns on two things: whether the ContractNLI gap matters for the real clause fields, and the throughput needed. Both are measurable in the pilot. Present this as a hypothesis with its test, beside the dated tier prices (existing PC; a 16 GB workstation at about $1,500 to $2,500; an L4 server at about $6,000 to $10,000; an L40S server at about $16,000 to $21,000), and add the measured desktop and laptop classes as section 28 asks.

### 4.4 Make the author and the next step visible

Neither page says who did the work, what she offers, or how to reach her. Add:

- a short author block (role, what she does, links to the portfolio case study, the article and LinkedIn),
- a dated "last updated" line,
- one call to action suited to the audience, such as discussing an evaluation for your own documents.

Keep the public site general. Organisation-specific versions belong in separate private briefs, not on this public repository.

## 5. Fix before anything else is published

The drafted Medium article and LinkedIn post (local drafts, not in this repository) say that both local models scored higher than the hosted model on both legal tasks. Given the 15-out-of-30 abstain baseline on CUAD, that sentence overstates the result. Recommended wording: on ContractNLI, Qwen3 32B with thinking off scored 18 of 30 against 12 for the hosted model; on CUAD, no configuration beat the always-absent baseline of 15. The portfolio page's legal table needs the same caveat.

## 6. Suggested order of work

1. **Correct before posting:** the legal wording in the article draft, LinkedIn post and portfolio page.
2. **Data audit:** re-import the round-2 failures and times from the run exports, unify rounding, and build one source file for every displayed number. Publish a hardware-by-task coverage table.
3. **Architecture:** the decision brief on top, with recommendations, hardware tiers and prices, the method and the author block. Track pages for tables, page text, charts and legal, each as question, test, result, meaning and limits. The named-comparison explorer underneath.
4. **Reports:** HTML report pages with matching PDFs for the final advisory, hardware and budget guide, and routing report.
5. **Examples and visuals:** owner-chosen or rule-selected public examples, licences checked; the legal chart with the baseline line; the pipeline proposal diagram.
6. **Consistency pass:** the site, the portfolio case study and the article say the same things with the same numbers. Then run the notes' acceptance checklist, including mobile, links and PDF rendering.

Two practical points for whoever implements this. Only one agent should own the site at a time, because the leadership page was already changed separately on 29 October. Also, the agreed rule is that public prose is drafted through the ChatGPT helper, but its spending ledger stands at about $28.60 of the $30 cap. A full rewrite needs the cap raised or a different drafting arrangement agreed.
