"""Round-2 addendum to the vision-v1 contract (docs/handoff/CODEX_HANDOFF_ADDENDUM_R2.md).

The v1 contract (tools/eval_contract.py, tools/contract.json, tools/golden_scores.json) is unchanged and still governs every
v1 row. This module fingerprints only what round 2 added, the same behavioural way:

  requests   vision_eval.run_case() driven with a recording stand-in model for the round-2 variants on the round-2 tasks:
             chart_qa x baseline/selfcheck/upscale (the vote3 members) and readfirst, page_text x baseline/layoutmask.
             layoutmask is driven with a fixed, fabricated set of layout boxes (one per DocLayout-YOLO class), and the exact
             pixels sent to the model are hashed, so which classes are painted white is part of the contract.
  layout     the yolo_all() code (formatting-free AST hash) and MASK_LABELS.
  vote       vision_eval.vote() run on a temporary database of fabricated member answers -> the chosen answer, pick and
             agreement for each case (majority under the 5% rule, ties to selfcheck).
  scoring    the page_text and chart_qa metrics run_case returns for fixed stand-in answers.
  stats      vision_eval.compare() on a fabricated round-2 table -> families exploratory_v2 / confirmatory_v2 / supporting_v2,
             with the pre-registered pick from docs/research/vision-eval/improvements/selection.json.
  cases      the frozen v2 manifest (eval_contract.FROZEN["v2"]).

Variant status (aligned with docs/research/ocr-round2-adoption-review.md) is recorded in tools/contract_r2.json and printed by
check_conformance.py --round2; it labels results, it does not change them. No model is called and no real document is read.

  python tools/eval_contract_r2.py            # print the round-2 fingerprints (JSON)
  python tools/eval_contract_r2.py --detail   # also print every recorded request
"""
import argparse
import ast
import contextlib
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import eval_contract  # noqa: E402

PROTOCOL_R2 = "vision-v1-r2"
STATUS = {
    "vote3": "confirmed: the pre-selected confirmatory test on chart_qa_confirm2 (Holm-corrected); higher-cost option",
    "selfcheck": "supporting comparison on chart_qa_confirm2, not confirmatory; the cheaper chart candidate",
    "upscale": "vote3 member; supporting comparison only",
    "layoutmask": "experimental: word F1 rose but numeric recall fell 87.2% -> 69.4%; not for budgets, contracts or other number-critical text",
    "readfirst": "dropped on development data (interval crossed zero); kept for reproducibility only",
}
R2_REQUESTS = {"chart_qa": ("baseline", "selfcheck", "upscale", "readfirst"), "page_text": ("baseline", "layoutmask")}
PROBE_SIZES = {"small": (420, 300), "large": (2400, 1700)}
# one fabricated box per DocLayout-YOLO class, as fractions of the page; only MASK_LABELS should be painted
FAKE_BOXES = [("title", (0.10, 0.03, 0.90, 0.08)), ("plain text", (0.10, 0.10, 0.90, 0.30)), ("figure", (0.10, 0.32, 0.50, 0.50)),
              ("figure_caption", (0.10, 0.51, 0.50, 0.54)), ("table", (0.52, 0.32, 0.90, 0.50)), ("table_caption", (0.52, 0.51, 0.90, 0.54)),
              ("isolate_formula", (0.20, 0.56, 0.80, 0.62)), ("formula_caption", (0.82, 0.57, 0.90, 0.61)), ("abandon", (0.10, 0.94, 0.90, 0.98))]
STAND_IN = {"text": "Section 2 reports 12.5% growth in 2024 across 3 regions", "answer": "12", "notes": "fabricated"}


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _png_size(data: bytes):
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def _pixels(data: bytes) -> str:
    """Hash of the decoded RGB pixels, so PNG encoder differences (zlib builds) cannot cause a false mismatch."""
    from PIL import Image
    return hashlib.sha256(Image.open(io.BytesIO(data)).convert("RGB").tobytes()).hexdigest()


def _answer(schema):
    if not schema:
        return ""
    props = schema.get("properties", {})
    if "header" in props or "rows" in props:  # readfirst's table step
        return {"header": ["x", "y"], "rows": [["a", "12"]], **({"notes": "fabricated"} if "notes" in props else {})}
    return {k: STAND_IN.get(k, "") for k in props if k in schema.get("required", props)}


def recorded_requests(repo: Path = REPO) -> dict:
    import vision_eval as ve
    import vlm_client
    import regions
    from PIL import Image

    calls, current = [], {}
    real = (vlm_client.chat, ve.load_image, ve.save_eval_crop, regions.yolo_all)

    def fake_chat(spec, prompt, schema=None, images=(), max_tokens=1200, timeout=600, think=False):
        calls.append({"prompt": prompt, "schema": schema, "max_tokens": max_tokens, "think": think,
                      "images": [{"size": list(_png_size(b)), "pixels_sha256": _pixels(b)} for b in images]})
        return _answer(schema), {"seconds": 0.0}

    def fake_yolo_all(image, conf=None):
        w, h = image.size
        return [{"label": lab, "bbox": [round(x0 * w, 1), round(y0 * h, 1), round(x1 * w, 1), round(y1 * h, 1)], "score": 0.9}
                for lab, (x0, y0, x1, y1) in FAKE_BOXES]

    def page(size):  # a grey page so painted-white boxes change the pixels
        return Image.new("RGB", size, (200, 200, 200))

    vlm_client.chat, regions.yolo_all = fake_chat, fake_yolo_all
    ve.load_image = lambda root, case, key="image": page(current["size"])
    ve.save_eval_crop = lambda root, case, image: ""
    cases = {"chart_qa": {"id": "probe", "task": "chart_qa_confirm2", "score_as": "chart_qa", "question": "What is the highest value?", "gold": "12"},
             "page_text": {"id": "probe", "task": "page_text_confirm2", "score_as": "page_text", "gold": "Section 2 reports 12.5% growth in 2024"}}
    out = {}
    try:
        for task, variants in R2_REQUESTS.items():
            for variant in variants:
                for size_name, size in PROBE_SIZES.items():
                    calls.clear()
                    current["size"] = size
                    prediction, metrics = ve.run_case(None, "openai:contract-probe", cases[task], variant)
                    out[f"{task}/{variant}/{size_name}"] = {"requests": list(calls), "prediction": prediction, "metrics": metrics}
    finally:
        vlm_client.chat, ve.load_image, ve.save_eval_crop, regions.yolo_all = real
    return json.loads(json.dumps(out))


def layout_hash(repo: Path = REPO) -> str:
    import vision_eval as ve
    tree = ast.parse((repo / "regions.py").read_text(encoding="utf-8"))
    keep = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "yolo_all"]
    for n in keep:
        if isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            n.body = n.body[1:]
    return _sha({"yolo_all": [ast.dump(n, include_attributes=False) for n in keep], "mask_labels": list(ve.MASK_LABELS)})


# ---------------------------------------------------------------- vote3 on fabricated member answers

VOTE_CASES = [  # (gold, baseline, selfcheck, upscale)
    ("12", "12", "12", "13"),        # baseline+selfcheck agree (13 is >5% off) -> tie between them -> selfcheck
    ("12", "11", "12", "13"),        # all differ -> tie -> selfcheck
    ("100", "100", "102", "99"),     # 5% rule: all three within 5% of each other
    ("yes", "no", "No", "yes"),      # "no"/"No" agree case-insensitively -> chosen although wrong
    ("7", None, "8", "7"),           # one member failed; 8 vs 7 is >5% apart -> 1-1 tie -> selfcheck
    ("3", None, None, None),         # nobody answered -> failed
    ("40", "40", "41", None),        # 40 and 41 agree under the 5% rule -> tie -> selfcheck
]


def run_vote():
    import vision_eval as ve
    import vlm_client
    real_digest = vlm_client.model_digest
    vlm_client.model_digest = lambda spec: "contract-probe"
    try:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            root = Path(d)
            cases = [{"id": f"v{i}", "task": "chart_qa_confirm2", "score_as": "chart_qa", "gold": g} for i, (g, *_r) in enumerate(VOTE_CASES)]
            (root / "evaluation").mkdir()
            (root / "evaluation" / ve.CASE_FILES["v2"]).write_text(json.dumps({"cases_sha256": "fabricated", "cases": cases}), encoding="utf-8")
            db = ve.connect(root)
            db.execute(ve.RESULT_SCHEMA)
            for vi, v in enumerate(ve.VOTE_MEMBERS):
                label = "m" if v == "baseline" else f"m [{v}]"
                for i, row in enumerate(VOTE_CASES):
                    ans = row[1 + vi]
                    db.execute("INSERT INTO vision_results VALUES(?,?,?,?,?,?,?,?,?,?)",
                               (f"r{v}", f"v{i}", "chart_qa_confirm2", label, "complete" if ans is not None else "failed",
                                json.dumps({"answer": ans}) if ans is not None else None, None, 1.0, None, "fixed"))
            db.commit()
            with contextlib.redirect_stdout(io.StringIO()):
                ve.vote(root, "m", "chart_qa_confirm2")
            got = db.execute("SELECT case_id, status, prediction, metrics FROM vision_results WHERE model='m [vote3]' ORDER BY case_id").fetchall()
            db.close()
    finally:
        vlm_client.model_digest = real_digest
    return [{"case": c, "status": s, "answer": (json.loads(p) or {}).get("answer") if p else None, "metrics": json.loads(m) if m else None}
            for c, s, p, m in got]


# ---------------------------------------------------------------- round-2 statistics on a fabricated table

def run_stats():
    import random
    import vision_eval as ve
    rng = random.Random(11)
    rows = []
    for i in range(30):  # development family
        b = rng.random() < 0.6
        rows.append(("m", "chart_qa_dev2", f"d{i}", "baseline", {"correct": b}))
        rows.append(("m", "chart_qa_dev2", f"d{i}", "selfcheck", {"correct": b or rng.random() < 0.25}))
    for i in range(40):  # confirmation: the pre-registered pick plus supporting rows
        b = rng.random() < 0.6
        rows.append(("m", "chart_qa_confirm2", f"c{i}", "baseline", {"correct": b}))
        rows.append(("m", "chart_qa_confirm2", f"c{i}", "vote3", {"correct": b or rng.random() < 0.3}))
        rows.append(("m", "chart_qa_confirm2", f"c{i}", "selfcheck", {"correct": b or rng.random() < 0.28}))
    for i in range(20):  # page text, continuous word F1
        b = round(rng.uniform(0.5, 0.95), 3)
        rows.append(("m", "page_text_confirm2", f"p{i}", "baseline", {"word_f1": b}))
        rows.append(("m", "page_text_confirm2", f"p{i}", "layoutmask", {"word_f1": min(1.0, round(b + rng.uniform(-0.08, 0.12), 3))}))
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        root = Path(d)
        db = ve.connect(root)
        db.execute(ve.RESULT_SCHEMA)
        for model, task, case, variant, metrics in rows:
            label = model + ("" if variant == "baseline" else f" [{variant}]")
            db.execute("INSERT INTO vision_results VALUES(?,?,?,?,?,?,?,?,?,?)",
                       (label + task, case, task, label, "complete", "null", json.dumps(metrics), 1.0, None, "fixed"))
        db.commit()
        db.close()
        (root / "reports").mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            ve.compare(root)
        result = json.loads((root / "reports" / "vision-variant-comparison.json").read_text(encoding="utf-8"))["results"]
    keep = ("model", "task", "variant", "cases", "baseline", "variant_score", "change", "ci95", "better", "worse",
            "test", "p_value", "family", "p_holm", "verdict_after_correction")
    return [{k: r.get(k) for k in keep} for r in result]


def fingerprints(repo: Path = REPO) -> dict:
    sel = repo / "docs/research/vision-eval/improvements/selection.json"
    out = {"protocol": PROTOCOL_R2, "base_method_sha256": eval_contract.fingerprints(repo)["method_sha256"],
           "requests_sha256": _sha(recorded_requests(repo)), "layout_sha256": layout_hash(repo),
           "vote_sha256": _sha(run_vote()), "stats_sha256": _sha(run_stats()),
           "selection_sha256": _sha(json.loads(sel.read_text(encoding="utf-8"))) if sel.exists() else None,
           "cases_v2_sha256": eval_contract.FROZEN["v2"]["cases_sha256"]}
    out["method_sha256"] = _sha({k: v for k, v in out.items()})
    return out


def freeze(repo: Path = REPO):
    """Maintainers only: write tools/contract_r2.json and tools/golden_r2.json from the current code."""
    (repo / "tools" / "golden_r2.json").write_text(json.dumps({"requests": recorded_requests(repo), "vote": run_vote(), "stats": run_stats()},
                                                             indent=1, ensure_ascii=False), encoding="utf-8")
    (repo / "tools" / "contract_r2.json").write_text(json.dumps({**fingerprints(repo), "status": STATUS,
                                                               "frozen_case_set": eval_contract.FROZEN["v2"]}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--detail", action="store_true")
    ap.add_argument("--freeze", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.freeze:
        freeze()
        print("wrote tools/contract_r2.json and tools/golden_r2.json")
        sys.exit(0)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if a.detail:
        print(json.dumps({"requests": recorded_requests(), "vote": run_vote(), "stats": run_stats()}, indent=1, ensure_ascii=False))
    print(json.dumps(fingerprints(), indent=1))
