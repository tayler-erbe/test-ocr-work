# Local OCR and document intelligence: final advisory evaluation

Tayler Erbe · 27 October 2026 · Public benchmarks only. **Evaluation complete; production acceptance outstanding.**

## The problem this addresses

Business information often remains trapped inside attachments even after an ERP migration. One packet can combine narrative, scans, pricing tables, figures, charts and spreadsheets rendered as PDF. Searchable text alone is insufficient: an amount must remain linked to its row, unit, currency, document and source page. Where documents are private, locally hosted models offer a deployment option without sending inference inputs to a cloud provider. Local inference still requires access controls, approved storage, retention and network controls.

This study advises people evaluating research proposals and awards, procurement proposals, contracts, amendments, invoices, financial statements, scientific papers, archival material and technical reports. These are **potential applications**, not validated customer outcomes. Native spreadsheets should be parsed directly; packet assembly, cross-page tables and native workbook extraction were not established by this evaluation.

## What to try first

| Task | Recommended starting configuration | Evidence and restriction |
|---|---|---|
| Table crops / financial-report tables | PaddleOCR-VL-1.6, bare Table Recognition prompt, single pass, 8,192 output tokens | H1 passed against Qwen3-VL 32B AWQ on 100 FinTabNet.c tables from 87 source clusters. TEDS 0.8523; numeric recall 0.9739; zero failures. Review amounts: this is not 99% numeric fidelity. |
| Whole-page prose | Nemotron 3.5 Parse, single pass | 80 project-unused OmniDocBench pages: word F1 0.8989; numeric recall 0.8822; one failed page. H2 did NOT pass: improved word F1, but numeric non-inferiority remained inconclusive. Candidate route with numeric review, not a confirmed overall winner. |
| Archival prose with low numeric sensitivity | olmOCR-2 7B FP8, tested bare adapter | Word F1 0.8979; numeric recall 0.7057 on those 80 pages. Its official toolkit was not evaluated; do not generalize this result to the complete vendor pipeline. |
| Table / figure detection | Existing DocLayout-YOLO route | Parse figure F1 was lower by 0.2646 on 120 layout cases; table F1 difference was not decisive. |
| Chart questions and chart-to-data | Existing task-specific Qwen3-VL routes | Preserve round-2 routing. Self-check is not universally beneficial. Vote3 was confirmatory; self-check was supporting. |
| Legal clause extraction / document inference | Qwen3 32B thinking-off as a candidate; GPT-OSS 20B low reasoning as a smaller alternative | Same 60 public documents; modest strict scores, not unattended legal extraction. Evidence IDs with code-copied source text are the proposed production interface. GPT-OSS low is NOT reasoning off. |

These recommendations rank tested **configurations**, not every model or architecture. The conclusion depends on image quality, language, layout, scan degradation, fields, annotation definitions and available resources.

## Confirmatory comparisons

Two hypotheses were declared before the new-case runs, with a 0.02 numeric-recall non-inferiority margin. Both sides used 8,192 output tokens but their documented image sizes differed. Statistics used paired source-cluster bootstrap, 2,000 draws, seed 20261026, and Holm adjustment across the two hypotheses. Project-unused does not mean absent from model training.

| Hypothesis | Primary difference vs 32B AWQ | Numeric-recall difference | Conclusion |
|---|---|---|---|
| H1: PaddleOCR-VL tables, 100 cases / 87 clusters | TEDS +0.0898; Holm-level interval +0.0478 to +0.1394 | +0.0417; interval -0.0079 to +0.0994 | Passed both requirements. Numeric superiority itself was not established by this interval. |
| H2: Parse pages, 80 cases / 80 clusters | Word F1 +0.0794; interval +0.0303 to +0.1348 | -0.0012; interval -0.0473 to +0.0509 | Word improvement supported; cannot rule out a numeric deficit exceeding 0.02. Overall hypothesis not passed. |

See [machine-readable closeout](https://github.com/tayler-erbe/test-ocr-work/blob/main/results/FINAL_EVALUATION.json), [statistics](https://github.com/tayler-erbe/test-ocr-work/blob/main/results/vision/round3/stats.json), [parser aggregates](https://github.com/tayler-erbe/test-ocr-work/blob/main/results/vision/round3/parsers.json), and [pre-registration with amendments](https://github.com/tayler-erbe/test-ocr-work/blob/main/docs/round3/PREREG_3B.md). Reported bootstrap zero-tail estimates are finite simulation estimates, not zero-probability claims.

## Legal comparison: what actually changed

Each task has 30 questions on 30 documents. The table shows strict correctness requiring the frozen answer/evidence checks; request and validation failures count as zero. All configurations here used a 16,000-token OUTPUT budget, not a 16k context. The local Qwen3 context was 40,960, GPT-OSS 65,536; the hosted endpoint advertised 262,144. Same cases and scorer do not eliminate quantization, runtime, context and interface differences.

| Configuration | CUAD /30 | ContractNLI /30 | Truncated across 60 |
|---|---:|---:|---:|
| Qwen3 32B, thinking off | 14 | 18 | 0 |
| Qwen3 32B, thinking on | 15 | 16 | 0 |
| GPT-OSS 20B, reasoning low | 15 | 14 | 0 |
| GPT-OSS 20B, reasoning high | 11 | 4 | 19 |
| Hosted Nemotron Nano, reasoning on, earlier comparison | 13 | 12 | 2 |

Qwen3 thinking-off has the highest observed NLI count; the CUAD differences among the leading rows are small. No paired cross-model significance claim follows from these aggregate counts. GPT-OSS high reasoning truncated often under the fixed output budget; this does not prove an intrinsic inability to extract. Nemotron improved materially when reasoning was enabled in its own controlled comparison. It is not an irredeemable model verdict. The balanced CUAD set contains 15 absent fields: always abstaining would score 15/30 under the strict absent-answer rule, so even the best CUAD count is not adequate extraction. Three seeds of the exploratory sampling arms did not exceed the GPT-OSS diagnostic baseline.

The 60-case run uses the original quoting/evidence schema. The ID-selection arm is a separate exploratory configuration; do not call every benchmark response an evidence-by-ID response. Sources: [legal summaries](https://github.com/tayler-erbe/test-ocr-work/blob/main/results/legal/round3/), [Nemotron confirmation](https://github.com/tayler-erbe/test-ocr-work/blob/main/results/legal/nemotron-confirmation-2026-10-26.json).

## Speed, without promising a different GPU's performance

Measured on one RTX 5090 32 GB, with a fixed queue of 20 pages plus 20 tables and an 8,192-token cap. Rates count attempted cases, including failures; p95 is request latency, not a full-document SLA. Model startup is excluded. A small warm queue does not establish sustained backfill capacity.

| Configuration | Cases/min at concurrency 1 / 4 | Request p95 seconds at 1 / 4 | Failed cases at 1 / 4 |
|---|---:|---:|---:|
| Nemotron 3.5 Parse | 44.7 / 139.7 | 3.28 / 4.28 | 0 / 0 |
| PaddleOCR-VL-1.6 | 24.1 / 73.0 | 5.60 / 5.79 | 2 / 2 |
| olmOCR-2 FP8 | 6.4 / 19.1 | 24.43 / 25.25 | 1 / 1 |
| Qwen3-VL 32B AWQ | 3.7 / 9.3 | 26.31 / 33.03 | 2 / 2 |

Consult [latency.json](https://github.com/tayler-erbe/test-ocr-work/blob/main/results/vision/round3/latency.json) for exact recorded values. Deployment targets are a single L4 or L40S; no target-card run is claimed. Memory estimates and price tiers are in [hardware and budget guidance](hardware-and-budget.md). Cross-GPU speed/ranking extrapolations are hypotheses, not measured performance guarantees.

## What did not help, and what remains uncertain

- Broad page masking improved word overlap while dropping important numbers. It stays experimental for financial documents.
- Parse double/triple passes did not improve the selected single-pass result; extra calls do not automatically add value.
- Paddle's layout-plus-element pipeline improved whole-page word F1 to 0.9218 but numeric recall fell to 0.7706; it did not beat the bare table route on these table cases.
- Larger output caps recovered few parser failures. Invalid pre-inference runs were logged in [PURGED.json](https://github.com/tayler-erbe/test-ocr-work/blob/main/results/vision/round3/PURGED.json) and excluded as harness defects, with replacement runs labelled. Do not count those exclusions as model improvements.
- Replaying 260 cases on the desktop reproduced its stored 7B scores; a cross-machine disagreement remains unresolved. The withdrawn laptop sweep was not completed.
- Word F1 is word overlap, TEDS is a flattened-table similarity, and numeric recall is a bag-of-tokens metric. None proves the right amount is in the right field, or penalizes every invented number. Human scorer audit, field-bound numeric precision/recall, merged cells and cross-page evidence remain open.
- Model checkpoint aliases and helper versions are not uniformly weight-hash verified. Frozen benchmark contracts reproduce earlier behavior; they do not certify every new adapter as semantically correct.

## How to apply this to your data

Start with representative documents and the exact fields you need. Stratify by document type, source, scan quality, language and difficult numeric/layout cases. Label evidence with document/page/region identity; define present, absent, unreadable and ambiguous separately. Keep a document-disjoint holdout, independent double-labelled subset and adjudication record. Measure per-field accuracy, abstention, numeric fidelity, failures and reviewer time before estimating cost savings.

Fine-tuning **may** improve domain language, layouts or extraction conventions after enough consistent labels exist. It was not tested here and is not guaranteed to help. First distinguish OCR omissions, retrieval misses, schema mismatch and reasoning errors: training the text extractor will not repair text lost before extraction. Compare prompt/retrieval changes and fine-tuned models against the same locked holdout; retain the original baseline. No claim of complete open-source licensing applies to every model: check the exact weights, code, datasets and deployment terms separately.

The evaluation phase is closed. The next phase is a scalable, review-assisted intake pipeline with the routes above, read-only source connectors, idempotent jobs, page-level provenance, bounded retries, pause/resume, explicit failed/unread states and reviewed exports. See [implementation roadmap](roadmap.md). No more candidate testing or GPU sweep is scheduled by this closeout.

## Evidence availability

The repository contains the completed aggregate statistics and source code. The fresh round-3b image manifest and per-case round-3 outputs remain on the originating work machine and were not transferred here. Aggregate means alone cannot independently reproduce paired bootstrap intervals or audit each case. The reported intervals are imported, source-hashed computations, not independently re-scored in this closeout. Do not claim complete case-level replication from these files alone.
