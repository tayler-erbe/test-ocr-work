# Round 3b and 3c results and routing recommendation (26 October 2026)

Pre-registration: `PREREG_3B.md`. Numbers: `results/vision/round3/stats.json` (paired, source-clustered bootstrap, 2,000 draws, seed 20261026), `parsers.json` (per-run means), `latency.json`, `replay_7b.json`, `PURGED.json`, and `results/legal/round3/*/summary.json`. Session narrative: `SESSION_2026-10-26.md`. All data public; the boundary of every claim is in section 5.

## 1. Confirmatory verdicts (fresh sets, equal 8,192-token budget, Holm over two hypotheses)

| Hypothesis | Cases | Primary metric: difference vs Qwen3-VL 32B AWQ [interval at the Holm level] | Numeric recall: difference [interval] | Holm alpha | Verdict |
|---|---|---|---|---|---|
| H1 PaddleOCR-VL-1.6 tables (FinTabNet.c) | 100 | TEDS +0.090 [+0.048, +0.139] | +0.042 [-0.008, +0.099] | 0.025 | **passed** |
| H2 Nemotron 3.5 Parse pages (fresh OmniDocBench) | 80 | word F1 +0.079 [+0.030, +0.135] | -0.001 [-0.047, +0.051] | 0.05 | **not passed**: lead on words, numeric part inconclusive |

PaddleOCR-VL-1.6 on tables: TEDS 0.852, numeric recall 0.974, zero failures, 1.25 s median per table. Nemotron Parse on pages: word F1 0.899, numeric recall 0.882, 1 failure in 80, 3.1 s median. H2's numeric point estimate is a tie; 80 pages give an interval about ±0.05 wide, so the 0.02 margin cannot be met with this sample. By the pre-registered rule that is "not a win", not "worse".

## 2. Supporting arms (exploratory; never pooled with section 1)

| Arm | Finding |
|---|---|
| Official pipelines | Nemotron Parse double and triple pass produced text identical to each other on all 180 fresh cases (the third stage added one request per case and changed nothing), and did not beat the single pass (page word F1 0.886 vs 0.899; table TEDS 0.804 vs 0.804). PaddleOCR-VL's official layout-plus-element pipeline repairs its whole-page weakness (word F1 0.922, +0.102 vs the 32B) but loses numbers (recall 0.771, -0.113) and does not beat the bare table prompt (TEDS 0.785 vs 0.852). |
| Budget sensitivity (confirm2 pages) | At 6,000, 8,192 and 12,288 tokens every parser's verdict is unchanged. The 12,288 recovery arm removes at most one failure per 80 pages (Parse 1 to 0, olmOCR 2 to 1, PaddleOCR 8 to 7); PaddleOCR's page failures are not a budget defect. The 32B at 8,744 instead of 6,000 changes no verdict. The 16,384 arm is unservable at the parsers' 16,384 context (purged, `PURGED.json`). |
| olmOCR-2 7B | Cleanest prose on every page set (+0.078 word F1 on the fresh pages) and the worst numbers everywhere (-0.178 numeric recall on the fresh pages, TEDS -0.057 on the fresh tables). Not for any page that carries amounts. |
| Reproducibility replay | The two Qwen2.5-VL 7B groups that differed across machines reproduce exactly on the desktop (260 of 260 cases identical). The discrepancy is machine-specific; the laptop replay (Codex) closes the question. |
| gpt-oss-20b seeds | Three seeds of the five temperature-1 arms on the 24-case pack move any arm by at most one case; none beats the deterministic baseline. |

## 3. Legal track on the identical 60 documents (CUAD and ContractNLI, 30 questions each, evidence by ID, 16k context, temperature 0)

| Model, reasoning | CUAD correct | ContractNLI correct | Truncated |
|---|---|---|---|
| Qwen3 32B, think off | 14 | 18 | 0 |
| Qwen3 32B, think on | 15 | 16 | 0 |
| gpt-oss-20b, reasoning low | 15 | 14 | 0 |
| gpt-oss-20b, reasoning high | 11 | 4 | 19 |
| hosted Nemotron, reasoning on (earlier run, laptop) | 13 | 12 | |

Reading: Qwen3 32B and gpt-oss-20b are within one or two cases of each other on CUAD; Qwen3 32B leads on ContractNLI; both local models beat the hosted Nemotron configuration on both tasks. Reasoning mode helps neither and breaks gpt-oss at 16k. With 30 questions per task, differences under about four cases are noise. Qwen3 32B ran the 120 requests in 12 minutes on the desktop.

## 4. Throughput (packet of 20 pages and 20 tables, 8,192 budget, desktop RTX 5090)

| Model | Concurrency 1: cases/min, p50, p95 | Concurrency 4: cases/min, p50, p95 | VRAM class |
|---|---|---|---|
| Nemotron 3.5 Parse 0.63B | 44.7, 1.0 s, 3.3 s | 139.7, 1.2 s, 4.3 s | under 4 GB |
| PaddleOCR-VL-1.6 | 24.1, 1.3 s, 5.6 s | 73.0, 1.5 s, 5.8 s | under 4 GB |
| olmOCR-2 7B FP8 | 6.4, 6.6 s, 24.4 s | 19.1, 6.6 s, 25.3 s | about 10 GB |
| Qwen3-VL 32B AWQ | 3.7, 10.9 s, 26.3 s | 9.3, 11.8 s, 33.0 s | about 24 GB |

## 5. Routing recommendation for the pipeline builder

Among the candidates tested, on public benchmarks, under the stated budgets:

1. **Tables:** PaddleOCR-VL-1.6, bare table-recognition prompt, single pass, 8,192 tokens, vLLM. Confirmed (H1). Numeric recall 0.974 is still below the 99% bar, so amounts keep human review and a field-bound numeric check.
2. **Whole-page text:** Nemotron 3.5 Parse, single pass (multipass adds cost and nothing else). Best word F1 and 15 times the 32B's throughput; numbers equal to the 32B on the point estimate but unproven to the 0.02 margin, so route numeric-heavy pages through the table path or a numeric check. olmOCR-2 only for archival prose where numbers do not matter.
3. **Layout detection:** keep the YOLO detector; Parse's figure detection is far worse (-0.265 F1).
4. **Charts:** unchanged from round 2 (Qwen3-VL family with the round-2 routing).
5. **Clause extraction:** Qwen3 32B with thinking off as the default local legal model, gpt-oss-20b at low reasoning as an interchangeable second opinion; both with evidence by ID. Reasoning modes off. The hosted Nemotron configuration is behind both on this set.
6. **Operating envelope:** parsers at concurrency 4 on one 32 GB card; the 32B only where a parser is not applicable. Fail-zero stays the scoring rule; one retry at 12,288 tokens is cheap but recovers almost nothing.

Boundaries, unchanged from `AUDIT.md`: no target-domain documents (the acceptance set is still to be labelled); numeric correctness is bag-of-tokens recall, so a field-bound metric with false positives is the next measurement; no candidate reaches 99% on numbers; the 32B comparator is a 4-bit AWQ build; olmOCR-2's own toolkit was not run; the laptop feasibility sweep is Codex's.
