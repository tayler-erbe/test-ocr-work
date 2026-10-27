# Round 3: laptop tasks (Codex)

Read `docs/round3/PLAN.md` first. Everything here runs on the 12 GB laptop with Ollama; nothing needs the desktop. Report back on this branch (`round3-2026-10-26`) with aggregate files only: no model responses, no crops, no private documents.

## 0. Deliverables the desktop is waiting on (do these first)

1. **The frozen 60-document legal pack.** Copy the directory that `tools/freeze_nemotron_confirmation.py` produced (`requests.json`, `references.DO_NOT_SEND_TO_MODEL.json`, `RECEIPT.json`) to `benchmarks/harness/handoff/legal-confirmation-60/` and commit it. Its receipt hash must equal `pack_receipt_sha256` in `results/legal/nemotron-confirmation-plan-2026-10-26.json`. It is public CUAD and ContractNLI text, like the 24-case pack already in the repo.
2. **Full spans for the 24 cases.** From the lab database, export `{case_id: spans}` for the 24 cases in `handoff/legal-comparison-24/references.DO_NOT_SEND_TO_MODEL.json` (the `spans` column of `document_spans` for each case's `doc_id`, exactly as `tools/nemotron_reassessment.py` reads it) to `benchmarks/harness/handoff/legal-comparison-24/full_spans.json`. The desktop database holds no documents, so the `full_document` arm cannot run there without this file.
3. **Laptop capability note.** Add `docs/round3/LAPTOP.md` stating: Ollama version; whether WSL2 with a CUDA-capable Python and vLLM exists on the laptop (yes/no, versions); free disk; and `nvidia-smi` memory. Nothing else.

## 1. Legal track on the laptop: Qwen3 14B (L-L1)

```
ollama pull qwen3:14b
set OLLAMA_MODEL=qwen3:14b
python -X utf8 benchmarks/harness/tools/local_legal_reassessment.py --out results/legal/round3/qwen3-14b-arms --full-spans benchmarks/harness/handoff/legal-comparison-24/full_spans.json --run
python -X utf8 benchmarks/harness/tools/local_legal_reassessment.py --confirm --pack benchmarks/harness/handoff/legal-confirmation-60 --out results/legal/round3/qwen3-14b-confirm --run
```

Commit `PLAN.json` and `summary.json` from each output directory. Do not commit `events.LOCAL_ONLY.jsonl`. One model on the GPU; check `ollama ps` shows 100% GPU before counting a run. If `qwen3:14b` does not sit fully on the GPU with a 32k context, stop and say so rather than letting layers spill to the CPU.

## 2. Tables held out, laptop 8B (V-L2)

```
python -X utf8 benchmarks/harness/vision_eval.py --root <lab root> run --model ollama:qwen3-vl:8b-instruct --task table_confirm --cases confirm
python -X utf8 benchmarks/harness/vision_eval.py --root <lab root> run --model ollama:qwen3-vl:8b-instruct --task table_confirm --cases confirm --variant expert
```

Then export with `--side laptop` as before and commit the export. The conformance check must still print CONFORMANT.

## 3. Numeric recall on the crops (V-L1)

Write `benchmarks/harness/tools/numeric_misses.py`: for every stored `ocr_crop` row (laptop 8B and 7B, plus the desktop export), list per case the numeric tokens in the gold that the prediction lacks, using `vision_eval.numbers` and `vision_eval.norm` unchanged. Output an aggregate table only: miss count by case id and by model, and whether the missed set is identical across models. No crop images, no predicted text in the committed output. Propose, in `docs/round3/NUMERIC.md`, a `numeric` variant (a second pass that re-reads only the numbers) as a new protocol version; do not run it until the proposal is on the branch.

## 4. Masking v2 (V-L3)

Add variant `layoutmask2` to a NEW runner (copy of the `layoutmask` branch of `run_case` into `benchmarks/harness/tools/layoutmask2.py`, importing everything else from `vision_eval`), masking only `table`, `figure` and `isolate_formula` labels (no `abandon`). Run it on 8B and 7B for `page_text` (40 dev) first. Primary metric is numeric recall; word F1 is secondary. Only if numeric recall holds on the 40 dev pages, run `page_text_confirm2` (80). Commit the aggregate JSON.

## 5. Only if WSL2 with CUDA exists on the laptop (P-L1)

Serve `PaddlePaddle/PaddleOCR-VL-1.6` with vLLM on 127.0.0.1:8001 (see `serve_ocr_vllm.sh` in the Skyrule bakeoff folder for the flags used on the desktop) and run:

```
python -X utf8 benchmarks/harness/parser_eval.py --root <lab root> run --backend paddleocrvl --task page_text --task page_text_confirm2 --task table --task table_confirm
python -X utf8 benchmarks/harness/parser_eval.py --root <lab root> report --out results/vision/round3/parsers-laptop.json
```
