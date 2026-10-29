# Website data audit

This first pass corrects legal interpretation and restores missing round-2 page metrics. No inference, new scoring rules or private data were used.

## Legal interpretation

No final CUAD configuration exceeds the always-absent baseline of 15/30. The highest observed ContractNLI count is 18/30 for Qwen3 32B with thinking off. Cross-model statistical superiority is not established. Local external article drafts were not edited in this repository.

## Restored round-2 page values

Calculated by the existing frozen aggregate function. All 80 attempts remain in each quality denominator; failed attempts score zero. Median latency uses completed attempts with metrics, matching the original aggregator. Means must not be relabelled as medians.

| Hardware | Model | Method | Attempts | Failed | Median seconds | Numeric recall |
|---|---|---|---:|---:|---:|---:|
| laptop | Qwen2.5-VL 7B | baseline | 80 | 4 | 13.44 | 74.4% |
| laptop | Qwen2.5-VL 7B | layoutmask | 80 | 0 | 17.31 | 65.5% |
| laptop | Qwen3-VL 8B Instruct | baseline | 80 | 1 | 15.45 | 82.5% |
| laptop | Qwen3-VL 8B Instruct | layoutmask | 80 | 3 | 17.92 | 66.3% |
| desktop | Qwen3-VL 32B AWQ | baseline | 80 | 1 | 15.85 | 87.2% |
| desktop | Qwen3-VL 32B AWQ | layoutmask | 80 | 1 | 12.16 | 69.4% |

Source hashes and run IDs: [audit JSON](../site/data/round2-audit.json). Reproduce with `python -X utf8 tools/audit_website_data.py`; use `--write` to rebuild. The importer refuses missing groups, duplicate cases or a material discrepancy with the published word scores.

## Dashboard coverage

Counts below are configuration summaries, not independent documents or distinct models. They establish dashboard source coverage; they do not mean every possible experiment was run.

| Hardware | Task | Evaluation set | Configurations |
|---|---|---|---:|
| desktop | chart_qa | confirmation v1 | 3 |
| desktop | chart_qa | development | 23 |
| desktop | chart_table | development | 22 |
| desktop | ocr_crop | development | 5 |
| desktop | page_text | confirmation v2 | 2 |
| desktop | page_text | confirmation v3 | 5 |
| desktop | page_text | development | 2 |
| desktop | table | confirmation v1 | 3 |
| desktop | table | confirmation v3 | 5 |
| desktop | table | development | 22 |
| laptop | chart_qa | development | 8 |
| laptop | chart_table | development | 8 |
| laptop | ocr_crop | development | 2 |
| laptop | page_text | confirmation v2 | 4 |
| laptop | table | development | 8 |

## Remaining presentation work

The review notes remain the specification for the larger redesign: populated named comparisons, plain-language task explanations, hardware guidance, legal visuals, HTML reports and matching PDFs. This audit does not claim that redesign is complete. Historical report files remain unchanged; restored dashboard values have a separate provenance record.
