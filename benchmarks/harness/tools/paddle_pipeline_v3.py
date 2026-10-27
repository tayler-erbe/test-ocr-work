"""PaddleOCR-VL-1.6 through its OFFICIAL pipeline (layout detection + element recognition) on frozen cases.
Runs under WSL with ~/paddle_venv/bin/python; the VL model is the one already served by vLLM on 127.0.0.1:8001
(key paddleocrvl16), so recognition weights are identical to the bare arm and only the pipeline differs.
Writes one JSONL row per case {"case_id","task","markdown","seconds","error","engine"} for parser_eval.py import.

  ~/paddle_venv/bin/python /mnt/c/dev/test-ocr-work/benchmarks/harness/tools/paddle_pipeline_v3.py \
      --manifest /mnt/c/dev/ocr-lab/evaluation/vision_cases_v3.json --root /mnt/c/dev/ocr-lab \
      --task page_text_confirm3 --task table_confirm3 --out /mnt/c/dev/ocr-lab/round3/paddle_pipeline_v3.jsonl
Pause: stops between cases when <control-dir>/PAUSE exists; rerun skips cases already in the output file.
"""
import argparse
import io
import json
from pathlib import Path
import time

parser = argparse.ArgumentParser()
parser.add_argument("--manifest", type=Path, required=True)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--task", action="append", required=True)
parser.add_argument("--out", type=Path, required=True)
parser.add_argument("--served", default="paddleocrvl16")
parser.add_argument("--control-dir", type=Path, default=Path("/mnt/c/dev/ocr-lab/round3-control"))
parser.add_argument("--limit", type=int)
args = parser.parse_args()

from PIL import Image  # noqa: E402
from paddleocr import PaddleOCRVL  # noqa: E402

ENGINE = "paddleocr_vl_1.6_pipeline"
cases = [c for c in json.loads(args.manifest.read_text(encoding="utf-8"))["cases"] if c["task"] in args.task]
done = set()
if args.out.exists():
    done = {json.loads(l)["case_id"] for l in args.out.read_text(encoding="utf-8").splitlines() if l.strip()}
cases = [c for c in cases if c["id"] not in done][: args.limit]
pipe = PaddleOCRVL(pipeline_version="v1.6", vl_rec_backend="vllm-server", vl_rec_server_url="http://127.0.0.1:8001/v1",
                   vl_rec_api_model_name=args.served, vl_rec_max_concurrency=4, use_doc_orientation_classify=False, use_doc_unwarping=False)


def load(case):
    image = Image.open(args.root / case["image"]).convert("RGB")
    if case.get("crop_box"):
        x0, y0, x1, y1 = case["crop_box"]
        image = image.crop((max(0, x0), max(0, y0), min(image.width, x1), min(image.height, y1)))
    return image


def markdown_of(results):
    parts = []
    for r in results:
        m = getattr(r, "markdown", None)
        if isinstance(m, dict):
            parts.append(m.get("markdown_texts") or m.get("text") or "")
        elif m:
            parts.append(str(m))
    return "\n".join(parts)


import numpy as np  # noqa: E402

for n, case in enumerate(cases, 1):
    if (args.control_dir / "PAUSE").exists():
        print(json.dumps({"paused": True, "done": n - 1, "of": len(cases)}), flush=True)
        break
    started = time.time()
    try:
        image = load(case)
        results = list(pipe.predict(np.array(image)[:, :, ::-1]))  # BGR array, as the pipeline expects
        row = {"case_id": case["id"], "task": case["task"], "markdown": markdown_of(results), "error": None}
    except Exception as exc:  # recorded, never hidden
        row = {"case_id": case["id"], "task": case["task"], "markdown": "", "error": repr(exc)[:300]}
    row.update(seconds=time.time() - started, engine=ENGINE)
    with args.out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    if n % 10 == 0 or n == len(cases):
        print(json.dumps({"done": n, "of": len(cases)}), flush=True)
