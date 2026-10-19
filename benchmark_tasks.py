"""Stage-specific baselines and dataset coverage; never substitute storage for evaluation."""
import argparse
from collections import Counter
import csv
import io
import json
import re
from pathlib import Path
import statistics
import time
import unicodedata
import zipfile
from document_lab import DEFAULT_ROOT, connect, digest, now, tokens, tesseract_read

def output(root, name, result):
    directory = root / "reports"
    directory.mkdir(exist_ok=True)
    (directory / (name + ".json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2), flush=True)

def retrieval(root):
    from rank_bm25 import BM25Okapi
    path = root / "datasets/acord/raw/ACORD Dataset & ReadMe.zip"
    with zipfile.ZipFile(path) as z:
        def member(suffix):
            return z.read(next(n for n in z.namelist() if n.endswith(suffix))).decode("utf-8")
        corpus = [json.loads(line) for line in member("corpus.jsonl").splitlines()]
        queries = {q["_id"]: q for q in map(json.loads, member("queries.jsonl").splitlines())}
        qrels = list(csv.DictReader(io.StringIO(member("qrels/test.tsv")), delimiter="\t"))
    labels = {}
    for row in qrels:
        labels.setdefault(row["query-id"], {})[row["corpus-id"]] = int(row["score"])
    engine = BM25Okapi([tokens(c["text"]) for c in corpus])
    ids = [c["_id"] for c in corpus]
    cases = []
    for query_id, relevance in sorted(labels.items()):
        start = time.perf_counter()
        scores = engine.get_scores(tokens(queries[query_id]["text"]))
        ranked = sorted(range(len(ids)), key=lambda i: (-scores[i], ids[i]))[:20]
        positives = {key for key, score in relevance.items() if score >= 4}
        relevant = [ids[i] in positives for i in ranked]
        cases.append({"query_id": query_id, "positive_labels": len(positives), "recall_at_20": sum(relevant) / len(positives) if positives else None, "hit_at_20": any(relevant) if positives else None, "reciprocal_rank_at_20": next((1 / (i + 1) for i, v in enumerate(relevant) if v), 0.0) if positives else None, "seconds": time.perf_counter() - start, "top_ids": [ids[i] for i in ranked]})
    scored = [c for c in cases if c["recall_at_20"] is not None]
    result = {"stage": "retrieval", "dataset": "acord", "baseline": "BM25Okapi-defaults", "split": "official_test_qrels", "corpus_clauses": len(corpus), "queries": len(cases), "scored_queries": len(scored), "positive_definition": "rating >=4; other ratings are not counted relevant for this local diagnostic", "mean_recall_at_20": statistics.mean(c["recall_at_20"] for c in scored), "hit_at_20": statistics.mean(c["hit_at_20"] for c in scored), "mrr_at_20": statistics.mean(c["reciprocal_rank_at_20"] for c in scored), "gate": "baseline_only_not_promoted", "cases": cases, "created_at": now()}
    output(root, "retrieval-baseline", result)

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

def norm(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())

def ocr_benchmark(root, count, directml, provider="tesseract"):
    import numpy as np
    from PIL import Image
    from rapidocr_onnxruntime import RapidOCR
    data = root / "datasets/omnidocbench/raw"
    pages = json.loads((data / "OmniDocBench.json").read_text(encoding="utf-8"))
    candidates = []
    for page in pages:
        info = page["page_info"]
        # Choose human-annotated English prose without inline LaTeX. This is a
        # cropped-text diagnostic, not the official end-to-end OmniDocBench score.
        for block in page["layout_dets"]:
            text = block.get("text", "")
            if block.get("ignore") or block["category_type"] != "text_block" or not 80 <= len(text) <= 700 or "$" in text or "\\" in text:
                continue
            ascii_letters = sum(c.isascii() and c.isalpha() for c in text)
            letters = sum(c.isalpha() for c in text)
            if ascii_letters / max(1, letters) < .98:
                continue
            image = data / "images" / Path(info["image_path"]).name
            if image.exists():
                candidates.append((digest(str(info["image_path"]) + str(block["anno_id"])), image, block))
    # At most one block per source page, deterministic seeded ordering.
    chosen, seen = [], set()
    for _, image, block in sorted(candidates):
        if image.name not in seen:
            chosen.append((image, block)); seen.add(image.name)
        if len(chosen) >= count:
            break
    engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1, det_use_dml=directml, cls_use_dml=directml, rec_use_dml=directml) if provider == "rapidocr" else None
    directory = root / "reports"
    directory.mkdir(exist_ok=True)
    cache = directory / ("ocr-block-events-" + provider + ("-dml" if directml else "-cpu") + ".jsonl")
    previous = {}
    if cache.exists():
        for line in cache.read_text().splitlines():
            row = json.loads(line); previous[row["id"]] = row
    cases = []
    for image, block in chosen:
        identifier = digest(image.name + str(block["anno_id"]))
        if identifier in previous:
            cases.append(previous[identifier]); continue
        start = time.perf_counter()
        try:
            with Image.open(image) as pic:
                poly = block["poly"]
                box = (max(0, int(min(poly[::2])) - 4), max(0, int(min(poly[1::2])) - 4), min(pic.width, int(max(poly[::2])) + 5), min(pic.height, int(max(poly[1::2])) + 5))
                crop = np.asarray(pic.convert("RGB").crop(box))
            if provider == "tesseract":
                read = " ".join(line["text"] for line in tesseract_read(Image.fromarray(crop), root, psm=6))
            else:
                output_lines, _ = engine(crop)
                read = " ".join(line[1] for line in (output_lines or []))
            expected = norm(block["text"])
            observed = norm(read)
            errors = edit_distance(observed, expected)
            status, error = "complete", None
        except Exception as exc:
            expected, observed, errors, status, error = norm(block["text"]), "", len(norm(block["text"])), "failed", str(exc)
        row = {"id": identifier, "source_image": image.name, "block_id": block["anno_id"], "expected": expected, "observed": observed, "errors": errors, "reference_chars": len(expected), "seconds": time.perf_counter() - start, "status": status, "error": error}
        with cache.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")
        cases.append(row)
        print(json.dumps({"ocr_block": len(cases), "total": len(chosen), "seconds": round(row["seconds"], 3)}), flush=True)
    numbers = lambda text: Counter(re.findall(r"(?<!\w)\d+(?:[.,]\d+)*(?:%)?", text))
    numeric_expected = sum(sum(numbers(c["expected"]).values()) for c in cases)
    numeric_predicted = sum(sum(numbers(c["observed"]).values()) for c in cases)
    numeric_matched = sum(sum((numbers(c["expected"]) & numbers(c["observed"])).values()) for c in cases)
    result = {"stage": "cropped_text_ocr", "dataset": "omnidocbench", "baseline": "tesseract-5.5.0-eng-fast-4.1.0-psm6" if provider == "tesseract" else "rapidocr_onnxruntime-1.4.4-" + ("directml" if directml else "cpu"), "selection": "deterministic ASCII-prose text blocks, 1 per page; no LaTeX; diagnostic subset", "pages": len(cases), "cer": sum(c["errors"] for c in cases) / max(1, sum(c["reference_chars"] for c in cases)), "numeric_reference_count": numeric_expected, "numeric_token_recall": numeric_matched / numeric_expected if numeric_expected else None, "numeric_token_precision": numeric_matched / numeric_predicted if numeric_predicted else None, "failures": sum(c["status"] != "complete" for c in cases), "median_seconds": statistics.median(c["seconds"] for c in cases) if cases else None, "gate": "diagnostic_only_not_full_page_fidelity", "cases": cases, "created_at": now()}
    output(root, "ocr-baseline", result)

def coverage(root):
    plan = json.loads((root / "datasets/download-plan.json").read_text())
    rows = []
    for dataset in plan["datasets"]:
        key = dataset["id"]
        raw = root / "datasets" / key / "raw"
        files = [f for f in raw.rglob("*") if f.is_file() and not f.name.endswith(".part")]
        state = "downloaded_not_scored"
        if key in ["cuad", "contractnli"]: state = "text_tasks_scored_see_runs"
        if key == "acord": state = "lexical_retrieval_baseline"
        if key == "omnidocbench": state = "cropped_ocr_diagnostic_full_layout_not_scored"
        if key in ["chartqa", "chartqapro"]: state = "blocked_no_installed_vision_model"
        if key in ["pubtables1m", "fintabnet", "doclaynet"]: state = "blocked_no_structure_or_layout_adapter"
        if key == "niaid": state = "unlabeled_educational_use_only_not_scored"
        rows.append({"dataset": key, "present_files": len(files), "bytes": sum(f.stat().st_size for f in files), "evaluation_status": state, "coverage": dataset["coverage"]})
    policy = json.loads(Path(__file__).with_name("quality_gates.json").read_text())["stage_policies"]
    stage_gates = []
    for stage, filename in [("ocr", "ocr-baseline"), ("retrieval", "retrieval-baseline")]:
        path = root / "reports" / (filename + ".json")
        if not path.exists():
            stage_gates.append({"stage": stage, "status": "not_tested", "reasons": ["No scored baseline"]}); continue
        report = json.loads(path.read_text(encoding="utf-8")); rules=policy[stage]; reasons=[]
        if stage == "ocr":
            if report["pages"] < rules["min_pages"]: reasons.append("Too few source pages")
            if report["cer"] > rules["max_cer"]: reasons.append("Character error rate above threshold")
            for metric in ["numeric_token_recall", "numeric_token_precision"]:
                if report.get(metric) is None or report[metric] < rules["min_"+metric]: reasons.append(metric+" below threshold or unmeasured")
            reasons.append("Full-page institutional OCR holdout still required")
        else:
            if report["scored_queries"] < rules["min_scored_queries"]: reasons.append("Too few scored positive-reference queries")
            if report["mean_recall_at_20"] < rules["min_recall_at_20"]: reasons.append("Recall at 20 below threshold")
            if report["hit_at_20"] < rules["min_hit_at_20"]: reasons.append("Hit rate at 20 below threshold")
        stage_gates.append({"stage": stage, "status": "failed" if reasons else "requires_holdout_review", "reasons": reasons, "thresholds": rules, "measurements": {k:v for k,v in report.items() if k not in ["cases", "created_at"]}})
    stage_gates += [{"stage": "chart_qa", "status": "not_tested", "reasons": ["No installed vision-language model adapter"]}, {"stage": "table_structure", "status": "not_tested", "reasons": ["No table-structure adapter evaluated"]}, {"stage": "classification", "status": "not_tested", "reasons": ["No task-specific labeled classifier evaluation"]}]
    additional = root / "reports/additional-task-summary.json"
    output(root, "task-coverage", {"created_at": now(), "datasets": rows, "stage_gates": stage_gates, "additional_tasks": json.loads(additional.read_text(encoding="utf-8")) if additional.exists() else None, "note": "A stored dataset is not an evaluated task. Unsupported modalities cannot pass a gate."})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("task", choices=["retrieval", "ocr", "coverage"])
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--directml", action="store_true")
    parser.add_argument("--engine", choices=["tesseract", "rapidocr"], default="tesseract")
    args = parser.parse_args()
    if args.task == "retrieval": retrieval(args.root)
    elif args.task == "ocr": ocr_benchmark(args.root, args.count, args.directml, args.engine)
    else: coverage(args.root)
