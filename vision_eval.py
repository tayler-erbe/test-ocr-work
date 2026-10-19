"""Vision and layout evaluation (protocol vision-v1) on public benchmarks.

Every task scores local models against published answer keys with plain code; no
model grades another model. Cases are frozen to evaluation/vision_cases_v1.json the
first time they are built, so every model sees the identical cases.

Tasks
  layout       find figures and tables on OmniDocBench pages; precision/recall/F1 at IoU>=0.5
  ocr_crop     the same 50 OmniDocBench prose crops as benchmark_tasks.py ocr; CER, numeric recall
  table        transcribe OmniDocBench table crops; TEDS, cell F1, numeric-cell recall
  chart_qa     ChartQA test questions from the chart IMAGE; relaxed accuracy (5%), paired with table-only
  chart_table  pull the data table out of a ChartQA chart; numeric recall/precision within 5%
  page_text    transcribe whole OmniDocBench pages; word F1, numeric recall

  python vision_eval.py --root LAB build
  python vision_eval.py --root LAB run --model openai:qwen3vl32b --task chart_qa
  python vision_eval.py --root LAB run --model yolo --task layout
  python vision_eval.py --root LAB report
"""
import argparse
from collections import Counter
import csv
import hashlib
import html
import io
import json
import math
from pathlib import Path
import re
import statistics
import time
import unicodedata
import zipfile

from document_lab import DEFAULT_ROOT, connect, digest, now
import regions
import vlm_client

PROTOCOL = "vision-v1"
COUNTS = {"layout": 120, "ocr_crop": 50, "table": 60, "chart_qa": 200, "chart_table": 60, "page_text": 40}
TASKS = tuple(COUNTS)
RESULT_SCHEMA = """CREATE TABLE IF NOT EXISTS vision_results(run_id TEXT, case_id TEXT, task TEXT, model TEXT, status TEXT,
  prediction TEXT, metrics TEXT, seconds REAL, error TEXT, created TEXT, PRIMARY KEY(run_id, case_id));"""
CHARTQA_ZIP = "datasets/chartqa/raw/ChartQA Dataset.zip"
OMNI = "datasets/omnidocbench/raw"


# ---------- text helpers ----------

def norm(text):
    return " ".join(unicodedata.normalize("NFKC", text or "").split())


def edit_distance(a, b):
    if len(a) < len(b):
        a, b = b, a
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        nxt = [i]
        for j, y in enumerate(b, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1, row[j - 1] + (x != y)))
        row = nxt
    return row[-1]


def numbers(text):
    return Counter(re.findall(r"(?<!\w)\d+(?:[.,]\d+)*(?:%)?", text or ""))


def words(text):
    return Counter(re.findall(r"\w+", norm(text).lower()))


def f1(expected, observed):
    """Multiset F1 between two Counters; (precision, recall, f1)."""
    matched = sum((expected & observed).values())
    p = matched / sum(observed.values()) if observed else (1.0 if not expected else 0.0)
    r = matched / sum(expected.values()) if expected else 1.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def to_number(text):
    if text is None:
        return None
    t = str(text).strip().replace(",", "").replace("$", "").replace("%", "").replace("−", "-")
    try:
        return float(t)
    except ValueError:
        return None


def relaxed_match(predicted, gold, tolerance=0.05):
    """ChartQA's relaxed accuracy: numbers within 5% relative error, otherwise case-insensitive exact."""
    p, g = to_number(predicted), to_number(gold)
    if p is not None and g is not None:
        return abs(p - g) <= tolerance * abs(g) if g else p == 0
    return norm(str(predicted)).lower().rstrip(".") == norm(str(gold)).lower().rstrip(".")


# ---------- table scoring: TEDS (tree edit distance similarity, PubTabNet) ----------

def cell_text(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text).replace("$", "")
    text = re.sub(r"\\[a-zA-Z]+|[{}_^]", "", text)
    return norm(text)


def parse_html_table(markup):
    """-> rows of (text, rowspan, colspan). Tolerates the unclosed tags in gold HTML."""
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)(?=<tr|</table>|$)", markup, flags=re.S | re.I):
        cells = []
        for attrs, body in re.findall(r"<t[dh]([^>]*)>(.*?)(?=<t[dh]|</tr>|$)", tr, flags=re.S | re.I):
            rs = re.search(r"rowspan=\"?(\d+)", attrs)
            cs = re.search(r"colspan=\"?(\d+)", attrs)
            cells.append((cell_text(body), int(rs.group(1)) if rs else 1, int(cs.group(1)) if cs else 1))
        if cells:
            rows.append(cells)
    return rows


def grid_to_rows(header, body):
    rows = [[(cell_text(c), 1, 1) for c in header]] if header else []
    rows += [[(cell_text(c), 1, 1) for c in r] for r in body]
    return [r for r in rows if r]


def teds(gold_rows, pred_rows):
    from apted import APTED, Config

    class Node:
        def __init__(self, tag, text="", rs=1, cs=1):
            self.tag, self.text, self.rs, self.cs, self.children = tag, text, rs, cs, []

    class Cost(Config):
        def rename(self, a, b):
            if a.tag != b.tag or a.rs != b.rs or a.cs != b.cs:
                return 1.0
            if a.tag == "td":
                if not a.text and not b.text:
                    return 0.0
                return edit_distance(a.text, b.text) / max(len(a.text), len(b.text), 1)
            return 0.0

        def children(self, node):
            return node.children

    def tree(rows):
        root = Node("table")
        for r in rows:
            tr = Node("tr")
            tr.children = [Node("td", *c) for c in r]
            root.children.append(tr)
        return root

    def size(node):
        return 1 + sum(size(c) for c in node.children)

    g, p = tree(gold_rows), tree(pred_rows)
    distance = APTED(g, p, Cost()).compute_edit_distance()
    return 1.0 - distance / max(size(g), size(p))


# ---------- case building ----------

def omni_pages(root):
    return json.loads((root / OMNI / "OmniDocBench.json").read_text(encoding="utf-8"))


def poly_box(poly):
    return [min(poly[::2]), min(poly[1::2]), max(poly[::2]), max(poly[1::2])]


def english(info):
    return info["page_attribute"].get("language") == "english"


def build_layout(root, pages, count):
    by_source = {}
    for page in pages:
        info = page["page_info"]
        if not english(info) or not (root / OMNI / "images" / Path(info["image_path"]).name).exists():
            continue
        gold = [{"kind": d["category_type"], "bbox": poly_box(d["poly"])} for d in page["layout_dets"]
                if d["category_type"] in ("figure", "table") and str(d.get("ignore")) != "True"]
        source = info["page_attribute"].get("data_source")
        pool = "with_regions" if gold else "without_regions"
        by_source.setdefault(pool, {}).setdefault(source, []).append((digest("layout-v1:" + info["image_path"]), info["image_path"], gold))
    # Three quarters of pages contain at least one figure or table; one quarter contain none, to count false alarms.
    # Round-robin across document sources so newspapers, slides, reports and papers all appear.
    cases = []
    for pool, quota in (("with_regions", count * 3 // 4), ("without_regions", count - count * 3 // 4)):
        sources = by_source.get(pool, {})
        for v in sources.values():
            v.sort()
        taken, i = 0, 0
        while taken < quota and any(i < len(v) for v in sources.values()):
            for source in sorted(sources):
                if i < len(sources[source]) and taken < quota:
                    _, image, gold = sources[source][i]
                    cases.append({"id": "layout:" + digest(image)[:16], "task": "layout", "image": f"{OMNI}/images/{Path(image).name}",
                                  "source": source, "gold": gold})
                    taken += 1
            i += 1
    return cases


def build_ocr_crop(root, pages, count):
    """Identical selection to benchmark_tasks.ocr_benchmark so results line up with the Tesseract baseline."""
    candidates = []
    for page in pages:
        info = page["page_info"]
        for block in page["layout_dets"]:
            text = block.get("text", "")
            if block.get("ignore") or block["category_type"] != "text_block" or not 80 <= len(text) <= 700 or "$" in text or "\\" in text:
                continue
            ascii_letters = sum(c.isascii() and c.isalpha() for c in text)
            if ascii_letters / max(1, sum(c.isalpha() for c in text)) < .98:
                continue
            image = root / OMNI / "images" / Path(info["image_path"]).name
            if image.exists():
                candidates.append((digest(str(info["image_path"]) + str(block["anno_id"])), image, block))
    chosen, seen = [], set()
    for _, image, block in sorted(candidates):
        if image.name not in seen:
            chosen.append((image, block))
            seen.add(image.name)
        if len(chosen) >= count:
            break
    out = []
    for image, block in chosen:
        poly = block["poly"]
        out.append({"id": "ocr:" + digest(image.name + str(block["anno_id"]))[:16], "task": "ocr_crop",
                    "image": f"{OMNI}/images/{image.name}", "crop_box": [int(min(poly[::2])) - 4, int(min(poly[1::2])) - 4, int(max(poly[::2])) + 5, int(max(poly[1::2])) + 5],
                    "gold": norm(block["text"])})
    return out


def build_table(root, pages, count):
    found = []
    for page in pages:
        info = page["page_info"]
        if not english(info):
            continue
        for d in page["layout_dets"]:
            if d["category_type"] == "table" and d.get("html") and str(d.get("ignore")) != "True":
                rows = parse_html_table(d["html"])
                if 2 <= len(rows) <= 40 and (root / OMNI / "images" / Path(info["image_path"]).name).exists():
                    found.append((digest("table-v1:" + info["image_path"] + str(d["anno_id"])), info, d))
    found.sort(key=lambda x: x[0])
    return [{"id": "table:" + h[:16], "task": "table", "image": f"{OMNI}/images/{Path(info['image_path']).name}",
             "crop_box": [int(v) for v in poly_box(d["poly"])], "source": info["page_attribute"].get("data_source"),
             "gold": d["html"]} for h, info, d in found[:count]]


def build_page_text(root, pages, count):
    skip = {"table", "figure", "equation_isolated", "abandon", "text_mask", "table_mask", "chart_mask", "unknown_mask", "need_mask"}
    found = []
    for page in pages:
        info = page["page_info"]
        if not english(info) or not (root / OMNI / "images" / Path(info["image_path"]).name).exists():
            continue
        text = "\n".join(d.get("text", "") for d in sorted(page["layout_dets"], key=lambda d: int(d.get("order") or 0))
                         if d["category_type"] not in skip and d.get("text"))
        if len(text) >= 300:
            found.append((digest("page-v1:" + info["image_path"]), info, text))
    found.sort(key=lambda x: x[0])
    return [{"id": "page:" + h[:16], "task": "page_text", "image": f"{OMNI}/images/{Path(info['image_path']).name}",
             "source": info["page_attribute"].get("data_source"), "gold": text} for h, info, text in found[:count]]


def chartqa_members(z):
    names = z.namelist()
    prefix = next(n for n in names if n.endswith("test/test_human.json")).rsplit("test/", 1)[0]
    return prefix


def build_chart_qa(root, count):
    with zipfile.ZipFile(root / CHARTQA_ZIP) as z:
        prefix = chartqa_members(z)
        cases = []
        for split in ("human", "augmented"):
            rows = json.loads(z.read(f"{prefix}test/test_{split}.json"))
            rows = sorted(rows, key=lambda r: digest(f"chartqa-v1:{split}:{r['imgname']}:{r['query']}"))
            seen = set()
            for r in rows:
                if r["imgname"] in seen:
                    continue  # one question per chart
                seen.add(r["imgname"])
                cases.append({"id": f"chartqa:{split}:" + digest(r["imgname"] + r["query"])[:12], "task": "chart_qa", "split": split,
                              "image": f"{prefix}test/png/{r['imgname']}", "table": f"{prefix}test/tables/{Path(r['imgname']).stem}.csv",
                              "question": r["query"], "gold": str(r["label"])})
                if len([c for c in cases if c["split"] == split]) >= count // 2:
                    break
    return cases


def build_chart_table(root, count, exclude):
    with zipfile.ZipFile(root / CHARTQA_ZIP) as z:
        prefix = chartqa_members(z)
        pngs = sorted((n for n in z.namelist() if n.startswith(prefix + "test/png/") and n.endswith(".png")),
                      key=lambda n: digest("charttable-v1:" + n))
        cases = []
        for name in pngs:
            stem = Path(name).stem
            table = f"{prefix}test/tables/{stem}.csv"
            if name in exclude or table not in z.namelist():
                continue
            rows = list(csv.reader(io.StringIO(z.read(table).decode("utf-8", "replace"))))
            if 2 <= len(rows) <= 30:
                cases.append({"id": "charttable:" + digest(name)[:16], "task": "chart_table", "image": name, "gold": rows})
            if len(cases) >= count:
                break
    return cases


def build(root, force=False):
    path = root / "evaluation" / "vision_cases_v1.json"
    if path.exists() and not force:
        raise SystemExit(f"{path} already frozen; refusing to rebuild (use --force only before any results exist)")
    pages = omni_pages(root)
    cases = build_layout(root, pages, COUNTS["layout"]) + build_ocr_crop(root, pages, COUNTS["ocr_crop"]) + \
        build_table(root, pages, COUNTS["table"]) + build_page_text(root, pages, COUNTS["page_text"])
    qa = build_chart_qa(root, COUNTS["chart_qa"])
    cases += qa + build_chart_table(root, COUNTS["chart_table"], {c["image"] for c in qa})
    body = json.dumps(cases, sort_keys=True)
    manifest = {"protocol": PROTOCOL, "created": now(), "counts": Counter(c["task"] for c in cases),
                "cases_sha256": hashlib.sha256(body.encode()).hexdigest(),
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "cases": cases}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"frozen": str(path), "counts": manifest["counts"], "cases_sha256": manifest["cases_sha256"]}))


CASE_FILES = {"v1": "vision_cases_v1.json", "confirm": "vision_confirm_v1.json"}


def load_cases(root, which="v1"):
    manifest = json.loads((root / "evaluation" / CASE_FILES[which]).read_text(encoding="utf-8"))
    return manifest


def build_confirm(root):
    """Held-out confirmation cases, frozen separately and never used while choosing variants.

    Variants were chosen on the 200 ChartQA and 60 table cases in vision_cases_v1. Confirming on those same
    cases would overstate the gain (selection bias), so this set contains every ChartQA test question whose
    chart is not in v1, and every eligible English OmniDocBench table not in v1.
    """
    path = root / "evaluation" / CASE_FILES["confirm"]
    if path.exists():
        raise SystemExit(f"{path} already frozen")
    dev = load_cases(root)["cases"]
    dev_images = {c["image"] for c in dev if c["task"] in ("chart_qa", "chart_table")}
    dev_tables = {c["id"] for c in dev if c["task"] == "table"}
    cases = []
    with zipfile.ZipFile(root / CHARTQA_ZIP) as z:
        prefix = chartqa_members(z)
        for split in ("human", "augmented"):
            for r in json.loads(z.read(f"{prefix}test/test_{split}.json")):
                image = f"{prefix}test/png/{r['imgname']}"
                if image in dev_images:
                    continue
                cases.append({"id": f"cqc:{split}:" + digest(r["imgname"] + r["query"])[:12], "task": "chart_qa_confirm", "score_as": "chart_qa",
                              "split": split, "image": image, "question": r["query"], "gold": str(r["label"])})
    for c in build_table(root, omni_pages(root), 10_000):
        if c["id"] not in dev_tables:
            cases.append({**c, "id": "tc:" + c["id"].split(":", 1)[1], "task": "table_confirm", "score_as": "table"})
    seen, unique = set(), []
    for c in cases:  # ChartQA repeats a few identical question/chart pairs; keep one
        if c["id"] not in seen:
            seen.add(c["id"])
            unique.append(c)
    body = json.dumps(unique, sort_keys=True)
    manifest = {"protocol": PROTOCOL + "-confirm", "created": now(), "counts": Counter(c["task"] for c in unique),
                "cases_sha256": hashlib.sha256(body.encode()).hexdigest(), "excludes": "every chart and table used in vision_cases_v1",
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "cases": unique}
    path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"frozen": str(path), "counts": manifest["counts"], "cases_sha256": manifest["cases_sha256"]}))


# ---------- images ----------

_zip = {}


def load_image(root, case, key="image"):
    from PIL import Image
    name = case[key]
    if name.startswith(OMNI):
        image = Image.open(root / name)
    else:
        z = _zip.setdefault(CHARTQA_ZIP, zipfile.ZipFile(root / CHARTQA_ZIP))
        image = Image.open(io.BytesIO(z.read(name)))
    image = image.convert("RGB")
    if case.get("crop_box"):
        x0, y0, x1, y1 = case["crop_box"]
        image = image.crop((max(0, x0), max(0, y0), min(image.width, x1), min(image.height, y1)))
    return image


def save_eval_crop(root, case, image):
    """Keep every evaluated image as a file so the review page can show it beside each model's reading."""
    path = root / "crops" / "eval" / case["task"] / (case["id"].replace(":", "_") + ".jpg")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, "JPEG", quality=88)
    return str(path.relative_to(root))


# ---------- running one case ----------

# ---------- controlled tuning experiment ----------
# Each variant changes ONE factor against the baseline, identically for every model. Cases, temperature 0,
# schema forcing and token budgets stay fixed, so a score change is attributable to that one factor.
VARIANTS = {
    "baseline": "Settings used for the first comparison",
    "hires": "Cap raised to 2048 px on the long side instead of 1600 (no effect in practice: almost every test image is already under 1600 px, so the input did not change)",
    "upscale": "Small images enlarged so the long side is 1600 px (the resolution test that actually changes the input)",
    "tuned": "The per-task winners combined: selfcheck for chart questions, expert prompt for tables",
    "expert": "Task-specific instructions that spell out how to read the image (axes, legend, units, every row and column)",
    "selfcheck": "Structured self-check: short notes (chart questions) or a row and column count (tables) before the answer",
}
EXPERT_PROMPTS = {
    "chart_qa": ("You are reading a chart to answer one question. First locate the title, axis labels, units, legend and every "
                 "data label printed on the chart. Use printed data labels when they exist; otherwise estimate from the gridlines. "
                 "If the question asks for a difference, sum, ratio or average, compute it from the values you read. "
                 "Reply with only the final answer: a number without units or a short word or phrase, matching the chart's wording."
                 "\nQuestion: "),
    "table": ("Transcribe this table exactly. Keep the same number of rows and columns as printed. Copy every cell's text and "
              "number exactly, including signs, decimals, percent signs and footnote marks. Keep empty cells as empty strings. "
              "When a header spans several columns, repeat its text in each column it covers. Never summarise or skip rows."),
    "chart_table": ("Extract the full data table behind this chart. Always return at least one row. The first column is the category "
                    "or x value exactly as labelled; add one column per series named as in the legend (or 'value' if there is one "
                    "series). Include every category shown, in order. Use printed data labels when present; otherwise estimate from "
                    "the gridlines as precisely as possible. Put the chart title in title and the units in notes."),
}
CHART_CHECK_SCHEMA = {"type": "object", "properties": {"notes": {"type": "string", "maxLength": 400}, "answer": {"type": "string"}},
                      "required": ["notes", "answer"], "additionalProperties": False}


def table_schema_with_check():
    schema = json.loads(json.dumps(regions.TABLE_SCHEMA))
    schema["properties"] = {"row_count": {"type": "integer"}, "column_count": {"type": "integer"}, **schema["properties"]}
    schema["required"] = ["row_count", "column_count"] + schema["required"]
    return schema


TEXT_SCHEMA = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"], "additionalProperties": False}
ANSWER_SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"], "additionalProperties": False}


def run_case(root, model, case, variant="baseline"):
    task = case.get("score_as", case["task"])
    if variant == "tuned":  # the per-task winners from the v1 experiment
        variant = {"chart_qa": "selfcheck", "table": "expert"}.get(task, "baseline")
    if task == "layout":
        image = load_image(root, case)
        save_eval_crop(root, case, image)
        found = regions.detect(image, "yolo" if model == "yolo" else "vlm=" + model)
        return {"regions": found}, score_layout(case["gold"], found)
    image = load_image(root, case)
    save_eval_crop(root, case, image)
    if variant == "upscale" and max(image.size) < 1600:
        from PIL import Image as _Image
        factor = 1600 / max(image.size)
        image = image.resize((round(image.width * factor), round(image.height * factor)), _Image.LANCZOS)
    png = vlm_client.png_bytes(image, 2048 if variant == "hires" else 1600)
    if task == "ocr_crop":
        out, _ = vlm_client.chat(model, "Transcribe all text in this image exactly as printed, in reading order. Do not correct or summarise.",
                                 TEXT_SCHEMA, [png], max_tokens=1200)
        observed, expected = norm(out["text"]), case["gold"]
        return out, {"errors": edit_distance(observed, expected), "reference_chars": len(expected),
                     "numeric_expected": sum(numbers(expected).values()), "numeric_predicted": sum(numbers(observed).values()),
                     "numeric_matched": sum((numbers(expected) & numbers(observed)).values())}
    if task == "page_text":
        out, _ = vlm_client.chat(model, "Transcribe all the running text on this page in reading order: headings, paragraphs, lists, "
                                 "captions, headers and footers. Skip tables, figures and display equations.", TEXT_SCHEMA,
                                 [vlm_client.png_bytes(image, 1800)], max_tokens=6000)
        p, r, f = f1(words(case["gold"]), words(out["text"]))
        _, nr, _ = f1(numbers(case["gold"]), numbers(out["text"]))
        return out, {"word_precision": p, "word_recall": r, "word_f1": f, "numeric_recall": nr}
    if task == "table":
        prompt = EXPERT_PROMPTS["table"] if variant == "expert" else regions.READ_PROMPTS["table"]
        schema = regions.TABLE_SCHEMA
        if variant == "selfcheck":
            prompt += " First count the table's rows and columns, then transcribe it with exactly that many."
            schema = table_schema_with_check()
        out, _ = vlm_client.chat(model, prompt, schema, [png], max_tokens=6000)
        return out, score_table(case["gold"], out)
    if task == "chart_qa":
        if variant == "expert":
            out, _ = vlm_client.chat(model, EXPERT_PROMPTS["chart_qa"] + case["question"], ANSWER_SCHEMA, [png], max_tokens=300)
        elif variant == "selfcheck":
            out, _ = vlm_client.chat(model, "In notes, briefly (under 60 words) list the values you read from the chart that the question "
                                     "needs and any calculation. Then give the answer: a number without units, or a short word or phrase."
                                     "\nQuestion: " + case["question"], CHART_CHECK_SCHEMA, [png], max_tokens=600)
        else:
            out, _ = vlm_client.chat(model, "Answer the question about this chart. Reply with only the answer: a number without units, "
                                     "or a short word or phrase.\nQuestion: " + case["question"], ANSWER_SCHEMA, [png], max_tokens=300)
        return out, {"correct": relaxed_match(out["answer"], case["gold"])}
    if task == "chart_table":
        prompt = EXPERT_PROMPTS["chart_table"] if variant == "expert" else regions.READ_PROMPTS["chart"]
        schema = regions.TABLE_SCHEMA
        if variant == "selfcheck":
            prompt += " First count the categories and series, then fill the table with exactly that many rows and columns."
            schema = table_schema_with_check()
        out, _ = vlm_client.chat(model, prompt, schema, [png], max_tokens=3000)
        return out, score_chart_table(case["gold"], out)
    raise ValueError(task)


def run_table_only(root, model, case):
    """The same ChartQA question answered from the gold CSV instead of the image (the earlier diagnostic, at scale)."""
    z = _zip.setdefault(CHARTQA_ZIP, zipfile.ZipFile(root / CHARTQA_ZIP))
    table = z.read(case["table"]).decode("utf-8", "replace")
    out, _ = vlm_client.chat(model, "Answer the question using only this table extracted from a chart. Reply with only the answer: "
                             "a number without units, or a short word or phrase.\nTable (CSV):\n" + table + "\nQuestion: " + case["question"],
                             ANSWER_SCHEMA, max_tokens=300)
    return out, {"correct": relaxed_match(out["answer"], case["gold"])}


# ---------- scorers ----------

def score_layout(gold, found, threshold=0.5):
    metrics = {}
    for kind in ("figure", "table"):
        g = [x["bbox"] for x in gold if x["kind"] == kind]
        # a detected chart is a figure in OmniDocBench's labels
        p = [x["bbox"] for x in found if (kind == "table" and x["kind"] == "table") or (kind == "figure" and x["kind"] in ("figure", "chart"))]
        pairs = sorted(((regions.iou(a, b), i, j) for i, a in enumerate(g) for j, b in enumerate(p)), reverse=True)
        used_g, used_p, ious = set(), set(), []
        for value, i, j in pairs:
            if value < threshold:
                break
            if i not in used_g and j not in used_p:
                used_g.add(i), used_p.add(j), ious.append(value)
        metrics[kind] = {"gold": len(g), "predicted": len(p), "matched": len(ious), "iou_sum": sum(ious)}
    return metrics


def score_table(gold_html, out):
    gold = parse_html_table(gold_html)
    pred = grid_to_rows(out.get("header") or [], out.get("rows") or [])
    gold_cells = Counter(c[0].lower() for r in gold for c in r if c[0])
    pred_cells = Counter(c[0].lower() for r in pred for c in r if c[0])
    _, _, cell_f1 = f1(gold_cells, pred_cells)
    gold_nums = Counter(n for r in gold for c in r for n in numbers(c[0]).elements())
    pred_nums = Counter(n for r in pred for c in r for n in numbers(c[0]).elements())
    np_, nr, _ = f1(gold_nums, pred_nums)
    structure = teds([[("", rs, cs) for _, rs, cs in r] for r in gold], [[("", rs, cs) for _, rs, cs in r] for r in pred]) if pred else 0.0
    return {"teds": teds(gold, pred) if pred else 0.0, "teds_structure": structure, "cell_f1": cell_f1,
            "numeric_recall": nr, "numeric_precision": np_, "gold_rows": len(gold), "pred_rows": len(pred)}


def score_chart_table(gold_rows, out, tolerance=0.05):
    """Match every gold number to an unused predicted number within 5% relative error."""
    gold_vals = [to_number(c) for r in gold_rows[1:] for c in r[1:]]
    gold_vals = [v for v in gold_vals if v is not None]
    pred_vals = [to_number(c) for r in (out.get("rows") or []) for c in r[1:]]
    pred_vals = [v for v in pred_vals if v is not None]
    unused = list(pred_vals)
    matched = 0
    for g in gold_vals:
        best = min(unused, key=lambda p: abs(p - g), default=None)
        if best is not None and (abs(best - g) <= tolerance * abs(g) if g else best == 0):
            unused.remove(best)
            matched += 1
    gold_labels = Counter(norm(r[0]).lower() for r in gold_rows[1:] if r)
    pred_labels = Counter(norm(r[0]).lower() for r in (out.get("rows") or []) if r)
    _, label_recall, _ = f1(gold_labels, pred_labels)
    return {"gold_values": len(gold_vals), "pred_values": len(pred_vals), "matched": matched,
            "value_recall": matched / len(gold_vals) if gold_vals else None,
            "value_precision": matched / len(pred_vals) if pred_vals else None, "label_recall": label_recall}


# ---------- run and report ----------

def run(root, model, tasks, limit=None, table_only=False, variant="baseline", which="v1"):
    manifest = load_cases(root, which)
    db = connect(root)
    db.execute(RESULT_SCHEMA)
    weights = "yolo:" + "/".join(regions.YOLO_WEIGHTS) if model == "yolo" else vlm_client.model_digest(model)
    if model != "yolo" and not weights:
        raise SystemExit(f"{model} is not being served right now")
    for task in tasks:
        mode = "table_only" if table_only else "image"
        config = {"protocol": PROTOCOL, "cases_sha256": manifest["cases_sha256"], "task": task, "model": model, "weights": weights, "mode": mode}
        if variant != "baseline":
            config["variant"] = variant  # baseline keeps its original config hash, so earlier results stay valid
        run_id = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:24]
        db.execute("INSERT OR IGNORE INTO runs(id, model, started, config, status) VALUES(?,?,?,?,?)", (run_id, model, now(), json.dumps(config), "running"))
        done = {c for (c,) in db.execute("SELECT case_id FROM vision_results WHERE run_id=?", (run_id,))}
        cases = [c for c in manifest["cases"] if c["task"] == task and c["id"] not in done][:limit]
        for n, case in enumerate(cases, 1):
            started = time.perf_counter()
            try:
                prediction, metrics = run_table_only(root, model, case) if table_only else run_case(root, model, case, variant)
                status, error = "complete", None
            except Exception as exc:  # failures stay in the denominator
                prediction, metrics, status, error = None, None, "failed", f"{type(exc).__name__}: {exc}"[:500]
            db.execute("INSERT OR REPLACE INTO vision_results VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (run_id, case["id"], task, model + ("" if mode == "image" else " [table only]") + ("" if variant == "baseline" else f" [{variant}]"), status,
                        json.dumps(prediction), json.dumps(metrics), time.perf_counter() - started, error, now()))
            db.commit()
            if n % 10 == 0 or n == len(cases):
                print(json.dumps({"model": model, "task": task, "mode": mode, "done": n, "of": len(cases)}), flush=True)
        db.execute("UPDATE runs SET status='complete' WHERE id=?", (run_id,))
        db.commit()


def aggregate(task, rows):
    """rows: list of (status, metrics, seconds). Failed cases count as zero."""
    n = len(rows)
    ok = [(m, s) for st, m, s in rows if st == "complete" and m]
    out = {"cases": n, "failed": n - len(ok), "median_seconds": round(statistics.median(s for _, s in ok), 2) if ok else None}
    if task == "layout":
        for kind in ("figure", "table"):
            g = sum(m[kind]["gold"] for m, _ in ok)
            p = sum(m[kind]["predicted"] for m, _ in ok)
            hit = sum(m[kind]["matched"] for m, _ in ok)
            pr, rc = (hit / p if p else None), (hit / g if g else None)
            out[kind] = {"precision": pr, "recall": rc, "f1": 2 * pr * rc / (pr + rc) if pr and rc else 0.0,
                         "mean_iou": sum(m[kind]["iou_sum"] for m, _ in ok) / hit if hit else None, "gold": g}
    elif task == "ocr_crop":
        errors = sum(m["errors"] for m, _ in ok)
        out["cer_completed"] = errors / max(1, sum(m["reference_chars"] for m, _ in ok))
        ne, np_, nm = (sum(m[k] for m, _ in ok) for k in ("numeric_expected", "numeric_predicted", "numeric_matched"))
        out["numeric_recall"] = nm / ne if ne else None
        out["numeric_precision"] = nm / np_ if np_ else None
    else:
        keys = {"table": ("teds", "teds_structure", "cell_f1", "numeric_recall"), "page_text": ("word_f1", "numeric_recall"),
                "chart_qa": ("correct",), "chart_table": ("value_recall", "value_precision", "label_recall")}[task.replace("_confirm", "")]
        for k in keys:
            values = [float(m.get(k) or 0) for m, _ in ok] + [0.0] * (n - len(ok))
            out[k] = sum(values) / n if n else None
    return out


def report(root):
    db = connect(root)
    db.execute(RESULT_SCHEMA)
    groups = {}
    for run_id, task, model, status, metrics, seconds in db.execute("SELECT run_id, task, model, status, metrics, seconds FROM vision_results"):
        groups.setdefault((task, model), []).append((status, json.loads(metrics) if metrics else None, seconds))
    summary = [{"task": t, "model": m, **aggregate(t, rows)} for (t, m), rows in sorted(groups.items())]
    split_of = {c["id"]: c.get("split") for c in load_cases(root)["cases"] if c["task"] == "chart_qa"}
    if (root / "evaluation" / CASE_FILES["confirm"]).exists():
        split_of.update({c["id"]: c.get("split") for c in load_cases(root, "confirm")["cases"] if c["task"] == "chart_qa_confirm"})
    for r in summary:
        if r["task"] in ("chart_qa", "chart_qa_confirm"):
            rows = db.execute("SELECT case_id, status, metrics FROM vision_results WHERE task=? AND model=?", (r["task"], r["model"])).fetchall()
            for split in ("human", "augmented"):
                chosen = [json.loads(m or "null") for c, s, m in rows if split_of.get(c) == split]
                r["correct_" + split] = sum(bool(m and m.get("correct")) for m in chosen) / len(chosen) if chosen else None
    out = root / "reports" / "vision-evaluation-summary.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"protocol": PROTOCOL, "created": now(), "results": summary}, indent=1), encoding="utf-8")
    for r in summary:
        print(json.dumps(r))
    print(out)


PRIMARY = {"chart_qa": "correct", "chart_table": "value_recall", "table": "teds", "chart_qa_confirm": "correct", "table_confirm": "teds"}


def compare(root, draws=2000, seed=20261019):
    """Paired comparison: the same cases under baseline and under each variant, per model and task.

    Reports mean change, cases that got better or worse, and a 95% paired bootstrap interval. A failed
    case scores 0. Temperature is 0, so a repeated run gives the same answers; case-level resampling is
    what measures uncertainty here.
    """
    import random
    db = connect(root)
    scores = {}
    for model, task, case, status, metrics in db.execute("SELECT model, task, case_id, status, metrics FROM vision_results"):
        if task not in PRIMARY or "[table only]" in model:
            continue
        base, _, rest = model.partition(" [")
        variant = rest.rstrip("]") or "baseline"
        m = json.loads(metrics) if metrics else None
        scores.setdefault((base, task, variant), {})[case] = float((m or {}).get(PRIMARY[task]) or 0) if status == "complete" else 0.0
    rng = random.Random(seed)
    out = []
    for (model, task, variant), cases in sorted(scores.items()):
        if variant == "baseline" or (model, task, "baseline") not in scores:
            continue
        base = scores[(model, task, "baseline")]
        shared = sorted(set(base) & set(cases))
        diffs = [cases[c] - base[c] for c in shared]
        if not diffs:
            continue
        boot = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(draws))
        row = {"model": model, "task": task, "variant": variant, "metric": PRIMARY[task], "cases": len(diffs),
               "baseline": round(sum(base[c] for c in shared) / len(shared), 4), "variant_score": round(sum(cases[c] for c in shared) / len(shared), 4),
               "change": round(sum(diffs) / len(diffs), 4), "ci95": [round(boot[int(.025 * draws)], 4), round(boot[int(.975 * draws)], 4)],
               "better": sum(d > 1e-9 for d in diffs), "worse": sum(d < -1e-9 for d in diffs)}
        row["verdict"] = "better" if row["ci95"][0] > 0 else "worse" if row["ci95"][1] < 0 else "no clear change"
        if task.startswith("chart_qa"):  # right/wrong per case: exact McNemar test on the discordant cases
            k, n = min(row["better"], row["worse"]), row["better"] + row["worse"]
            row["p_value"] = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
            row["test"] = "exact McNemar"
        else:  # continuous score: two-sided paired bootstrap p-value
            row["p_value"] = min(1.0, 2 * min(sum(x <= 0 for x in boot), sum(x >= 0 for x in boot)) / draws)
            row["test"] = "paired bootstrap"
        out.append(row)
    # Holm correction: many model x task x variant comparisons were made, so some would look significant by chance
    order = sorted(range(len(out)), key=lambda i: out[i]["p_value"])
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(out) - rank) * out[i]["p_value"]))
        out[i]["p_holm"] = round(running, 4)
        out[i]["p_value"] = round(out[i]["p_value"], 4)
        out[i]["verdict_after_correction"] = ("better" if out[i]["change"] > 0 else "worse") if running < 0.05 else "not significant"
    for row in out:
        print(json.dumps(row))
    path = root / "reports" / "vision-variant-comparison.json"
    path.write_text(json.dumps({"protocol": PROTOCOL, "variants": VARIANTS, "created": now(), "results": out}, indent=1), encoding="utf-8")
    print(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--force", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("--model", required=True, help="ollama:<name>, openai:<name>, or yolo (layout only)")
    r.add_argument("--task", action="append", choices=TASKS + ("chart_qa_confirm", "table_confirm"))
    r.add_argument("--limit", type=int)
    r.add_argument("--table-only", action="store_true", help="chart_qa from the gold CSV instead of the image")
    r.add_argument("--variant", default="baseline", choices=sorted(VARIANTS))
    r.add_argument("--cases", default="v1", choices=sorted(CASE_FILES), help="v1 (development) or confirm (held out)")
    sub.add_parser("build-confirm", help="freeze the held-out confirmation cases")
    sub.add_parser("report")
    sub.add_parser("compare", help="each variant against baseline on the same cases, with paired bootstrap intervals")
    args = parser.parse_args()
    if args.command == "build":
        build(args.root, args.force)
    elif args.command == "run":
        tasks = tuple(args.task or (("layout",) if args.model == "yolo" else TASKS))
        run(args.root, args.model, tasks, args.limit, args.table_only, args.variant, args.cases)
    elif args.command == "build-confirm":
        build_confirm(args.root)
    elif args.command == "compare":
        compare(args.root)
    else:
        report(args.root)


if __name__ == "__main__":
    main()
