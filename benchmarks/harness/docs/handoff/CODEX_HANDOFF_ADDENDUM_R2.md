# Codex handoff, addendum: round 2 (20 Oct 2026)

This addendum extends [CODEX_HANDOFF.md](CODEX_HANDOFF.md). Everything there still applies. The vision-v1 contract
(`tools/contract.json`, `tools/golden_scores.json`, `tools/eval_contract.py`) is unchanged byte for byte; round 2 has its own
contract in `tools/contract_r2.json`, `tools/golden_r2.json` and `tools/eval_contract_r2.py`.

## 1. What round 2 is

The desktop's attempt to improve chart questions and page text, tested on cases unused in any earlier evaluation run
(not proven absent from model training). Full results: `docs/research/vision-eval/improvements/REPORT.md`; adoption
decisions: `docs/research/ocr-round2-adoption-review.md` on `main`.

| Variant | Task | Status (from the adoption review) |
|---|---|---|
| `vote3` | chart_qa | **Confirmed.** The pre-selected confirmatory test on `chart_qa_confirm2`, significant after Holm. Higher-cost option (three answers per question). |
| `selfcheck` | chart_qa | **Supporting comparison**, not confirmatory. The cheaper chart candidate (one call). |
| `upscale` | chart_qa | vote3 member; supporting comparison only. |
| `layoutmask` | page_text | **Experimental.** Word F1 rose (0.814 to 0.881), but numeric recall fell from 87.2% to 69.4%. Not for budgets, contracts or other number-critical text. |
| `readfirst` | chart_qa | Dropped on development data. Kept only so the code path is reproducible. |

The page-text metric is **word F1**, not general accuracy. `check_conformance.py --round2` prints these labels; they label
results and change nothing in the scoring.

## 2. What the round-2 contract fixes

`tools/eval_contract_r2.py` fingerprints only what round 2 added, the same behavioural way as v1:

- **Requests:** `run_case()` with a recording stand-in model for chart_qa x baseline/selfcheck/upscale/readfirst and
  page_text x baseline/layoutmask, at a small and a large probe size. Prompts, schemas, token budgets, image sizes and the
  decoded pixels sent to the model are recorded. For layoutmask, a fixed fabricated set of layout boxes (one per
  DocLayout-YOLO class) is used, so *which classes get painted white* (figure, table, isolate_formula, abandon) is part of
  the contract.
- **Layout code:** a formatting-free hash of `regions.yolo_all()` and `MASK_LABELS`.
- **vote3 majority rule:** `vision_eval.vote()` on a temporary database of fabricated member answers: answers equal under
  the 5% relaxed-match rule count as agreeing; the most-supported answer wins; ties go to selfcheck; a case where no member
  answered is failed.
- **Statistics:** `compare()` on a fabricated round-2 table: families `exploratory_v2`, `confirmatory_v2` and
  `supporting_v2`, using the pre-registered pick in `docs/research/vision-eval/improvements/selection.json`.
- **Cases:** the frozen v2 manifest, `cases_sha256 0615583a6cfe12856ad6aa8cc1f5125b7306a53a4156ce2f439392a1de41a729`
  (586 `chart_qa_dev2`, 1,322 `chart_qa_confirm2`, 80 `page_text_confirm2`).

`method_sha256` of the round-2 contract: `2a64100df0d83a02bccca676e56601e626001b27dabd26b1c11a46b48a3a3a97`. It includes the
v1 method hash, so a v1 change also breaks round 2.

## 3. Data

Nothing new to copy. `case_pack/` already holds the v2 manifest, the 80 OmniDocBench pages and the ChartQA zip (whose
validation split holds all 1,056 round-2 chart images), all listed in `RECEIPT.json`. If you copied `case_pack\` to
`C:\dev\ocr-lab` before, you already have it; `git lfs pull` and copy again only if the receipt check fails.

## 4. Exact commands, in order (PowerShell, laptop)

```powershell
git fetch origin; git checkout handoff-codex; git lfs pull
$R = "C:\dev\ocr-lab"

# 0. conformance: v1 and round 2 must both pass
python -X utf8 tools\check_conformance.py --root $R --data --round2     # must print CONFORMANT

# 1. the pre-registered round-2 protocol, per laptop model (instruct builds only)
foreach ($M in "qwen3-vl:8b-instruct", "qwen2.5vl:7b") {
  # development (exploratory family)
  foreach ($V in "baseline", "selfcheck", "upscale") {
    python -X utf8 vision_eval.py --root $R run --model "ollama:$M" --task chart_qa_dev2 --cases v2 --variant $V
  }
  python -X utf8 vision_eval.py --root $R vote --model "ollama:$M" --task chart_qa_dev2 --cases v2
  # confirmation: the desktop's pre-registered pick is vote3, so run its three members, then vote
  foreach ($V in "baseline", "selfcheck", "upscale") {
    python -X utf8 vision_eval.py --root $R run --model "ollama:$M" --task chart_qa_confirm2 --cases v2 --variant $V
  }
  python -X utf8 vision_eval.py --root $R vote --model "ollama:$M" --task chart_qa_confirm2 --cases v2
  # page text (experimental variant)
  foreach ($V in "baseline", "layoutmask") {
    python -X utf8 vision_eval.py --root $R run --model "ollama:$M" --task page_text_confirm2 --cases v2 --variant $V
  }
}
# optional: readfirst on chart_qa_dev2 (dropped variant; only to reproduce the desktop's development table)

# 2. report, compare, export with round 2, validate
python -X utf8 vision_eval.py --root $R report
python -X utf8 vision_eval.py --root $R compare
python -X utf8 tools\export_results.py --root $R --side laptop --out exports\laptop.jsonl --round2
python -X utf8 tools\check_conformance.py --root $R --results exports\laptop.jsonl --round2
```

**Do not run `docs/research/vision-eval/improvements/run_round2.py` on the laptop.** It re-runs the selection step and
rewrites `selection.json`, which changes the round-2 contract; export would then refuse. The laptop replicates the desktop's
fixed, pre-registered protocol with its own models; it does not re-select variants.

Rough laptop time at one request at a time: about 4,000 chart calls and 160 page calls per model on the confirmation set,
plus about 1,800 on development. Plan on several hours per model. Runs are resumable (finished cases are skipped).

## 5. Merging

```powershell
python -X utf8 tools\merge_results.py --root C:\dev\ocr-lab --out merged\final --round2 exports\desktop.jsonl exports\laptop.jsonl
```

- Round-2 rows carry an extra field, `r2_method_sha256`, stamped by `export_results.py --round2` after checking the
  checkout against `tools/contract_r2.json`. The merge refuses any round-2 row without the matching value, and refuses
  round-2 rows entirely without `--round2`. v1 rows are unchanged.
- The desktop tested this on its own 22,731 exported rows (8,418 of them round 2) merged with a relabelled copy: the merged
  comparison reproduced the desktop's numbers (vote3 +0.0257, CI +0.0136 to +0.0371; layoutmask word F1 +0.0668), and a
  copy with a tampered round-2 hash was refused.

## 6. Caveats: what can still make the two sides disagree

1. **The pick is the desktop's.** vote3 was selected on Qwen3-VL-32B's development scores. On the laptop's 8B and 7B models,
   the confirmation rows test the same pre-registered variant with a different model. They are a replication of the protocol,
   not a new selection, and the confirmatory label in the merged report still refers to the desktop's pre-registration.
2. **Different models.** The laptop runs 7B and 8B models; the desktop ran 32B. Cross-machine reproducibility applies only to
   a model run on both machines; otherwise the merge shows "different weights: not a reproduction test".
3. **GPU and server differences** (RTX 5090 with vLLM against RTX 4000 Ada with Ollama) can flip a few answers even at
   temperature 0. vote3 is built from stored answers, so one flipped member answer can change a vote.
4. **layoutmask depends on DocLayout-YOLO on CPU.** The weights and `doclayout_yolo==0.0.4` are pinned in the v1 handoff.
   Different torch builds can move box edges slightly, which changes what is painted white. The contract fixes the masking
   rule, not the detector's boxes on real pages.
5. **Fresh means unused in earlier runs**, not absent from model training data.
6. **Tables were not retested** in round 2 (no unused eligible tables were left); there is no round-2 table result to replicate.
7. **Holm families:** the merge runs one `compare()` over both machines, so each family's correction covers every test from
   both sides; the desktop-only report's p-values will differ slightly from the merged report's.
