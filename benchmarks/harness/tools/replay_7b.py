"""Reproducibility replay (round 3b): rerun the two same-weight Qwen2.5-VL 7B comparison groups that did not
reproduce between the desktop and the laptop (routing report: chart_qa expert, +3.0 points; chart_table upscale,
-14.8 points), on this machine, with vision_eval.run_case unchanged. Rows are stored under protocol vision-v1-replay
and the label suffix [replay], so the original rows are untouched and the two runs can be compared case by case.

  python -X utf8 tools/replay_7b.py --root C:/dev/ocr-lab --control-dir C:/dev/ocr-lab/round3-control
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import vision_eval as ve  # noqa: E402
import vlm_client  # noqa: E402
from document_lab import connect, now  # noqa: E402
from campaign_control import paused, bounded_results, acquire_lock  # noqa: E402

MODEL = "ollama:qwen2.5vl:7b"
GROUPS = [("chart_qa", "expert"), ("chart_table", "upscale")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--control-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--summary-only", action="store_true", help="only recompute the agreement table from stored rows (no model calls)")
    args = parser.parse_args()
    db = connect(args.root)
    db.execute(ve.RESULT_SCHEMA)
    manifest = ve.load_cases(args.root, "v1")
    if args.summary_only:
        for task, variant in GROUPS:
            for (run_id,) in db.execute("SELECT id FROM runs WHERE model=?", (f"{MODEL} [{variant}] [replay]",)):
                agreement(db, run_id, task, variant)
        return
    if paused(args.control_dir):
        print("PAUSED")
        return
    acquire_lock(args.root / "evaluation" / "replay-runner.LOCAL_ONLY.lock")
    weights = vlm_client.model_digest(MODEL)
    if not weights:
        raise SystemExit(f"{MODEL} is not being served right now")
    for task, variant in GROUPS:
        if paused(args.control_dir):
            break
        label = f"{MODEL} [{variant}] [replay]"
        config = {"protocol": "vision-v1-replay", "cases_sha256": manifest["cases_sha256"], "task": task, "model": MODEL, "weights": weights,
                  "variant": variant, "mode": "image", "replay_of": "vision-v1 desktop rows", "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        run_id = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:24]
        db.execute("INSERT OR IGNORE INTO runs(id, model, started, config, status) VALUES(?,?,?,?,?)", (run_id, label, now(), json.dumps(config), "running"))
        done = {c for (c,) in db.execute("SELECT case_id FROM vision_results WHERE run_id=?", (run_id,))}
        cases = [c for c in manifest["cases"] if c["task"] == task and c["id"] not in done]

        def one(case):
            started = time.perf_counter()
            try:
                prediction, metrics = ve.run_case(args.root, MODEL, case, variant)
                status, error = "complete", None
            except Exception as exc:
                prediction, metrics, status, error = None, None, "failed", f"{type(exc).__name__}: {exc}"[:500]
            return prediction, metrics, status, error, time.perf_counter() - started

        n = 0
        for case, (prediction, metrics, status, error, seconds) in bounded_results(cases, one, args.workers, args.control_dir):
            n += 1
            db.execute("INSERT OR REPLACE INTO vision_results VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (run_id, case["id"], task, label, status, json.dumps(prediction), json.dumps(metrics), seconds, error, now()))
            db.commit()
            if n % 25 == 0 or n == len(cases):
                print(json.dumps({"task": task, "variant": variant, "done": n, "of": len(cases)}), flush=True)
        recorded = db.execute("SELECT COUNT(*) FROM vision_results WHERE run_id=?", (run_id,)).fetchone()[0]
        expected = sum(c["task"] == task for c in manifest["cases"])
        db.execute("UPDATE runs SET status=? WHERE id=?", ("complete" if recorded == expected else "partial", run_id))
        db.commit()
        agreement(db, run_id, task, variant)


def agreement(db, run_id, task, variant):
    """Case-by-case agreement with the stored desktop rows. A failed case stores metrics as JSON null; it counts as
    score zero on both sides, the same rule the scorer applies."""
    orig = f"{MODEL} [{variant}]"
    pairs = db.execute("SELECT a.case_id, a.metrics, b.metrics FROM vision_results a JOIN vision_results b ON a.case_id=b.case_id AND b.model=? AND b.task=a.task WHERE a.run_id=?",
                       (orig, run_id)).fetchall()
    key = "correct" if task == "chart_qa" else "value_recall"

    def score(m):
        d = json.loads(m) if m else None
        return (d or {}).get(key, 0) or 0

    agree = sum(1 for _, m1, m2 in pairs if score(m1) == score(m2))
    mean_new = sum(score(m1) for _, m1, _ in pairs) / len(pairs) if pairs else None
    mean_old = sum(score(m2) for _, _, m2 in pairs) / len(pairs) if pairs else None
    print(json.dumps({"task": task, "variant": variant, "paired": len(pairs), "identical_scores": agree,
                      "mean_replay": mean_new, "mean_original_desktop": mean_old}))


if __name__ == "__main__":
    main()
