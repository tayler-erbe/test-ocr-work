"""Round 2 runner: development runs, the pre-registered selection rule, then the confirmation runs (PLAN.md).

  .venv/Scripts/python -X utf8 docs/research/vision-eval/improvements/run_round2.py --root C:/dev/ocr-lab

Resumable: vision_eval.run skips cases already stored for the same run. Uses the 8001 vLLM server as it is.
"""
import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
MODEL = "openai:qwen3vl32b"
CHART_CANDIDATES = ("selfcheck", "vote3", "readfirst")  # fixed in PLAN.md before any v2 run


def ve(root, *args):
    cmd = [sys.executable, "-X", "utf8", str(REPO / "vision_eval.py"), "--root", str(root), *args]
    print(">>", " ".join(args), flush=True)
    subprocess.run(cmd, cwd=REPO, check=True)


def mean(db, task, label, metric):
    rows = db.execute("SELECT status, metrics FROM vision_results WHERE task=? AND model=?", (task, label)).fetchall()
    vals = [float((json.loads(m) or {}).get(metric) or 0) if s == "complete" and m else 0.0 for s, m in rows]
    return (sum(vals) / len(vals) if vals else None), len(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    w = ["--workers", str(a.workers)]
    # 1. development
    for v in ("baseline", "selfcheck", "upscale", "readfirst"):
        ve(a.root, "run", "--model", MODEL, "--task", "chart_qa_dev2", "--cases", "v2", "--variant", v, *w)
    ve(a.root, "vote", "--model", MODEL, "--task", "chart_qa_dev2", "--cases", "v2")
    ve(a.root, "run", "--model", MODEL, "--task", "page_text", "--variant", "layoutmask", "--workers", "2")
    # 2. selection (pre-registered)
    db = sqlite3.connect(a.root / "library.sqlite3")
    dev = {v: mean(db, "chart_qa_dev2", f"{MODEL} [{v}]", "correct") for v in CHART_CANDIDATES}
    dev["baseline"] = mean(db, "chart_qa_dev2", MODEL, "correct")
    chosen = max(CHART_CANDIDATES, key=lambda v: dev[v][0])
    pt_base, _ = mean(db, "page_text", MODEL, "word_f1")
    pt_mask, _ = mean(db, "page_text", f"{MODEL} [layoutmask]", "word_f1")
    decision = {"chart_qa_dev2": dev, "chart_choice": chosen, "page_text_dev": {"baseline": pt_base, "layoutmask": pt_mask},
                "page_text_confirm": pt_mask >= pt_base}
    out = REPO / "docs/research/vision-eval/improvements/selection.json"
    out.write_text(json.dumps(decision, indent=1), encoding="utf-8")
    print(json.dumps(decision), flush=True)
    # 3. confirmation
    ve(a.root, "run", "--model", MODEL, "--task", "chart_qa_confirm2", "--cases", "v2", "--variant", "baseline", *w)
    if chosen == "vote3":
        for v in ("selfcheck", "upscale"):
            ve(a.root, "run", "--model", MODEL, "--task", "chart_qa_confirm2", "--cases", "v2", "--variant", v, *w)
        ve(a.root, "vote", "--model", MODEL, "--task", "chart_qa_confirm2", "--cases", "v2")
    else:
        ve(a.root, "run", "--model", MODEL, "--task", "chart_qa_confirm2", "--cases", "v2", "--variant", chosen, *w)
    if decision["page_text_confirm"]:
        for v in ("baseline", "layoutmask"):
            ve(a.root, "run", "--model", MODEL, "--task", "page_text_confirm2", "--cases", "v2", "--variant", v, "--workers", "2")
    ve(a.root, "compare")
    ve(a.root, "report")
    print("round 2 done", flush=True)


if __name__ == "__main__":
    main()
