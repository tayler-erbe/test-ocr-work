"""Find, cut out and store the charts, tables and figures on each page.

Each region is saved as its own PNG with its page, box, detector and hash, so a
reviewer can jump straight to one chart and compare it against what each model
read from it. Detection runs locally: DocLayout-YOLO (a small layout model) or a
local vision model asked for boxes. Model readings of a crop are stored next to
it in region_reads.

  python regions.py --root LAB detect --pdf-dir PDFS [--detector yolo] [--classify openai:qwen3vl32b]
  python regions.py --root LAB read --model openai:qwen3vl32b [--kind table]
  python regions.py --root LAB export
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import threading
import time

from document_lab import DEFAULT_ROOT, connect, now
import vlm_client

RENDER_SCALE = 2.5  # 180 dpi: crops stay legible without huge files
PAD = 6  # px of margin around each crop at render scale
KINDS = ("figure", "table", "chart")
YOLO_WEIGHTS = ("juliozhao/DocLayout-YOLO-DocStructBench", "doclayout_yolo_docstructbench_imgsz1024.pt")
YOLO_CLASSES = {"figure": "figure", "table": "table"}  # captions and text are not cut out
MIN_SCORE = 0.25
MIN_AREA_FRACTION = 0.004  # ignore specks smaller than 0.4% of the page

REGION_SCHEMA = """
CREATE TABLE IF NOT EXISTS regions(id TEXT PRIMARY KEY, doc_id TEXT, page INTEGER, kind TEXT, subtype TEXT,
  bbox TEXT, page_size TEXT, score REAL, detector TEXT, crop_path TEXT, sha256 TEXT, created TEXT, metadata TEXT);
CREATE INDEX IF NOT EXISTS regions_doc ON regions(doc_id, page);
CREATE TABLE IF NOT EXISTS region_reads(region_id TEXT, model TEXT, task TEXT, status TEXT, output TEXT,
  seconds REAL, error TEXT, created TEXT, PRIMARY KEY(region_id, model, task));
"""


def open_db(root):
    db = connect(root)
    db.executescript(REGION_SCHEMA)
    return db


def slug(text, limit=60):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)[:limit].strip("_") or "doc"


# ---------- detectors ----------

_yolo = None
_yolo_lock = threading.Lock()


def yolo_detect(image):
    """DocLayout-YOLO on CPU. Returns [{kind, bbox:[x0,y0,x1,y1], score}] in image pixels."""
    global _yolo
    with _yolo_lock:
        if _yolo is None:
            from huggingface_hub import hf_hub_download
            from doclayout_yolo import YOLOv10
            _yolo = YOLOv10(hf_hub_download(*YOLO_WEIGHTS))
        result = _yolo.predict(image, imgsz=1024, conf=MIN_SCORE, device="cpu", verbose=False)[0]
    names = result.names
    found = []
    for box, cls, conf in zip(result.boxes.xyxy.tolist(), result.boxes.cls.tolist(), result.boxes.conf.tolist()):
        kind = YOLO_CLASSES.get(names[int(cls)])
        if kind:
            found.append({"kind": kind, "bbox": [round(v, 1) for v in box], "score": round(conf, 4)})
    return found


def yolo_all(image, conf=MIN_SCORE):
    """Every DocLayout-YOLO box with its raw class name (title, plain text, figure, table, isolate_formula, abandon, ...)."""
    yolo_detect(image)  # loads the model once
    with _yolo_lock:
        result = _yolo.predict(image, imgsz=1024, conf=conf, device="cpu", verbose=False)[0]
    return [{"label": result.names[int(c)], "bbox": [round(v, 1) for v in b], "score": round(s, 4)}
            for b, c, s in zip(result.boxes.xyxy.tolist(), result.boxes.cls.tolist(), result.boxes.conf.tolist())]


VLM_BOX_SCHEMA = {"type": "object", "properties": {"regions": {"type": "array", "maxItems": 30, "items": {
    "type": "object", "properties": {"kind": {"type": "string", "enum": list(KINDS)},
                                     "bbox": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4}},
    "required": ["kind", "bbox"], "additionalProperties": False}}}, "required": ["regions"], "additionalProperties": False}
VLM_BOX_PROMPT = ("Find every chart (plots, graphs), table and other figure (photo, diagram, logo, drawing) on this page. "
                  "Do not include plain paragraphs, headings or captions. For each give its kind and its bounding box as "
                  "[x0, y0, x1, y1] on a 0-1000 scale relative to the page width and height.")


def vlm_detect(image, spec, max_side=1280):
    """Ask a local vision model for boxes (Qwen-VL convention: 0-1000 relative coordinates)."""
    answer, info = vlm_client.chat(spec, VLM_BOX_PROMPT, VLM_BOX_SCHEMA, [vlm_client.png_bytes(image, max_side)], max_tokens=1500)
    w, h = image.size
    found = []
    for r in answer["regions"]:
        x0, y0, x1, y1 = r["bbox"]
        if not (0 <= x0 < x1 <= 1000 and 0 <= y0 < y1 <= 1000):
            continue
        found.append({"kind": r["kind"], "bbox": [x0 * w / 1000, y0 * h / 1000, x1 * w / 1000, y1 * h / 1000], "score": None})
    return found


def detect(image, detector):
    if detector == "yolo":
        found = yolo_detect(image)
    elif detector.startswith("vlm="):
        found = vlm_detect(image, detector[4:])
    else:
        raise ValueError(f"Unknown detector {detector!r}")
    w, h = image.size
    return [r for r in found if (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1]) >= MIN_AREA_FRACTION * w * h]


SUBTYPE_SCHEMA = {"type": "object", "properties": {"subtype": {"type": "string", "enum": [
    "bar_chart", "line_chart", "pie_chart", "scatter_plot", "other_chart", "table", "photo", "diagram", "logo_or_seal",
    "signature", "map", "other"]}}, "required": ["subtype"], "additionalProperties": False}


def classify(crop, spec):
    answer, _ = vlm_client.chat(spec, "What kind of image region is this? Pick the closest subtype.", SUBTYPE_SCHEMA,
                                [vlm_client.png_bytes(crop, 896)], max_tokens=40)
    return answer["subtype"]


# ---------- cropping and storage ----------

def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def cut(image, bbox, pad=PAD):
    w, h = image.size
    x0, y0, x1, y1 = bbox
    return image.crop((max(0, int(x0 - pad)), max(0, int(y0 - pad)), min(w, int(x1 + pad + 0.999)), min(h, int(y1 + pad + 0.999))))


def store_page(db, root, doc_id, page, image, found, detector, classify_spec=None):
    """Save each region's crop and row. Re-running replaces this detector's rows for the page."""
    folder = root / "crops" / slug(detector) / slug(doc_id)
    folder.mkdir(parents=True, exist_ok=True)
    db.execute("DELETE FROM regions WHERE doc_id=? AND page=? AND detector=?", (doc_id, page, detector))
    found = sorted(found, key=lambda r: (round(r["bbox"][1] / 40), r["bbox"][0]))  # reading order: top to bottom, left to right
    rows = []
    for n, r in enumerate(found, 1):
        crop = cut(image, r["bbox"])
        subtype = classify(crop, classify_spec) if classify_spec and r["kind"] != "table" else None
        kind = "chart" if subtype and subtype.endswith(("_chart", "_plot")) else r["kind"]
        name = f"p{page:04d}_{kind}_{n:02d}.png"
        path = folder / name
        crop.save(path, "PNG")
        data = path.read_bytes()
        rid = hashlib.sha256(f"{doc_id}|{page}|{detector}|{n}".encode()).hexdigest()[:20]
        meta = {"render_scale": RENDER_SCALE, "pad": PAD, "classifier": classify_spec}
        db.execute("INSERT OR REPLACE INTO regions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (rid, doc_id, page, kind, subtype, json.dumps(r["bbox"]), json.dumps(image.size), r["score"], detector,
                    str(path.relative_to(root)), hashlib.sha256(data).hexdigest(), now(), json.dumps(meta)))
        rows.append(rid)
    db.commit()
    return rows


def render_pages(pdf_path, scale=RENDER_SCALE):
    import pypdfium2
    pdf = pypdfium2.PdfDocument(str(pdf_path))
    try:
        for index in range(len(pdf)):
            yield index + 1, pdf[index].render(scale=scale).to_pil()
    finally:
        pdf.close()


def detect_pdfs(root, pdf_dir=None, detector="yolo", classify_spec=None, limit=None):
    """Detect regions on every page of every PDF in pdf_dir, or on library documents with a stored PDF path."""
    db = open_db(root)
    if pdf_dir:
        targets = [("pdf:" + p.stem, p) for p in sorted(Path(pdf_dir).glob("*.pdf"))]
    else:
        targets = [(doc_id, root / path if not Path(path).is_absolute() else Path(path))
                   for doc_id, path in db.execute("SELECT id, path FROM documents WHERE path LIKE '%.pdf' ORDER BY id")]
    total = 0
    for doc_id, path in targets[:limit]:
        started = time.perf_counter()
        count = 0
        for page, image in render_pages(path):
            count += len(store_page(db, root, doc_id, page, image, detect(image, detector), detector, classify_spec))
        total += count
        print(f"{doc_id}: {count} regions in {time.perf_counter() - started:.1f}s", flush=True)
    print(f"{total} regions stored under {root / 'crops'}")


# ---------- reading each crop with a local model ----------

TABLE_SCHEMA = {"type": "object", "properties": {
    "title": {"type": "string"},
    "header": {"type": "array", "items": {"type": "string"}, "maxItems": 40},
    "rows": {"type": "array", "maxItems": 200, "items": {"type": "array", "items": {"type": "string"}, "maxItems": 40}},
    "notes": {"type": "string"}}, "required": ["header", "rows"], "additionalProperties": False}
READ_PROMPTS = {
    "table": "Transcribe this table exactly. Copy every cell's text and number as printed, keep empty cells as empty strings, "
             "and keep merged header text in each column it spans.",
    "chart": "Extract the data shown in this chart as a table: the first column is the category or x value, one column per "
             "series, using the series names from the legend or axis. Read values as precisely as the chart allows; do not "
             "invent series. Put the chart title in title and the axis units in notes.",
    "figure": "Describe what this figure shows in notes. If it contains a table or chart, also extract it into header and rows; "
              "otherwise leave header and rows empty.",
}


def read_regions(root, spec, kinds=KINDS, detector=None, limit=None):
    db = open_db(root)
    sql = "SELECT id, kind, crop_path FROM regions WHERE kind IN (%s)" % ",".join("?" * len(kinds))
    params = list(kinds)
    if detector:
        sql += " AND detector=?"
        params.append(detector)
    done = {r for (r,) in db.execute("SELECT region_id FROM region_reads WHERE model=? AND status='ok'", (spec,))}
    todo = [row for row in db.execute(sql + " ORDER BY doc_id, page, id", params) if row[0] not in done][:limit]
    from PIL import Image
    for rid, kind, crop_path in todo:
        image = Image.open(root / crop_path)
        try:
            answer, info = vlm_client.chat(spec, READ_PROMPTS[kind], TABLE_SCHEMA, [vlm_client.png_bytes(image, 1600)], max_tokens=4000)
            db.execute("INSERT OR REPLACE INTO region_reads VALUES(?,?,?,?,?,?,?,?)",
                       (rid, spec, "read_" + kind, "ok", json.dumps(answer), info["seconds"], None, now()))
        except Exception as error:  # a failed read is recorded, never silently dropped
            db.execute("INSERT OR REPLACE INTO region_reads VALUES(?,?,?,?,?,?,?,?)",
                       (rid, spec, "read_" + kind, "failed", None, None, f"{type(error).__name__}: {error}"[:500], now()))
        db.commit()
    print(f"{spec}: read {len(todo)} regions")


def export(root):
    db = open_db(root)
    out = root / "crops" / "manifest.jsonl"
    reads = {}
    for rid, model, task, status, output, seconds, error in db.execute(
            "SELECT region_id, model, task, status, output, seconds, error FROM region_reads"):
        reads.setdefault(rid, []).append({"model": model, "task": task, "status": status, "seconds": seconds, "error": error,
                                          "output": json.loads(output) if output else None})
    with out.open("w", encoding="utf-8") as f:
        for row in db.execute("SELECT id, doc_id, page, kind, subtype, bbox, page_size, score, detector, crop_path, sha256 FROM regions ORDER BY doc_id, page, id"):
            keys = ("id", "doc_id", "page", "kind", "subtype", "bbox", "page_size", "score", "detector", "crop_path", "sha256")
            item = dict(zip(keys, row))
            item["bbox"], item["page_size"] = json.loads(item["bbox"]), json.loads(item["page_size"])
            item["reads"] = reads.get(item["id"], [])
            f.write(json.dumps(item) + "\n")
    print(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("detect")
    d.add_argument("--pdf-dir", type=Path)
    d.add_argument("--detector", default="yolo", help="yolo, or vlm=<model spec> e.g. vlm=openai:qwen3vl32b")
    d.add_argument("--classify", help="model spec used to label figures as chart/photo/diagram")
    d.add_argument("--limit", type=int)
    r = sub.add_parser("read")
    r.add_argument("--model", required=True)
    r.add_argument("--kind", action="append", choices=KINDS)
    r.add_argument("--detector")
    r.add_argument("--limit", type=int)
    sub.add_parser("export")
    args = parser.parse_args()
    if args.command == "detect":
        detect_pdfs(args.root, args.pdf_dir, args.detector, args.classify, args.limit)
    elif args.command == "read":
        read_regions(args.root, args.model, tuple(args.kind or KINDS), args.detector, args.limit)
    else:
        export(args.root)


if __name__ == "__main__":
    main()
