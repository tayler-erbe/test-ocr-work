# Laptop readiness and division of work

Verified 26 October 2026 on the work laptop:

- Dell Precision 7780; 64 GB installed RAM (reported physical bytes: 68,388,900,864).
- NVIDIA RTX 4000 Ada Laptop GPU; 12,282 MiB total VRAM; 0 MiB allocated at initial check.
- NVIDIA driver 580.92; driver reports CUDA compatibility 13.0. This does not establish a locally installed CUDA toolkit.
- Ollama 0.34.4.
- WSL is not installed. No WSL2 CUDA Python/vLLM environment exists to reproduce the desktop parser setup.
- About 733 GiB free on C: at the check.
- Installed vision artifacts: qwen3-vl:8b-instruct (70e58e37beb1, 6.2 GB), qwen2.5vl:7b (5ced39dfa4ba, 6.0 GB).
- Qwen3 14B and GPT-OSS 20B are not installed. A 14B 32k-context/16k-output campaign is not yet proven to fit fully on this GPU.

## Agreed allocation, pending actual execution

| Machine | Model/work | Gate |
|---|---|---|
| Desktop / the desktop operator | GPT-OSS 20B, Qwen3 32B, local Nemotron Nano legal comparisons | GPU availability; adapter fixes; full input packs now supplied |
| Desktop / the desktop operator | Nemotron 3.5 Parse, PaddleOCR-VL-1.6, olmOCR 2 | Working native parser pipelines, accurate adapters and pinned revisions |
| Laptop / Codex | Public pack verification and export | Complete; see PACK_VERIFICATION.json |
| Laptop / Codex | Qwen3-VL 8B held-out tables, numeric miss analysis, 7B/8B masking-v2 development | Frozen conformance gates; new variants in new runners; no frozen selection changes |
| Laptop / Codex | Qwen3 14B legal campaign | Conditional on measured full GPU fit at the actual context/output budget; not yet started |
| Laptop / Codex | PaddleOCR-VL cross-machine run | Deferred: no WSL environment; no system installation performed |

GPT-OSS 20B remains assigned to the desktop. CPU offload is possible in principle, but would answer a different performance question and must not be passed off as a fully GPU-resident laptop run.

## Required methodological corrections before campaigns

1. GPT-OSS low/high reasoning is not an on/off ablation. Record actual controls and use separate contrast labels and budgets. Do not call its low setting non-reasoning.
2. Local Nemotron versus the hosted endpoint does not isolate serving unless checkpoint revision, quantization, template, context and generation are matched. Otherwise label it a deployment comparison.
3. Preserve raw final answers and stop reasons locally even when parsing/validation fails. The adapter now retains these before scoring. Reasoning text remains excluded.
4. The adapter's byte-based context guard can reject token-feasible inputs. Quantify these rejections before inference; do not rank a model on a large set of requests it never received. A tokenizer-based preflight is needed for a supported exact build; changing context requires a newly labelled configuration and measured memory fit.
5. Frozen contracts currently pass for the original pipelines; this does not validate the new adapters. Test mapping of native outputs, errors, truncations and evidence offsets before scoring.
6. Full parser pipelines include rendering/layout/retries; record those steps and GPU/CPU time. Do not describe bare recognition output as a complete parser.
7. The existing 60 cases have been exposed to the earlier Nemotron comparison. Reuse is valid for a fixed matched comparison, not a new untouched final holdout after tuning on them.
8. Masking-v2 needs a numerical non-inferiority tolerance fixed before checking results. A vague requirement that recall "holds" permits post-hoc decisions. Its confirmation pages have prior experiment exposure.

The original round-3 branch predates the latest completed Nemotron documentation. This readiness branch is based on current main and imports only round-3 code/plans, avoiding restoration of stale reports. Neither an inference campaign nor a desktop GPU release is claimed here.

## Preflight result

The current conservative context guard rejects 32/60 requests in each confirmation arm before inference, and 13/24 in most 16k exploratory arms (14/24 for definitions). See LOCAL_CONTEXT_PREFLIGHT.json. This blocks valid local model-quality comparisons until the guard/context fit is resolved. No failed-request campaign was launched.
