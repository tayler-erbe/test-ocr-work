"""Dedicated document parsers on the frozen page tasks (protocol vision-v3-parsers, round 3, 26 Oct 2026).

Same frozen cases and the same scorers as vision_eval.py (imported, never copied): word F1 and numeric
recall on whole pages, TEDS / cell F1 / numeric recall on table crops, precision and recall at IoU 0.5 on
layout. The parsers are not chat models, so each gets the prompt or control tokens its authors publish
and an adapter that turns its native output into the shapes the scorers already take. The mapping is
fixed here and recorded in every run's config; vision_eval.py is not changed.

Backends (all OpenAI-compatible chat on 127.0.0.1, one model on the GPU at a time):
  olmocr2        allenai/olmOCR-2-7B-1025-FP8, its published no-anchoring prompt, markdown with HTML tables
  paddleocrvl    PaddlePaddle/PaddleOCR-VL-1.6 element prompts: "OCR:" for pages, "Table Recognition:" for tables
  nemotron-parse nvidia/Nemotron-3.5-Parse control tokens; blocks, classes and boxes via its postprocessing helpers

Page text follows the instruction the vision models were given ("skip tables, figures and display
equations"): table, picture, chart and display-formula blocks are dropped, everything else is kept.
Tables are flattened to header + rows exactly like the vision models' schema, so spans count the same way.

  python -X utf8 parser_eval.py --root C:/dev/ocr-lab run --backend olmocr2 --url http://127.0.0.1:8001/v1 --task page_text --task page_text_confirm2
  python -X utf8 parser_eval.py --root C:/dev/ocr-lab report --out results/vision/round3/parsers.json
"""
import argparse
import base64
import hashlib
import html as html_lib
import io
import json
import os
from pathlib import Path
import re
import statistics
import sys
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vision_eval as ve  # noqa: E402
from document_lab import connect, now  # noqa: E402

PROTOCOL = "vision-v3-parsers"
TASK_CASES = {"page_text": "v1", "page_text_confirm2": "v2", "table": "v1", "table_confirm": "confirm", "layout": "v1"}
SKIP_CLASS = re.compile(r"table|picture|figure|chart|formula|equation", re.I)

OLMOCR_PROMPT = ("Attached is one page of a document that you must process. Just return the plain text representation "
                 "of this document as if you were reading it naturally. Convert equations to LateX and tables to HTML.\n"
                 "If there are any figures or charts, label them with the following markdown syntax "
                 "![Alt text describing the contents of the figure](page_startx_starty_width_height.png)\n"
                 "Return your output as markdown, with a front matter section on top specifying values for the "
                 "primary_language, is_rotation_valid, rotation_correction, is_table, and is_diagram parameters.")
PARSE_PROMPT = "</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>"

BACKENDS = {
    "olmocr2": {"side": 1288, "max_tokens": 8192, "prompts": {"page": OLMOCR_PROMPT, "table": OLMOCR_PROMPT}},
    "paddleocrvl": {"side": 1800, "max_tokens": 8192, "prompts": {"page": "OCR:", "table": "Table Recognition:"}},
    "nemotron-parse": {"side": 2048, "max_tokens": 8744, "prompts": {"page": PARSE_PROMPT, "table": PARSE_PROMPT, "layout": PARSE_PROMPT},
                       "extra": {"repetition_penalty": 1.1, "top_k": 1, "skip_special_tokens": False}},
}


# ---------- transport ----------

def served_model(url):
    with urllib.request.urlopen(url + "/models", timeout=20) as r:
        data = json.load(r)["data"][0]
    return data["id"], {"id": data["id"], "root": data.get("root"), "max_model_len": data.get("max_model_len")}


def chat(url, model, prompt, image, side, max_tokens, extra=None, timeout=1800):
    png = ve.vlm_client.png_bytes(image, side)
    body = {"model": model, "temperature": 0, "max_tokens": max_tokens, "stream": False,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}}]}]}
    if extra:
        body.update(extra)
    request = urllib.request.Request(url + "/chat/completions", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as r:
        raw = json.load(r)
    choice = raw["choices"][0]
    if choice.get("finish_reason") != "stop":  # truncated output is a failure, never a partial credit
        raise ValueError("non_stop_generation: " + str(choice.get("finish_reason")))
    return choice["message"]["content"] or "", raw.get("usage", {})


# ---------- adapters: native output -> scorer shapes ----------

def strip_front_matter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip()
    return text


def markdown_page_text(text):
    """Drop what the gold page text leaves out: tables, figures, display equations."""
    text = re.sub(r"<table.*?</table>", " ", text, flags=re.S | re.I)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\$\$.*?\$\$|\\\[.*?\\\]", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return html_lib.unescape(text)


def html_to_grid(markup):
    rows = [[c[0] for c in r] for r in ve.parse_html_table(markup)]
    rows = [r for r in rows if r]
    if not rows:
        return {"header": [], "rows": []}
    return {"header": rows[0], "rows": rows[1:]}


def first_table(text):
    m = re.search(r"<table.*?</table>", text, flags=re.S | re.I)
    if m:
        return m.group(0)
    if re.search(r"<tr", text, flags=re.I):  # unclosed table markup
        return text[text.lower().find("<t"):]
    return ""


_parse_helpers = {}


def parse_document(raw, image_size):
    """Nemotron Parse raw string -> {'markdown', 'blocks': [{'class','bbox_pixels','content','text'}]} via its own helpers."""
    if "fn" not in _parse_helpers:
        helpers = Path(__import__("os").environ.get("NEMOTRON_PARSE_HELPERS", "C:/dev/ocr-lab/models/nemotron-parse-helpers"))
        sys.path.insert(0, str(helpers))
        from nemotron_parse import postprocess_document, PostprocessOptions  # type: ignore
        _parse_helpers["fn"] = postprocess_document
        _parse_helpers["options"] = PostprocessOptions(infer_headers=True, render_charts=True)
    return _parse_helpers["fn"](raw, image_size=image_size, options=_parse_helpers["options"])


def adapt(backend, task, raw, image):
    """-> (prediction stored as JSON, scorer input)."""
    base = ve.base_task(task)
    if backend == "nemotron-parse":
        document = parse_document(raw, image.size)
        blocks = document.get("blocks") or []
        if base == "page_text":
            kept = [b for b in blocks if not SKIP_CLASS.search(str(b.get("class", "")))]
            text = "\n".join(html_lib.unescape(re.sub(r"<[^>]+>", " ", str(b.get("content") or b.get("text") or ""))) for b in kept)
            return {"text": text, "classes": sorted({str(b.get("class")) for b in blocks})}, text
        if base == "table":
            tables = [b for b in blocks if str(b.get("class", "")).lower() == "table"]
            markup = str(tables[0].get("content") or "") if tables else first_table(document.get("markdown") or "")
            grid = html_to_grid(markup)
            return {**grid, "table_blocks": len(tables)}, grid
        if base == "layout":
            found = []
            for b in blocks:
                cls = str(b.get("class", "")).lower()
                box = b.get("bbox_pixels")
                if not box:
                    continue
                if cls == "table":
                    found.append({"kind": "table", "bbox": list(box)})
                elif cls in ("picture", "figure", "chart"):
                    found.append({"kind": "figure", "bbox": list(box)})
            return {"regions": found}, found
    text = strip_front_matter(raw) if backend == "olmocr2" else raw
    if base == "page_text":
        page = markdown_page_text(text)
        return {"text": page, "raw_chars": len(raw)}, page
    if base == "table":
        grid = html_to_grid(first_table(text))
        return grid, grid
    raise ValueError(f"{backend} does not do {task}")


def score(task, case, scorer_input):
    base = ve.base_task(task)
    if base == "page_text":
        p, r, f = ve.f1(ve.words(case["gold"]), ve.words(scorer_input))
        _, nr, _ = ve.f1(ve.numbers(case["gold"]), ve.numbers(scorer_input))
        return {"word_precision": p, "word_recall": r, "word_f1": f, "numeric_recall": nr}
    if base == "table":
        return ve.score_table(case["gold"], scorer_input)
    if base == "layout":
        return ve.score_layout(case["gold"], scorer_input)
    raise ValueError(task)


# ---------- run ----------

def run_case(root, backend, url, model, task, case):
    spec = BACKENDS[backend]
    base = ve.base_task(task)
    kind = "page" if base == "page_text" else base
    if kind not in spec["prompts"]:
        raise ValueError(f"{backend} has no prompt for {task}")
    image = ve.load_image(root, case)
    ve.save_eval_crop(root, case, image)
    raw, usage = chat(url, model, spec["prompts"][kind], image, spec["side"], spec["max_tokens"], spec.get("extra"))
    prediction, scorer_input = adapt(backend, task, raw, image)
    prediction["usage"] = usage
    return prediction, score(task, case, scorer_input)


def run(root, backend, url, tasks, limit=None, workers=1):
    model, served = served_model(url)
    db = connect(root)
    db.execute(ve.RESULT_SCHEMA)
    spec = BACKENDS[backend]
    for task in tasks:
        manifest = ve.load_cases(root, TASK_CASES[task])
        config = {"protocol": PROTOCOL, "cases_sha256": manifest["cases_sha256"], "task": task, "model": "parser:" + backend,
                  "weights": served, "side": spec["side"], "max_tokens": spec["max_tokens"], "prompt": spec["prompts"]["page" if ve.base_task(task) == "page_text" else ve.base_task(task)],
                  "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        run_id = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:24]
        db.execute("INSERT OR IGNORE INTO runs(id, model, started, config, status) VALUES(?,?,?,?,?)",
                   (run_id, "parser:" + backend, now(), json.dumps(config), "running"))
        done = {c for (c,) in db.execute("SELECT case_id FROM vision_results WHERE run_id=?", (run_id,))}
        cases = [c for c in manifest["cases"] if c["task"] == task and c["id"] not in done][:limit]
        label = "parser:" + backend
        from concurrent.futures import ThreadPoolExecutor

        def one(case):
            started = time.perf_counter()
            try:
                prediction, metrics = run_case(root, backend, url, model, task, case)
                status, error = "complete", None
            except Exception as exc:  # failures stay in the denominator
                prediction, metrics, status, error = None, None, "failed", f"{type(exc).__name__}: {exc}"[:500]
            return prediction, metrics, status, error, time.perf_counter() - started

        pause_file = os.environ.get("ROUND3_PAUSE_FILE")
        n = 0
        step = max(1, workers)
        with ThreadPoolExecutor(max_workers=step) as pool:
            for start in range(0, len(cases), step):  # one batch at a time, so a pause takes effect within one batch
                if pause_file and Path(pause_file).exists():
                    print(json.dumps({"paused": True, "backend": backend, "task": task, "done": n, "of": len(cases)}), flush=True)
                    sys.exit(75)
                batch = cases[start:start + step]
                for case, (prediction, metrics, status, error, seconds) in zip(batch, pool.map(one, batch)):
                    n += 1
                    db.execute("INSERT OR REPLACE INTO vision_results VALUES(?,?,?,?,?,?,?,?,?,?)",
                               (run_id, case["id"], task, label, status, json.dumps(prediction), json.dumps(metrics), seconds, error, now()))
                    db.commit()
                    if n % 20 == 0 or n == len(cases):
                        print(json.dumps({"backend": backend, "task": task, "done": n, "of": len(cases), "run_id": run_id}), flush=True)
        db.execute("UPDATE runs SET status='complete' WHERE id=?", (run_id,))
        db.commit()


def report(root, out):
    db = connect(root)
    db.execute(ve.RESULT_SCHEMA)
    summary = []
    for run_id, model, config in db.execute("SELECT id, model, config FROM runs WHERE config LIKE ?", (f'%"protocol": "{PROTOCOL}"%',)):
        cfg = json.loads(config)
        rows = [(st, json.loads(m) if m else None, s) for st, m, s in db.execute("SELECT status, metrics, seconds FROM vision_results WHERE run_id=?", (run_id,))]
        if not rows:
            continue
        agg = ve.aggregate(cfg["task"], rows)
        summary.append({"run_id": run_id, "model": model, "task": cfg["task"], "weights": cfg["weights"], "side": cfg["side"],
                        "max_tokens": cfg["max_tokens"], **agg})
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"protocol": PROTOCOL, "generated": now(), "runs": summary}, indent=2), encoding="utf-8")
    for s in summary:
        print(json.dumps(s))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, required=True)
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--backend", required=True, choices=sorted(BACKENDS))
    r.add_argument("--url", default="http://127.0.0.1:8001/v1")
    r.add_argument("--task", action="append", required=True, choices=sorted(TASK_CASES))
    r.add_argument("--limit", type=int)
    r.add_argument("--workers", type=int, default=4)
    p = sub.add_parser("report")
    p.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.cmd == "run":
        run(args.root, args.backend, args.url.rstrip("/"), args.task, args.limit, args.workers)
    else:
        report(args.root, args.out)


if __name__ == "__main__":
    main()
