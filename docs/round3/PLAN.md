# Round 3 plan: more candidates, same contract (26 October 2026)

**Scope, fixed 26 October evening: candidates that have not been run yet, nothing else.** Round 3 asks one question: is there a model not yet tested that fits this use case? It runs gpt-oss-20b on the legal track and Nemotron 3.5 Parse, olmOCR-2 and PaddleOCR-VL-1.6 on the page tasks. Every other item below (Qwen3 32B and local Nemotron legal arms, Qwen3 14B, the 8B numeric and masking work) is deferred and not scheduled; it stays in this file only so the ids keep meaning.

Read [laptop readiness and methodological gates](LAPTOP.md) before execution. The gates qualify this proposed schedule; they are not completed inference results.

Round 3 adds new models to the existing public-benchmark evaluation without changing anything that produced the earlier rows. Frozen case manifests, the frozen scorers and the conformance checks stay as they are. Every new model, method or transport gets its own protocol label and its own run ids, so old and new rows never mix.

Two machines share the work. Each item below says which machine runs it and what it needs first.

| Machine | GPU | Runtime | Who drives it |
|---|---|---|---|
| Desktop | RTX 5090, 32 GB | Ollama on Windows; vLLM 0.30 under WSL2 | Claude |
| Laptop | RTX 4000 Ada Laptop, 12 GB, 64 GB RAM | Ollama on Windows (WSL2 status unknown: report it) | Codex |

Rules that carry over unchanged: one model resident on the GPU at a time, served on 127.0.0.1; temperature 0 except where an arm explicitly sets sampling; failed and truncated answers score zero and stay in the denominator; no model grades another; nothing is re-run to rescue a result; public data only; aggregate tables only leave the machine.

## 1. Legal track: the same campaign every text model gets

The hosted Nemotron 3 Nano 30B endpoint received an eight-configuration campaign on the 24-case public pack and a reasoning on/off contrast on 60 public documents unused in locally recorded earlier runs. No other model has had that. Round 3 gives the identical campaign to every text model, local ones included, through `benchmarks/harness/tools/local_legal_reassessment.py`. It imports the arms, the request builder and the frozen scorer from the Nemotron tools; only the transport changes (Ollama's native chat endpoint, which is the only way to set thinking on a local model).

Context fit is measured per request with the model's own tokenizer (a one-token prefill) against the context recorded in the plan (gpt-oss and Nemotron 65,536; Qwen3 32B 40,960, its published window); a request that cannot fit is recorded as `context_exceeded`, never truncated. The byte guard that rejected token-feasible requests is gone. The run also records whether the weights sit fully on the GPU and stops if they do not.

Thinking control per family is recorded in every row: Qwen3 and Nemotron use think on/off; gpt-oss cannot switch reasoning off, so its "off" arms run reasoning level low and its "on" arms level high.

| Id | Model | Machine | Fits | Why |
|---|---|---|---|---|
| L-D1 | gpt-oss-20b (Ollama `gpt-oss:20b`, MXFP4, about 13 GB) | Desktop | 32 GB yes; 12 GB no (would spill to CPU) | The open-weight GPT candidate for reasoning over extracted text |
| L-D2 | Qwen3 32B (Ollama `qwen3:32b`) | Desktop | 32 GB only | The local reference that scored 5/12 and 9/12 with the quoting design; it never had the arms |
| L-D3 | Nemotron 3 Nano 30B, local (Ollama `nemotron-3-nano`) | Desktop | 32 GB only | Deployment challenger; checkpoint, quantization, template and runtime must match before attributing differences to serving |
| L-L1 | Qwen3 14B (Ollama `qwen3:14b`, about 9 GB) | Laptop | Fit gate pending at actual 32k context | What a 12 GB workstation can do on the legal track |

Each model runs 8 arms x 24 cases (192 requests), then the fixed reasoning on/off contrast on the 60-document pack (120 requests). Pre-registered primary contrast: strict correctness, reasoning on versus off at a 16k budget, per model, on the 60 documents. Pre-registered cross-model comparison: strict correctness on the 60 documents, every model on the identical cases, document-level paired bootstrap. Nothing is selected on the 60 documents.

Needed first, from the laptop (public data, commit to the round-3 branch):
1. The frozen 60-document pack (`requests.json`, `references.DO_NOT_SEND_TO_MODEL.json`, `RECEIPT.json`) under `benchmarks/harness/handoff/legal-confirmation-60/`.
2. `benchmarks/harness/handoff/legal-comparison-24/full_spans.json`: `{case_id: spans}` for the 24 cases, exported from the lab database's `document_spans` table (the `full_document` arm needs it; the desktop database holds no documents).

## 2. Page tasks: dedicated parsers against the 8B route

New protocol `vision-v3-parsers`, runner `benchmarks/harness/parser_eval.py`. Same frozen cases, same scorers (word F1 and numeric recall on pages, TEDS and numeric recall on tables, precision/recall at IoU 0.5 on layout). The parsers are not chat models, so each gets its own published prompt or control tokens and an adapter that converts its native output into the shapes the scorers already take. Nothing in `vision_eval.py` changes.

| Id | Model | Size | Machine | Tasks | Serving |
|---|---|---|---|---|---|
| P-D1 | Nemotron 3.5 Parse (NVIDIA, OpenMDW 1.1) | 0.63B | Desktop | page_text 40 + 80, table 60 + 159, layout 120 | vLLM plugin in its own environment under WSL2 |
| P-D2 | olmOCR-2 7B FP8 (Apache 2.0) | 7B | Desktop | page_text 40 + 80, table 60 + 159 | vLLM under WSL2 (already cached and served once for the book corpus) |
| P-D3 | PaddleOCR-VL-1.6 (Apache 2.0) | 0.9B | Desktop | page_text, table, layout | vLLM under WSL2 (the 1.5 build is cached and was served once) |
| P-L1 | PaddleOCR-VL-1.6 | 0.9B | Laptop, only if WSL2 with CUDA exists there | same | Cross-machine reproduction of P-D3 |

Reserves, not scheduled: DeepSeek-OCR-2 (3B), Nemotron OCR v2 (text lines with confidence; a candidate for an unread-page detector, not for accuracy).

Caveat written into the report: OmniDocBench is both our development data and the benchmark these publishers optimise toward. Page results are reported on the 80 held-out pages first, and the comparison is labelled exploratory until a page set outside OmniDocBench is frozen.

## 3. Pushing the small models further (laptop)

| Id | Work | Done when |
|---|---|---|
| V-L1 | Numeric recall on the 50 crops: list the missed numbers per case for 8B, 7B and the desktop 32B rows; establish whether the 3.5% miss is the same cases for every model, then a numbers-only second pass as variant `numeric` on 8B and 7B | A table of missed numbers by cause, and the `numeric` variant's recall with an interval on the dev crops; a fresh crop set is frozen before any claim |
| V-L2 | Tables, 159 held-out, on the laptop 8B, baseline and expert | Closes the gap that confirmation tables ran only on the desktop |
| V-L3 | Masking v2: blank tables, figures and display equations only, as variant `layoutmask2`, 8B and 7B, 40 dev then 80 held-out, numeric recall as the primary metric | Numeric recall holds while word F1 improves, or the variant is dropped |

## 4. Order and timing

Desktop: parsers first (small models, fast), then the legal campaign as soon as the two laptop deliverables land. The legal arms at a 16k budget with thinking on are the slow path: budget hours, not minutes, for Qwen3 32B.

Laptop: deliverables (section 1) first, then V-L2, V-L1, V-L3, then L-L1, then P-L1 if WSL2 is available.

## 5. Reporting

Results land under `results/legal/round3/` and `results/vision/round3/` as aggregate JSON and Markdown only. The merged routing report gets a round-3 addendum; public pages are updated only after the whole round is in.
