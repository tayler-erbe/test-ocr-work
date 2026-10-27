# Vision evaluation, round 2: improvements (20 Oct 2026)

All reading was done by local models (Qwen3-VL-32B AWQ on vLLM, DocLayout-YOLO). No the desktop operator model saw any image or document; the desktop operator wrote code and orchestrated only.

## Verdict

Two improvements passed their pre-registered confirmation tests on fresh, never-used data. Both remain significant after Holm correction across the two confirmatory tests.

| Task | Method | Baseline | Improved | Change (95% CI) | Test |
|---|---|---:|---:|---:|---|
| Chart questions (1,322 fresh) | vote3: majority of plain, self-check and enlarged answers | 82.0% | 84.6% | +2.6 pts (+1.4 to +3.8) | exact McNemar p < 0.001 (49 fixed, 15 broken) |
| Page text (80 fresh pages) | layoutmask: blank tables, figures, equations, headers/footers before reading | word F1 0.814 | 0.881 | +0.067 (+0.034 to +0.101) | paired bootstrap |

## 1. Chart questions

- **Where the gain is:** human-written questions, which need arithmetic: 75.6% to 80.5%. Machine-generated questions barely move: 88.7% to 88.9%.
- **Cheaper option:** the self-check prompt alone scores 84.5% (+2.5, CI +0.9 to +4.1) with one call instead of three, about 1.8 s per question instead of about 5 s. The vote picked the self-check answer 94% of the time.
- **Recommendation:** use self-check alone in production; vote3 only where the extra 0.1 point is worth three times the compute.

## 2. Page text

- Precision rose from 0.787 to 0.931. Academic papers 0.729 to 0.843; books 0.745 to 0.844. Median time per page fell from 16.1 s to 12.3 s.
- **Costs:** recall fell from 0.894 to 0.848, and **number recall fell from 0.872 to 0.694**. Newspapers got worse (0.845 to 0.798). 3 pages lost more than 0.05 F1 (one lost 0.32); 27 gained more than 0.05.
- **Likely cause (untested):** the layout model's "abandon" class also covers footnotes, which the answer key keeps.
- **Recommendation:** do not adopt as is for documents where numbers matter. Next test: mask only tables, figures and equations, on fresh pages.

## What did not help

- **Read the chart's data table first, then answer:** +1.9 points on development data, interval crossing zero, about 15 s per question. Dropped.
- **Enlarging the image alone:** +1.5 points on fresh questions, smaller than self-check.
- **Tables:** not retested. Round 1 used every eligible OmniDocBench table; a new benchmark (PubTabNet validation) is needed first.

## How it was kept honest

- Round 1 used every ChartQA test question, so round 2 used the never-touched ChartQA validation split: 586 development and 1,322 confirmation questions, split by chart so no chart is in both. 80 pages appear in no earlier case.
- The plan and decision rules were written down (PLAN.md) and the case set frozen and fingerprinted (frozen_case_manifest_v2.json, sha256 0615583a6cfe...a729) before any run.
- Variants were chosen on development data only (selection.json). Exactly two confirmatory tests, Holm-corrected.
- Temperature, output schema, scorers and thresholds unchanged from round 1. One page hit the 6,000-token output limit under both settings and counts as zero in both.

## Files

- `vision_eval.py`: variants vote3, readfirst, layoutmask; commands build-v2 and vote; `--workers`; Holm families for round 2.
- `regions.py`: `yolo_all()` returns every layout box with its class.
- This folder: PLAN.md (pre-registration), run_round2.py (exact run order and selection rule), selection.json, frozen_case_manifest_v2.json, summary and comparison JSONs.

## For the Codex handoff

Round 2 is outside the frozen vision-v1 contract. To replicate it on the laptop, the contract needs an addendum freezing the round-2 variants (self-check and layoutmask) and the v2 manifest; until then, export and merge exclude round-2 rows unless `--round2` is passed.
