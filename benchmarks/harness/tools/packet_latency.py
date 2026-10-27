"""Packet-level latency (round 3b): one fixed queue of 20 fresh pages and 20 fresh tables (first by id from
vision_cases_v3.json), run at concurrency 1 and 4 against whatever is being served, timing every request and the
whole queue. Writes results/vision/round3/latency.json (appends one entry per model and concurrency).

  python -X utf8 tools/packet_latency.py --root C:/dev/ocr-lab --backend paddleocrvl --url http://127.0.0.1:8001/v1 --out ../../results/vision/round3/latency.json
  python -X utf8 tools/packet_latency.py --root C:/dev/ocr-lab --vlm openai:qwen3vl32b --out ...
Outputs are timed, not scored (the scored rows come from the evaluation runs).
"""
import argparse
import json
from pathlib import Path
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import parser_eval as pe  # noqa: E402
import vision_eval as ve  # noqa: E402
import vlm_client  # noqa: E402
import regions  # noqa: E402
from vlm_v3 import PAGE_PROMPT  # noqa: E402

BUDGET = 8192


def queue(root):
    m = pe.load_cases(root, "v3")
    pages = sorted((c for c in m["cases"] if c["task"] == "page_text_confirm3"), key=lambda c: c["id"])[:20]
    tables = sorted((c for c in m["cases"] if c["task"] == "table_confirm3"), key=lambda c: c["id"])[:20]
    return pages + tables


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--backend", choices=sorted(k for k in pe.BACKENDS if k != "paddle-pipeline"))
    parser.add_argument("--vlm", help="vision model spec for vlm_client, e.g. openai:qwen3vl32b")
    parser.add_argument("--url", default="http://127.0.0.1:8001/v1")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.backend and not args.vlm:
        raise SystemExit("--backend or --vlm")
    cases = queue(args.root)
    images = {c["id"]: pe.load_image(args.root, c) for c in cases}
    if args.backend:
        model, served = pe.served_model(args.url)
        spec = {**pe.BACKENDS[args.backend], "max_tokens": BUDGET}
        name = "parser:" + args.backend

        def one(case):
            kind = "page" if pe.base_task(case["task"]) == "page_text" else "table"
            t0 = time.perf_counter()
            try:
                pe.chat(args.url, model, spec["prompts"][kind], images[case["id"]], spec["side"], spec["max_tokens"], spec.get("extra"))
                ok = True
            except Exception:
                ok = False
            return time.perf_counter() - t0, ok
    else:
        name = args.vlm
        served = vlm_client.model_digest(args.vlm)

        def one(case):
            t0 = time.perf_counter()
            try:
                if pe.base_task(case["task"]) == "page_text":
                    vlm_client.chat(args.vlm, PAGE_PROMPT, ve.TEXT_SCHEMA, [vlm_client.png_bytes(images[case["id"]], 1800)], max_tokens=BUDGET)
                else:
                    vlm_client.chat(args.vlm, regions.READ_PROMPTS["table"], regions.TABLE_SCHEMA, [vlm_client.png_bytes(images[case["id"]], 1600)], max_tokens=BUDGET)
                ok = True
            except Exception:
                ok = False
            return time.perf_counter() - t0, ok
    entries = []
    for concurrency in (1, 4):
        one(cases[0])  # warm-up, untimed
        wall0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            results = list(pool.map(one, cases))
        wall = time.perf_counter() - wall0
        secs = sorted(s for s, _ in results)
        entry = {"model": name, "served": served, "concurrency": concurrency, "queue": {"pages": 20, "tables": 20}, "budget": BUDGET,
                 "wall_seconds": round(wall, 1), "cases_per_minute": round(60 * len(cases) / wall, 1),
                 "p50": round(statistics.median(secs), 2), "p95": round(secs[int(0.95 * (len(secs) - 1))], 2), "max": round(secs[-1], 2),
                 "failed": sum(1 for _, ok in results if not ok), "when": time.strftime("%Y-%m-%d %H:%M:%S")}
        entries.append(entry)
        print(json.dumps(entry), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(args.out.read_text(encoding="utf-8")) if args.out.exists() else {"entries": []}
    existing["entries"] += entries
    args.out.write_text(json.dumps(existing, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
