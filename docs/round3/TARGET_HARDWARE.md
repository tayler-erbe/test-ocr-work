# Target hardware: NVIDIA L4 and L40S (set by Tayler, 27 October 2026)

The deployment targets for this work are a single **NVIDIA L4 (24 GB)** or a single **NVIDIA L40S (48 GB)**. The desktop (RTX 5090, 32 GB) is only where the selection ran, and the work laptop is not a target. Audit item 9 ("deployment hardware was not the selection environment") is re-scoped to these two cards, and the laptop feasibility sweep in `CODEX_TASKS_3B.md` is withdrawn.

The work serves two purposes:

1. **Client solution at work:** a private document-intelligence service (research proposals, procurement documents, contracts and legal, reports) on open-weight models, on an L4 or L40S.
2. **Public guidance:** which open-weight model to use for which document job, on which GPU, with measured accuracy, speed and cost, for anyone hosting models on private data.

## What fits, from weight sizes (measured on disk; not yet run on either card)

| Job | Recommended model | Weights | L4 24 GB | L40S 48 GB |
|---|---|---|---|---|
| Tables | PaddleOCR-VL-1.6 (0.9B, BF16) | about 2 GB | fits easily | fits easily |
| Whole-page text | Nemotron 3.5 Parse (0.63B, BF16) | about 1.3 GB | fits easily | fits easily |
| Clean prose, archives | olmOCR-2 7B FP8 | about 9 GB | fits | fits |
| Charts, general vision | Qwen3-VL 8B FP8 | about 10 GB | fits | fits |
| Comparator, hard pages | Qwen3-VL 32B AWQ | about 20 GB | tight: little room for KV cache and images | fits |
| Clause extraction | Qwen3 32B 4-bit | about 20 GB | tight at 16k context | fits, with room for concurrency |
| Clause extraction, second opinion | gpt-oss-20b MXFP4 | about 13 GB | fits | fits |

Both cards are Ada generation with FP8 support. Two models can share one L40S (for example a parser plus a 32B model); on an L4 the parsers and one mid-size model share comfortably, a 32B model does not.

## What does not transfer from the desktop

Accuracy transfers (same weights, same decoding, temperature 0), subject to a reproduction check. Speed does not. Token generation is limited by memory bandwidth: the RTX 5090 has about 1.8 TB/s, the L40S about 0.86 TB/s and the L4 about 0.3 TB/s. Expect the L40S at roughly half the desktop's decode speed and the L4 at roughly a sixth, worst for the 32B models. Every throughput number in `RESULTS_3B.md` is desktop-only until measured on the target cards.

## Decision (Tayler, 27 October 2026): no target-hardware run

All models were measured on one machine, so the desktop numbers are valid relative comparisons, and that is the precision this work needs. Note for any reader: absolute speeds on an L4 or L40S will be lower, and not exactly proportional. The large models (32B) are limited by memory bandwidth and slow down more than the small parsers, so the parsers' speed advantage should hold or widen on the target cards. Report desktop speeds as relative, with the bandwidth ratios above as the guide; fit on each card follows from the weight sizes in the table.
