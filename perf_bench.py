"""Serving performance for a local vision model: latency, throughput and GPU memory under concurrency.

Uses held-out ChartQA chart images with the baseline chart-question prompt, so the request shape matches
the quality evaluation. Answers are not scored here; this measures speed and capacity only.

  python perf_bench.py --root LAB --model openai:qwen3vl32b --concurrency 1 2 4 8 16
  python perf_bench.py --root LAB --model ollama:qwen3.8:27b --concurrency 1
"""
import argparse
import concurrent.futures
import json
from pathlib import Path
import statistics
import subprocess
import time
import urllib.request

from document_lab import DEFAULT_ROOT, now
import vision_eval
import vlm_client


def gpu_memory_mib():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total,name", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20).stdout.strip().split(", ")
        return {"used_mib": int(out[0]), "total_mib": int(out[1]), "gpu": out[2]}
    except Exception as error:
        return {"error": str(error)}


def ollama_vram(name):
    try:
        with urllib.request.urlopen(vlm_client.OLLAMA_URL + "/api/ps", timeout=10) as r:
            for m in json.load(r)["models"]:
                if m["name"] == name:
                    return {"size_vram_gb": round(m["size_vram"] / 1e9, 2), "size_gb": round(m["size"] / 1e9, 2)}
    except Exception:
        pass
    return None


def one(root, model, case):
    image = vlm_client.png_bytes(vision_eval.load_image(root, case), 1600)
    started = time.perf_counter()
    try:
        _, info = vlm_client.chat(model, "Answer the question about this chart. Reply with only the answer: a number without units, "
                                  "or a short word or phrase.\nQuestion: " + case["question"], vision_eval.ANSWER_SCHEMA, [image], max_tokens=300)
        return {"ok": True, "seconds": time.perf_counter() - started, "prompt_tokens": info.get("prompt_tokens"), "output_tokens": info.get("output_tokens")}
    except Exception as error:
        return {"ok": False, "seconds": time.perf_counter() - started, "error": f"{type(error).__name__}: {error}"[:200]}


def bench(root, model, levels, per_level):
    cases = [c for c in vision_eval.load_cases(root, "confirm")["cases"] if c["task"] == "chart_qa_confirm"]
    one(root, model, cases[0])  # warm-up: load weights and compile before timing
    results = []
    for level in levels:
        batch = cases[1:1 + max(per_level, level * 4)]
        started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(level) as pool:
            rows = list(pool.map(lambda c: one(root, model, c), batch))
        wall = time.perf_counter() - started
        ok = [r for r in rows if r["ok"]]
        lat = sorted(r["seconds"] for r in ok)
        row = {"concurrency": level, "requests": len(rows), "failed": len(rows) - len(ok), "wall_seconds": round(wall, 2),
               "requests_per_second": round(len(ok) / wall, 3),
               "p50_seconds": round(statistics.median(lat), 3) if lat else None,
               "p95_seconds": round(lat[min(len(lat) - 1, int(0.95 * len(lat)))], 3) if lat else None,
               "mean_prompt_tokens": round(statistics.mean(r["prompt_tokens"] or 0 for r in ok)) if ok else None,
               "gpu": gpu_memory_mib()}
        results.append(row)
        print(json.dumps(row), flush=True)
    provider, name = vlm_client.parse_model(model)
    record = {"model": model, "weights": vlm_client.model_digest(model), "created": now(), "per_level_minimum": per_level,
              "ollama_vram": ollama_vram(name) if provider == "ollama" else None, "levels": results}
    out = root / "reports" / "perf"
    out.mkdir(parents=True, exist_ok=True)
    path = out / (model.replace(":", "_").replace("/", "_") + ".json")
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--model", required=True)
    parser.add_argument("--concurrency", type=int, nargs="+", default=[1])
    parser.add_argument("--per-level", type=int, default=24)
    args = parser.parse_args()
    bench(args.root, args.model, args.concurrency, args.per_level)


if __name__ == "__main__":
    main()
