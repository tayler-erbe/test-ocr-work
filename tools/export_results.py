"""Export vision-v1 results from a lab's library.sqlite3 to one portable JSONL file (one row per case per run).

Both machines export the same way; tools/merge_results.py only accepts these files. Every row carries the
frozen case-set hash, the code fingerprints (prompts, scorers) and the exact model weights, so a merge can
refuse anything that was not run under the same contract.

  python tools/export_results.py --root C:/dev/ocr-lab --side desktop --out exports/desktop.jsonl
  python tools/export_results.py --root LAB --side laptop --out exports/laptop.jsonl [--run 2]

--run labels a repeat of the same configuration (default 1). The protocol itself is one deterministic run per
model x variant at temperature 0; a repeat is only a determinism check and must be exported separately
(from a copy of the database) with --run 2.
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import eval_contract  # noqa: E402

SCHEMA_VERSION = "vision-v1-row-1"


def label_parts(label: str):
    """'ollama:qwen2.5vl:7b [table only] [expert]' -> ('ollama:qwen2.5vl:7b', 'expert', 'table_only')."""
    base, mode, variant = label, "image", "baseline"
    if " [table only]" in base:
        base, mode = base.replace(" [table only]", ""), "table_only"
    if base.endswith("]") and " [" in base:
        base, _, v = base.rpartition(" [")
        variant = v.rstrip("]")
    return base, variant, mode


def export(root: Path, side: str, out: Path, run: int = 1, round2: bool = False) -> int:
    db = sqlite3.connect(root / "library.sqlite3")
    configs = {rid: json.loads(cfg) for rid, cfg in db.execute("SELECT id, config FROM runs")}
    fp = eval_contract.fingerprints()
    contract = json.loads((REPO / "tools" / "contract.json").read_text(encoding="utf-8"))
    if fp["method_sha256"] != contract["method_sha256"]:
        raise SystemExit("REFUSED: this checkout's prompts or scorers differ from tools/contract.json; "
                         "run tools/check_conformance.py and fix that first")
    r2_hash = None
    if round2:
        import eval_contract_r2
        r2_hash = eval_contract_r2.fingerprints()["method_sha256"]
        if r2_hash != json.loads((REPO / "tools" / "contract_r2.json").read_text(encoding="utf-8"))["method_sha256"]:
            raise SystemExit("REFUSED: this checkout's round-2 code differs from tools/contract_r2.json; "
                             "run tools/check_conformance.py --round2 and fix that first")
    set_of = {spec["cases_sha256"]: name for name, spec in eval_contract.FROZEN.items()}
    out.parent.mkdir(parents=True, exist_ok=True)
    n = skipped = 0
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for run_id, case_id, task, label, status, prediction, metrics, seconds, error, created in db.execute(
                "SELECT run_id, case_id, task, model, status, prediction, metrics, seconds, error, created FROM vision_results "
                "ORDER BY task, model, case_id"):
            cfg = configs.get(run_id) or {}
            if cfg.get("protocol") != eval_contract.PROTOCOL:
                skipped += 1
                continue
            base, variant, mode = label_parts(label)
            case_set = set_of.get(cfg.get("cases_sha256"), "unknown")
            if not round2 and (case_set not in ("v1", "confirm") or variant not in eval_contract.V1_VARIANTS):
                skipped += 1
                continue
            row = {"schema": SCHEMA_VERSION, "side": side, "protocol": eval_contract.PROTOCOL,
                   "case_set": case_set, "cases_sha256": cfg.get("cases_sha256", ""),
                   "method_sha256": fp["method_sha256"], "prompts_sha256": fp["prompts_sha256"], "scorers_sha256": fp["scorers_sha256"],
                   "run_id": run_id, "case_id": case_id, "task": task, "model": base, "variant": variant, "mode": mode, "run": run,
                   "weights": cfg.get("weights"), "status": status, "prediction": json.loads(prediction) if prediction else None,
                   "metrics": json.loads(metrics) if metrics else None, "seconds": float(seconds or 0), "error": error, "created": created}
            if case_set == "v2" or variant not in eval_contract.V1_VARIANTS:
                row["r2_method_sha256"] = r2_hash
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
    print(json.dumps({"exported": n, "skipped_round2_or_other": skipped, "out": str(out), **fp}))
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--side", required=True, help="who ran it: desktop or laptop")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--run", type=int, default=1)
    ap.add_argument("--round2", action="store_true", help="also export round-2 cases (v2) and round-2 variants")
    a = ap.parse_args()
    export(a.root, a.side, a.out, a.run, a.round2)


if __name__ == "__main__":
    main()
