# Evidence-by-ID extraction: implementation and exploratory results (20 Oct 2026)

Step 4 of the extraction plan (nemotron-failure-analysis.md section 8; evidence-and-fields.md), built and run on the desktop with local models only: Qwen3-32B (Ollama 0.34.4, digest 030ee887880f) and Qwen3-VL-32B-Instruct-AWQ (vLLM, served name qwen3vl32b). No Claude model read any document. Public data only (the 24-case input pack).

**Exploratory only.** 12 CUAD and 12 ContractNLI questions, all previously seen during diagnostics; only 6 of the 12 CUAD questions are positives. One question moves a score by about 8 points. No production claim.

## What was built (`evidence_by_id.py`, 33 tests in `test_evidence_by_id.py`)

1. **Source blocks.** Each source span, or each OCR line via `blocks_from_ocr_lines` (keeps page and bounding box), is split into sentence/clause blocks with stable IDs `<span>.<k>`. Abbreviations, clause numbers and single letters don't end a block; fragments under 25 characters merge into the previous block. Concatenating a span's blocks reproduces the span exactly (checked on build). `SourceStore` is immutable and re-checks the document fingerprint before every copy.
2. **The model selects; code copies.** The model returns block IDs (trimmed modes: block ID + character offsets, or block ID + exact first/last words). Rejected: unknown IDs, duplicates, out-of-range/empty/whitespace offsets, overlaps, anchors missing/repeated/out of order within the cited block, wrong shapes, more than 30 items. No fuzzy repair, no reassignment to another block.
3. **Explicit outcomes:** `found`, `not_found_in_excerpts`, `not_present_after_full_review` (offered only with the whole document in context), `insufficient_evidence` (candidates kept for review, not accepted), `unreadable`. A failed request is a record status, never an outcome.
4. **Separate stages:** single call or two-stage (outcome first, evidence only if found); per-field or multi-field requests (a bad field doesn't discard the others); a value stage (`normalize_money`) that requires the value to appear verbatim in the copied evidence (unit-tested only; CUAD has no value key).
5. **Coverage before the call:** source coverage (no key) and reference coverage (scoring-only key, evaluation only), logged per case, never in a prompt.
6. **Scoring unchanged:** accepted evidence is converted to the frozen response shape and scored by the unchanged `validate_response` and `score`.

## Ceiling measured before any model call (diagnostic, uses the key)

Selecting exactly the gold-overlapping blocks: excerpts pass 1 of 6 positives (3 of 6 have no gold text in the excerpts); whole documents pass 2 of 6. Short answers (document name, date, parties) are far shorter than a sentence, so whole-block evidence fails the scorer's 0.8 word-overlap rule. With whole blocks, strict CUAD gains can only come from absent cases.

## Results

| Model, arm | CUAD strict | positives / absents | failed | present/absent right | evidence F1 | char precision | char recall (pos) | NLI strict |
|---|---|---|---|---|---|---|---|---|
| Qwen3-32B baseline | 5/12 | 1/6, 4/6 | 2 | 7/12 | 0.443 | | | 9/12 |
| Qwen3-32B id_x | 6/12 | 1/6, 5/6 | 0 | 8/12 | 0.589 | 0.556 | 0.418 | 9/12 |
| Qwen3-32B two_x | 7/12 | 1/6, 6/6 | 0 | 9/12 | 0.672 | 0.742 | 0.418 | |
| Qwen3-32B trim_x | 5/12 | 1/6, 4/6 | 2 | 7/10 | 0.461 | 0.306 | 0.400 | |
| Qwen3-32B fulldoc baseline | 4/11 | 0/6, 4/5 | 4 | 10/11 | 0.467 | | | 9/12 |
| Qwen3-32B id_full | 6/11 | 1/6, 5/5 | 0 | 11/11 | 0.716 | 0.426 | 0.770 | 9/12 |
| Qwen3-32B trim_full | 4/11 | 0/6, 4/5 | 4 | 7/7 | 0.468 | 0.254 | 1.000 | |
| Qwen3-VL-32B baseline | 5/12 | 1/6, 4/6 | 3 | 9/12 | 0.478 | | | 8/12 |
| Qwen3-VL-32B id_x | 5/12 | 1/6, 4/6 | 0 | 9/12 | 0.554 | 0.318 | 0.480 | 9/12 |
| Qwen3-VL-32B two_x | 5/12 | 1/6, 4/6 | 0 | 8/12 | 0.536 | 0.371 | 0.480 | |
| Qwen3-VL-32B trim_x | 5/12 | 1/6, 4/6 | 3 | 8/9 | 0.479 | 0.306 | 0.400 | |

Arms: `id` whole blocks by ID; `trim` adds first/last words; `two` outcome first, then evidence; `_x` excerpts; `_full` whole document (one 52,712-token document doesn't fit 32,768 and was not run in any arm). No truncation; no reasoning observed with thinking off. Block-ID calls used about 13-40 output tokens (anchors about 120-140); median latency about 1-4 s per case.

Paired against the same model's baseline (exact McNemar; none significant at this size): id_full fixed 2, broke 0 (p = 0.5); two_x fixed 2, broke 0 (p = 0.5); Qwen3-32B id_x fixed 1, broke 0; Qwen3-VL id_x CUAD 0/0, NLI fixed 2, broke 1.

## Findings

1. **Block-ID selection removes copy failures:** 0 failed requests and 100% valid items in every ID arm, against 2-4 failed requests per baseline arm.
2. **Strict gains come from absent-field handling, not better positives:** whole document + IDs made the present/absent call right 11 of 11; two_x got all 6 absents right; positives stayed at 1/6 everywhere (the whole-block ceiling).
3. **Whole documents + IDs found the most answer text** (char recall 0.77 vs 0.42 on excerpts) at precision 0.43 (whole blocks carry extra text).
4. **First/last-word trimming did not fix precision:** the model attached anchors to the wrong block ID (the words exist in a neighbouring block), the same binding failure as generated quotes; 2-4 failed requests and 66-75% valid items, correctly rejected by code.
5. **NLI unchanged** at 9/12 for both models with block IDs mapped to span IDs.
6. **Two-stage is the most conservative arm:** never called an absent field found, but called some positives absent (3 found for 6 positives).

## Next steps to consider (not decided)

- Make block-ID selection with explicit outcomes the default (zero copy failures, correct abstention).
- Close the precision gap in code, not model-written text: finer clause-level blocks, or a second ID-only pass over sub-blocks of the chosen blocks; measure against the ceiling first.
- Report character precision/recall and present/absent accuracy beside strict CUAD.
- Confirm on a fresh set with document-level uncertainty before any adoption decision.

## Files

`evidence_by_id.py`, `test_evidence_by_id.py` (repo root); in this folder: `run_evid.py`, `run_qwen3_32b_window.py`, `summary.json`, `paired.json`, `.gitignore` (keeps `local/` raw answers out of git).
