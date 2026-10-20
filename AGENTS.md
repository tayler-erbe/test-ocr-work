# Instructions for coding agents (Codex and others)

This repository holds the Evidence Desk document-intelligence prototype and the **vision-v1** OCR/vision evaluation. The evaluation runs on two machines (the desktop and the work laptop), and both must produce results that merge into one report. **Read `docs/handoff/CODEX_HANDOFF.md` before running or changing anything in the evaluation.**

## Before any evaluation run, and before any merge
```
python -X utf8 tools/check_conformance.py --root <lab folder> --data
```
It must print `CONFORMANT`. If it doesn't, stop and fix the cause; never edit `tools/contract.json` or `tools/golden_scores.json` to make it pass.

## Method rules (vision-v1)
- Run the repository's code (`vision_eval.py`, `vlm_client.py`, `regions.py`); do not reimplement prompts, scorers or statistics.
- The frozen case manifests (`evaluation/vision_cases_v1.json`, `vision_confirm_v1.json`, `vision_cases_v2.json`) are never edited or rebuilt. Copy them in the case pack and verify them by `cases_sha256`.
- Never lower a threshold, drop a case, raise a token budget, or re-run a failed case to replace it. Failed and truncated answers count as zero.
- Temperature 0. One run per model × variant. Uncertainty comes from the paired bootstrap over cases (`vision_eval.py compare`).
- Do not use thinking/reasoning model builds; use `-instruct` builds (budgets are fixed and a thinking model truncates).
- No model grades another model; every score comes from published answer keys and code.
- Local models only, served on 127.0.0.1. One model on the GPU at a time.
- A new prompt, variant, task or scorer is a new protocol version with its own frozen cases and a new contract. It never changes v1.
- Export rows with `tools/export_results.py` and merge with `tools/merge_results.py`; the final report is the generated `MERGED_REPORT.md` plus written conclusions.

## Data and git
- Only aggregates go to GitHub. Never commit datasets, crops, `*.sqlite3`, `exports/`, `merged/`, model outputs, private PDFs or credentials.
- Use `python -X utf8` on Windows.

## Case pack location (added 20 Oct 2026)
The frozen case pack is in this repo at `case_pack/` (datasets stored with Git LFS). After cloning or checking out
`handoff-codex`, run `git lfs install` and `git lfs pull`, then copy `case_pack\` to `C:\dev\ocr-lab` and use that as `--root`
(results databases are written under `--root`, so keep them out of the repo). Verify with:
`python -X utf8 tools\check_conformance.py --root C:\dev\ocr-lab --data` -> must print CONFORMANT.
The desktop ran this exact check against `case_pack/` itself before pushing: CONFORMANT.

## Round 2 addendum (added 20 Oct 2026)
Round 2 (vote3 confirmed, selfcheck supporting, layoutmask experimental) has its own contract: `tools/contract_r2.json`,
`tools/golden_r2.json`, `tools/eval_contract_r2.py`. Read `docs/handoff/CODEX_HANDOFF_ADDENDUM_R2.md` before any round-2 run.
Run `python -X utf8 tools\check_conformance.py --root C:\dev\ocr-lab --data --round2` first; it must print CONFORMANT.
Never run `docs/research/vision-eval/improvements/run_round2.py` on the laptop (it rewrites selection.json and breaks the contract).
Export round-2 rows with `--round2`; merge with `--round2`.
