# Round 3b: laptop tasks (Codex)

Read `docs/round3/AUDIT.md` and `docs/round3/PREREG_3B.md` first. Everything here runs on the 12 GB laptop with Ollama. Aggregates only come back on branch `round3-desktop-2026-10-26`.

## 1. Feasibility sweep for the recommended configurations (audit item 9)

For each of: Qwen3-VL 8B Instruct baseline, Qwen3-VL 8B self-check (chart_table prompt), Qwen2.5-VL 7B self-check (chart_qa prompt), record on the laptop: peak VRAM from `nvidia-smi` sampled every second during 20 representative requests (10 pages at 1,800 px with a 6,000-token budget, 10 tables at 1,600 px), whether Ollama reports 100% GPU (`/api/ps` size equals size_vram), any CPU offload, failures, and p50/p95 request latency at concurrency 1. Write `docs/round3/LAPTOP_FEASIBILITY.md` with one table. No new scoring.

## 2. Replay of the two unreproduced 7B groups, laptop side (audit item 11)

Run `benchmarks/harness/tools/replay_7b.py --root <lab root> --control-dir <a local control dir>` on the laptop. It reruns `chart_qa` expert and `chart_table` upscale for `ollama:qwen2.5vl:7b` under protocol `vision-v1-replay` and prints, per group, how many cases scored identically to the stored laptop rows. Export the two replay runs with the usual `--side laptop` export and commit the export plus the printed agreement lines in `docs/round3/REPLAY_LAPTOP.md`. The desktop runs the same script; the two agreement rates together say whether the discrepancy is machine-specific or run-to-run noise.

## 3. Nothing else

No parser runs (no WSL on the laptop), no legal runs, no changes to `parser_eval.py`, `local_legal_reassessment.py`, `campaign_control.py`, `vlm_v3.py`, `replay_7b.py` or the drivers while the desktop campaign runs.
