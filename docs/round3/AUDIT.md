# Evaluation audit (26 October 2026): what a senior reviewer could still pull apart

Two independent reviews of the protocol as it stands after the round-3 parsers: one by the orchestrating assistant, one by a second model given the same written description and asked to find holes. Items both raised are marked (both). Ranked by how much each undermines a "this model is best" claim. "Day" means closable with under a day of single-GPU work.

## Claims the evidence supports today

Among the candidates tested, on public benchmarks, under the stated resource envelopes: which model and method to try first for each task, with intervals for the vision-model comparisons and the round-2 confirmation. Nothing more.

## Gaps

| # | Gap | Who raised it | Day? | What closes it |
|---|---|---|---|---|
| 1 | No target-domain documents. Public pages and charts cannot establish correctness on proposals, contracts and reports, and the parser publishers optimise toward OmniDocBench, which is also our development data. | both | no | A labelled, document-disjoint acceptance set from representative packets (already listed as next step 04). Until then every winner is "among tested, on public data". |
| 2 | Parsers were tested in their weakest documented mode: Parse single pass, PaddleOCR-VL without its layout-plus-element pipeline, olmOCR without its toolkit. The ordering says which bare recogniser is best, not which supported stack. | both | partly | Run each official pipeline end to end on the same frozen pages, beside the bare arm, with all steps and time charged. Parse multipass and PaddleOCR's pipeline are a day; olmOCR's toolkit needs its own environment. |
| 3 | Resource envelope is a confound. Vision models shared 1,600 to 1,800 px and up to 6,000 output tokens; parsers used 1,288 to 2,048 px and 8,192 to 8,744 tokens. Truncation failures depend on the budget, and failures score zero. | both | yes | A budget-sensitivity arm: the 32B vision model at the parsers' budget on the 80 pages, and the parsers at 6,000, so the truncation share is attributable. |
| 4 | Round-3 comparisons have no intervals and no pre-registered hypothesis; candidate selection after seeing results risks the winner's curse. 0.818 vs 0.821 TEDS is not "equivalent" merely by being close. | both | yes | Paired, document-clustered bootstrap for every parser-versus-best-vision comparison on identical cases; a stated equivalence margin; label round 3 exploratory and confirm any winner on a fresh set. |
| 5 | The legal cross-model comparison is incomplete. Only the hosted Nemotron and gpt-oss get the 60-document contrast; the local Qwen models have the quoting baseline on 24 exposed cases only. No "best legal model" follows. | both | no (4 to 6 h) | Qwen3 32B on the 60-document contrast with evidence by ID and matched retrieval, or state plainly that the legal track ranks configurations of two models, not the field. |
| 6 | Numeric correctness is a bag-of-tokens recall. It credits a right number in the wrong cell and ignores invented numbers, signs, units and scale; even so nothing reaches 99%. | second review | no | A field-bound numeric metric with false positives, and an explicit outcome "no candidate qualifies for unattended extraction". |
| 7 | Flattened tables and the page-text mapping erase what the workload needs: span relationships, header-to-value binding, and the very table, figure and formula content removed from page scoring. | second review | partly | Score structure-preserving TEDS beside the flat one (the parsers already emit spans); add a tables-in-context metric on whole pages. |
| 8 | The 99% bar has no acceptance rule. Numbers within a table or document are correlated, so the effective sample is far smaller than the token count. | second review | no | A document-clustered one-sided lower bound above 99% as the acceptance test, with the sample sized for it. |
| 9 | Deployment hardware was not the selection environment for the parsers or the 32B models. | both | yes | A laptop feasibility sweep for every recommended configuration: peak VRAM, CPU offload, failures, end-to-end latency. The laptop has no WSL, so the parsers need a Windows path or stay desktop-only, which must be stated. |
| 10 | Legal reasoning effects rest on single stochastic passes (sampling arms at temperature 1) and an eight-arm search on 24 exposed cases; gpt-oss low versus high is a different estimand from Nemotron off versus on. | both | yes | Repeat the sampling arms across seeds; keep each model's reasoning contrast as its own estimand; never pool them. |
| 11 | Two of thirteen same-weight cross-machine comparisons did not reproduce and the cause is unexplained; an unexplained discrepancy of that size could flip a few-point gain. | second review | yes | Replay the two discrepant groups on both machines with matched runtime and decoding, or report them as machine-specific. |
| 12 | Vote3's diversity source is unstated at temperature 0 (its members are baseline, self-check and upscale, so diversity comes from the method, not sampling) and its three-call cost is not charged beside single-pass methods in the tables. | second review | yes | State the member provenance and disagreement rate; report cost per case beside the gain. |
| 13 | Latency figures do not describe the operating regime: four concurrent parser requests on a 32 GB card, unknown concurrency for the vision rows, no packet-level p95, no laptop numbers. | both | yes | One representative packet queue at concurrency one and at the intended concurrency, p50 and p95, memory, total work including voting and preprocessing. |
| 14 | Fail-zero conflates quality with recoverable serving faults; PaddleOCR's page truncations may be a budget defect, and a real service would retry. | second review | yes | Keep the strict scores; add a pre-declared bounded recovery arm (one retry at a larger budget) reported separately with its cost. |
| 15 | Candidate coverage is incomplete against the current OmniDocBench leaders (TeleOCR, OvisOCR2, MinerU2.5, GLM-OCR) and against a hosted frontier model as a ceiling reference; the 32B vision model ran as a 4-bit AWQ build. | first review | yes per model | One run each through the existing parser adapter; the AWQ confound stays a stated limitation unless a BF16 run fits elsewhere. |
| 16 | No failure taxonomy or scorer audit on a human-checked sample; the numeric-miss analysis is deferred. | first review | yes | The planned numeric-miss table, plus a small human audit of scorer decisions on public cases. |

## Verdict

The vision-model comparison is defensible as a controlled, pre-registered, reproducible study on public data. The round-3 parser result is a strong lead, not a verdict: items 2, 3 and 4 have to be closed before "PaddleOCR-VL-1.6 is the best table reader" can stand up to review, and item 1 bounds every claim to public data. The legal track ranks configurations, not models, until item 5 is closed. A reviewer who says "they picked a winner without domain data, without intervals on the new rows, without running the vendors' own pipelines, and on unequal budgets" would be right today.

## Proposed round 3b (closable in about one GPU day)

1. Intervals and equivalence margins for every round-3 comparison (code only).
2. Budget-sensitivity arm (item 3), about 1 hour.
3. Parse multipass and PaddleOCR official pipeline on the same pages (item 2), about half a day.
4. Laptop feasibility sweep for the recommended configurations (item 9), on the laptop.
5. Replay of the two unreproduced groups (item 11), about 1 hour.
6. Seeds for the sampling arms and a packet-level latency run (items 10, 13), about 2 hours.
Items 1, 5, 6, 7 and 8 are larger and are the honest boundary of what this evaluation can claim.
