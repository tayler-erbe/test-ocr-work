# Round 3b pre-registration (written 26 October 2026, before any 3b run)

Round 3 found two leads on public data: PaddleOCR-VL-1.6 on tables and Nemotron 3.5 Parse on whole-page text. Both were found by looking at results, so they are exploratory. Round 3b tests them on frozen cases no model has seen in this project, under one output budget, with the comparison and the decision rule fixed here first. Everything else in 3b is a labelled supporting arm.

## Fresh confirmation sets (frozen by `tools/freeze_confirm3.py` before any run)

- `page_text_confirm3`: 80 OmniDocBench English pages with at least 300 characters of prose, none used by any earlier page task, selected by sorted content hash.
- `table_confirm3`: 100 table images from the FinTabNet.c test split (financial-report tables with structure and word annotations; the harness's own `acquire_datasets.py` already lists this source), selected by sorted content hash, with the source document recorded for clustering. Amended before any 3b table run: every one of the 219 eligible English OmniDocBench tables is already in an earlier set, so no unused OmniDocBench table exists. Gold HTML is built from the structure annotation by code (row and column boxes, spanning cells, words by centre), and that builder is frozen with the set. This moves the table test onto a different publisher's data and closer to the target domain, which also weakens the "publishers optimise toward this benchmark" objection for tables.
"Fresh" means unused in this project's recorded runs. It does not mean absent from any model's pretraining; OmniDocBench is public and the parser publishers report results on it.

## Equal budget

On the confirmation sets every model gets the same output budget, 8,192 tokens, and its own published image size. Truncated and failed answers score zero and stay in the denominator. This removes the budget confound of round 3 (6,000 for the vision models against 8,192 to 8,744 for the parsers).

## Confirmatory hypotheses

H1 (tables). PaddleOCR-VL-1.6, bare "Table Recognition:" prompt, single pass, beats Qwen3-VL 32B AWQ baseline on TEDS on `table_confirm3`, and its numeric recall is not worse by more than 0.02.
H2 (pages). Nemotron 3.5 Parse, single pass, beats Qwen3-VL 32B AWQ baseline on word F1 on `page_text_confirm3`, and its numeric recall is not worse by more than 0.02.

Test: paired difference per case, bootstrap resampling by source page (2,000 draws, seed 20261026), two-sided 95% interval. "Beats" means the interval for the difference excludes zero in the model's favour. "Not worse by more than 0.02" means the interval's lower bound for the numeric-recall difference is above −0.02. A hypothesis passes only if both parts hold. A lead that fails the numeric part is reported as "cleaner text, fewer numbers", not as a win. Holm correction over the two hypotheses.

Comparator weights: the same Qwen3-VL 32B AWQ build and the same vLLM serving as every earlier desktop row (digest recorded).

## Supporting arms (exploratory, reported beside the confirmatory rows, never pooled with them)

- Official pipelines on the same fresh sets: Nemotron Parse double and triple pass (its documented `DocumentParser` modes, temperature 0, top-k 1), PaddleOCR-VL-1.6 through its official layout-plus-element pipeline. olmOCR-2's toolkit is not run (no environment); its bare result stays labelled bare.
- Budget sensitivity on `page_text_confirm2`: the three parsers at 6,000 tokens and at 16,384 tokens; the 32B at 8,744. The 16,384 arm doubles as the bounded recovery arm: it shows what the round-3 truncations would have scored with one larger budget, reported with its time cost.
- Reproducibility replay: the two same-weight Qwen2.5-VL 7B comparison groups that did not reproduce across machines, rerun on the desktop; the laptop side is Codex's.
- Legal: Qwen3 32B on the 60-document reasoning contrast (think off versus on, 16k, temperature 0, the identical requests the hosted Nemotron and gpt-oss received). Estimands: each model's own reasoning contrast; and strict correctness across models on identical documents, paired by document, with gpt-oss labelled low versus high. Sampling arms of gpt-oss repeated with two more seeds on the 24-case pack; variability reported, never averaged into the single-pass row.
- Packet-level latency: one fixed queue of 20 pages and 20 tables from `*_confirm3`, run at concurrency 1 and 4 for each parser and for the 32B; p50 and p95 per request and wall clock per queue.

## What 3b does not do

No target-domain documents, no field-bound numeric metric, no structure-preserving table score. Those remain the stated boundary of the claim. Any statement about proposals or contracts still needs its own labelled set.

## Amendments after launch (26 October, evening)

1. The 16,384-token recovery arm cannot be served: every parser server runs with a 16,384-token context window, so prompt plus budget exceeds it and every request was rejected before inference (HTTP 400). Those rows are harness errors, not model failures; they are deleted (logged in `results/vision/round3/PURGED.json`) and the recovery arm is rerun at 12,288 tokens. Nothing about the confirmatory hypotheses changes.
2. The Nemotron Parse double and triple passes failed on a missing import in the runner before any model call. Same treatment: deleted, logged, rerun unchanged.

