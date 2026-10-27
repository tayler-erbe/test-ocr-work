"""Vision-language comparator rows for round 3b (protocol vision-v3-vlm): the frozen page and table prompts of
vision_eval.py, the same scorers, but on the fresh v3 sets and at a chosen output budget (docs/round3/PREREG_3B.md:
8,192 tokens for every model on the confirmation sets; 8,744 as the budget-sensitivity arm on page_text_confirm2).
vision_eval.py itself is not changed, so every earlier row and its conformance fingerprint stand.

  python -X utf8 tools/vlm_v3.py --root C:/dev/ocr-lab --model openai:qwen3vl32b --task page_text_confirm3 --task table_confirm3 --max-tokens 8192 --control-dir C:/dev/ocr-lab/round3-control
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
import regions  # noqa: E402
from document_lab import connect, now  # noqa: E402
from campaign_control import paused, bounded_results, acquire_lock  # noqa: E402
from parser_eval import load_cases, base_task, load_image, TASK_CASES  # noqa: E402

PROTOCOL = "vision-v3-vlm"
PAGE_PROMPT = ("Transcribe all the running text on this page in reading order: headings, paragraphs, lists, "
               "captions, headers and footers. Skip tables, figures and display equations.")  # identical to vision_eval.run_case


def run_case(root, model, case, max_tokens):
    base = base_task(case["task"])
    image = load_image(root, case)
    ve.save_eval_crop(root, case, image)
    if base == "page_text":
        out, _ = vlm_client.chat(model, PAGE_PROMPT, ve.TEXT_SCHEMA, [vlm_client.png_bytes(image, 1800)], max_tokens=max_tokens)
        p, r, f = ve.f1(ve.words(case["gold"]), ve.words(out["text"]))
        _, nr, _ = ve.f1(ve.numbers(case["gold"]), ve.numbers(out["text"]))
        return out, {"word_precision": p, "word_recall": r, "word_f1": f, "numeric_recall": nr}
    if base == "table":
        out, _ = vlm_client.chat(model, regions.READ_PROMPTS["table"], regions.TABLE_SCHEMA, [vlm_client.png_bytes(image, 1600)], max_tokens=max_tokens)
        return out, ve.score_table(case["gold"], out)
    raise ValueError(case["task"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--task", action="append", required=True, choices=sorted(TASK_CASES))
    parser.add_argument("--max-tokens", type=int, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--control-dir", type=Path, required=True)
    args = parser.parse_args()
    if paused(args.control_dir):
        print("PAUSED: no inference performed")
        return
    acquire_lock(args.root / "evaluation" / "vlm-v3-runner.LOCAL_ONLY.lock")
    weights = vlm_client.model_digest(args.model)
    if not weights:
        raise SystemExit(f"{args.model} is not being served right now")
    db = connect(args.root)
    db.execute(ve.RESULT_SCHEMA)
    label = f"{args.model} [budget{args.max_tokens}]"
    for task in args.task:
        if paused(args.control_dir):
            break
        manifest = load_cases(args.root, TASK_CASES[task])
        config = {"protocol": PROTOCOL, "cases_sha256": manifest["cases_sha256"], "task": task, "model": args.model, "weights": weights,
                  "max_tokens": args.max_tokens, "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        run_id = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:24]
        db.execute("INSERT OR IGNORE INTO runs(id, model, started, config, status) VALUES(?,?,?,?,?)", (run_id, label, now(), json.dumps(config), "running"))
        done = {c for (c,) in db.execute("SELECT case_id FROM vision_results WHERE run_id=?", (run_id,))}
        cases = [c for c in manifest["cases"] if c["task"] == task and c["id"] not in done][: args.limit]

        def one(case):
            started = time.perf_counter()
            try:
                prediction, metrics = run_case(args.root, args.model, case, args.max_tokens)
                status, error = "complete", None
            except Exception as exc:  # failures stay in the denominator
                prediction, metrics, status, error = None, None, "failed", f"{type(exc).__name__}: {exc}"[:500]
            return prediction, metrics, status, error, time.perf_counter() - started

        n = 0
        for case, (prediction, metrics, status, error, seconds) in bounded_results(cases, one, args.workers, args.control_dir):
            n += 1
            db.execute("INSERT OR REPLACE INTO vision_results VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (run_id, case["id"], task, label, status, json.dumps(prediction), json.dumps(metrics), seconds, error, now()))
            db.commit()
            if n % 20 == 0 or n == len(cases):
                print(json.dumps({"model": label, "task": task, "done": n, "of": len(cases)}), flush=True)
        recorded = db.execute("SELECT COUNT(*) FROM vision_results WHERE run_id=?", (run_id,)).fetchone()[0]
        expected = sum(c["task"] == task for c in manifest["cases"])
        state = "complete" if recorded == expected else "paused" if paused(args.control_dir) else "partial"
        db.execute("UPDATE runs SET status=? WHERE id=?", (state, run_id))
        db.commit()
        print(json.dumps({"run_id": run_id, "status": state, "recorded": recorded, "expected": expected}), flush=True)


if __name__ == "__main__":
    main()
