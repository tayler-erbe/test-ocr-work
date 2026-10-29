# OCR routing report, 21 October 2026

Source: `merged/final/MERGED_REPORT.md`, produced by `tools/merge_results.py --round2` from the desktop export (22,731 rows) and the validated laptop export (18,244 rows, SHA-256 `ebc69a53...f5da753`, matches). Merged: 40,975 rows, 26 same-model comparison groups. Both exports passed `check_conformance.py --round2` (CONFORMANT). Everything below is scores and counts from code. No model output was read by a person or by the desktop operator. Failed cases count as zero.

## Status: prototype routing, not production approval

These results select candidate routes for the prototype. They do not approve anything for production. The best laptop crop OCR (8B) still has about 1.23% character error and 96.5% numeric recall, below the project's existing acceptance targets. Readiness is decided by human-labelled institutional documents (the annotation pilot), not by these public benchmarks.

## Routing choices

| Task | Route | Measured basis |
|---|---|---|
| Crop OCR (prose crops) | Qwen3-VL 8B instruct, baseline | Character error 1.2% vs 2.0% for Qwen2.5-VL 7B (50 crops each, laptop). 8B matches the desktop 32B models (1.1% to 1.2%) and runs in 2.6 s median on the laptop |
| Charts, question answering | Qwen3-VL 8B instruct, **self-check off**, baseline or upscale | 79.5% baseline (200 cases, laptop). Self-check drops it to 36.0%, a loss of 43 points (95% CI -51 to -35) |
| Charts, 7B fallback | Qwen2.5-VL 7B, **self-check on** | 52.5% to 79.0%, a gain of 26.5 points (CI +18.5 to +34), and +17.8 points on the v2 confirmation set (1,322 questions across 722 charts; questions on the same chart are not independent) |
| Chart to table | 8B with self-check or expert prompt | Score 0.42 to 0.93 (self-check), 60 cases. Baseline 8B is poor here |
| Tables | Any of the 8B variants, baseline is enough | TEDS 0.82 to 0.83, no variant differs significantly |
| Whole-page text masking (layoutmask) | **Experimental, not routed by default** | Helps 7B (+0.085) and the desktop 32B (+0.067); no gain on 8B (+0.010, CI includes 0). On the desktop 32B it lowers numeric recall: 0.909 to 0.720 on the 40 development pages, and 0.872 to 0.694 on the 80 confirmation pages (reported separately; different page sets) |
| Three-vote chart answers (vote3) | Use only with 7B or 32B | +0.045 on 7B (CI +0.030 to +0.061), +0.026 on 32B; no effect on 8B (-0.002, not significant) |

## Charts, question answering (relaxed accuracy, 200 development cases)

| Model | Baseline | Expert | Self-check | Upscale |
|---|---|---|---|---|
| Qwen2.5-VL 7B, laptop | 52.5% | 47.5% | **79.0%** | 47.5% |
| Qwen2.5-VL 7B, desktop | 53.5% | 44.5% | 80.0% | 49.0% |
| Qwen3-VL 8B instruct, laptop | **79.5%** | 75.0% | 36.0% | 80.0% |
| Qwen3-VL 8B instruct, desktop | 78.0% | 76.0% | 32.5% | 79.5% |
| Qwen3-VL 32B, desktop (reference) | 85.0% | 84.0% | 91.0% | 89.5% |

Round-2 confirmation (1,322 questions across 722 charts, laptop), change from baseline with 95% CI:

| Model | Variant | Change | 95% CI | Verdict |
|---|---|---|---|---|
| 7B | vote3 | +0.045 | +0.030 to +0.061 | better (confirmatory) |
| 7B | self-check | +0.178 | +0.150 to +0.207 | better (supporting) |
| 7B | upscale | -0.038 | -0.055 to -0.021 | worse |
| 8B | vote3 | -0.002 | -0.011 to +0.008 | not significant |
| 8B | self-check | -0.427 | -0.455 to -0.396 | worse |
| 8B | upscale | +0.015 | +0.003 to +0.027 | slightly better |
| 32B, desktop | vote3 | +0.026 | +0.014 to +0.037 | better (confirmatory) |

## Crop OCR (character error, lower is better, 50 crops)

| Model | Laptop | Desktop |
|---|---|---|
| Qwen3-VL 8B instruct | **0.012** | 0.012 |
| Qwen2.5-VL 7B | 0.020 | 0.018 |
| 32B-class models (desktop only) | n/a | 0.011 to 0.012 |

## Tables (TEDS, 60 cases) and chart data extraction

| Model | Table TEDS laptop | Table TEDS desktop | Chart to table laptop (baseline / self-check) |
|---|---|---|---|
| Qwen3-VL 8B instruct | 0.818 | 0.819 | 0.418 / 0.930 |
| Qwen2.5-VL 7B | 0.724 | 0.724 | 0.650 / 0.626 |

## Page masking (word F1)

| Model | Cases | Baseline | Layoutmask | Change [95% CI] |
|---|---|---|---|---|
| 7B, laptop | 80 | 0.757 | 0.843 | +0.085 [+0.039, +0.135] |
| 8B, laptop | 80 | 0.828 | 0.838 | +0.010 [-0.035, +0.050] |
| 32B, desktop | 80 | 0.814 | 0.881 | +0.067 [+0.033, +0.101] |

## Do the two machines agree?

Qwen2.5-VL 7B has the same weights on both machines. Of its 13 comparisons, 11 reproduced; 2 disagreed (chart_qa expert, +3.0 points; chart_table upscale, -14.8 points, a 60-case task). Crop OCR and tables reproduced.

## Caveats

- The 8B digest on the laptop (`70e58e37...b96eb`) differs from the desktop record. The merged report marks all 8B rows "different weights: not a reproduction test". The 8B comparison is a method comparison, not a reproduction. Even so, laptop and desktop 8B scores agree closely (for example crop error 0.0123 vs 0.0124).
- 7B and 8B results are not reproductions of the desktop 32B. The vote3 pick was made on 32B development data. On 7B and 8B it replicates the protocol with a different model, and does not count as a new selection.
- Many tasks have only 50 to 60 cases, so their intervals are wide. Holm-adjusted p-values are in the merged report. Only the round-2 confirmation set is large: 1,322 questions across 722 charts (questions cluster by chart, so the effective sample is smaller than 1,322) and 80 pages.
- Page masking stays experimental per the round-2 contract, and needs a numeric-recall check before use.
- Self-check's effect depends on the model and task. It helps 7B and the desktop 32B on chart answering, but hurts 8B. Route it per model and task, not globally.

Corrections, 21 Oct 2026 (Codex review): confirmation-set size stated as questions across charts; masking numeric-recall figures labelled by page set (40 development vs 80 confirmation); self-check wording changed to model- and task-dependent; prototype-not-production status added.
