"""The evaluation contract shared by the desktop (operator-orchestrated) and laptop (Codex) runs of vision-v1.

Two machines can only be compared if they ran the same cases, sent the models the same requests and scored
the answers the same way. The fingerprints here are behavioural, not textual:

  requests  For every v1 task x variant, vision_eval.run_case() is driven with a synthetic blank image (small
            and large) and a recording stand-in for vlm_client.chat. What is recorded is exactly what a model
            would receive: prompt text, JSON schema, output-token budget, image pixel size, thinking flag.
            Adding a new variant or a new task does not change it; changing any v1 prompt, budget or image cap does.
  client    The system prompt and the request payload settings in vlm_client.chat (temperature 0, num_ctx,
            schema forcing, truncation handling), as a formatting-free AST hash of chat().
  scorers   The outputs of every scorer and of the statistics code on the fixed golden inputs in
            tools/check_conformance.py. Any implementation that produces the same numbers agrees.
  cases     The frozen manifests' cases_sha256 (FROZEN below).

No model is called and no real document or image is read.

  python tools/eval_contract.py            # print the fingerprints (JSON)
  python tools/eval_contract.py --detail   # also print every recorded request
"""
import argparse
import ast
import hashlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROTOCOL = "vision-v1"

# cases_sha256 = sha256(json.dumps(manifest["cases"], sort_keys=True)), as vision_eval computes it (whitespace-free).
FROZEN = {
    "v1": {"file": "evaluation/vision_cases_v1.json", "protocol": "vision-v1", "required": True,
           "cases_sha256": "d92bcbc12d72600f36bd981080b4080c30d793efb0fd39b6ea2cd00fcdf4d6f7",
           "counts": {"layout": 120, "ocr_crop": 50, "table": 60, "page_text": 40, "chart_qa": 200, "chart_table": 60}},
    "confirm": {"file": "evaluation/vision_confirm_v1.json", "protocol": "vision-v1-confirm", "required": True,
                "cases_sha256": "a8e2b349e391506ca6b0cd231fed71a2108c22c16a9af487cd2e177fc0b22702",
                "counts": {"chart_qa_confirm": 2022, "table_confirm": 159}},
    # Round 2 (docs/research/vision-eval/improvements/PLAN.md): cases frozen 20 Oct 2026 15:35 UTC before any round-2 run.
    # Its variants are still being decided on the desktop, so round 2 is optional here and not part of method_sha256.
    "v2": {"file": "evaluation/vision_cases_v2.json", "protocol": "vision-v1-v2", "required": False,
           "cases_sha256": "0615583a6cfe12856ad6aa8cc1f5125b7306a53a4156ce2f439392a1de41a729",
           "counts": {"chart_qa_dev2": 586, "chart_qa_confirm2": 1322, "page_text_confirm2": 80}},
}

V1_TASKS = ("ocr_crop", "page_text", "table", "chart_qa", "chart_table", "layout")
V1_VARIANTS = ("baseline", "hires", "upscale", "expert", "selfcheck", "tuned")
PROBE_SIZES = {"small": (420, 300), "large": (2400, 1700)}  # below and above the 1600 px cap


def _png_size(data: bytes):
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def _dummy(schema):
    t = schema.get("type")
    if t == "object":
        return {k: _dummy(v) for k, v in schema.get("properties", {}).items() if k in schema.get("required", [])}
    return {"string": "", "array": [], "integer": 0, "number": 0}.get(t)


def recorded_requests(repo: Path = REPO) -> dict:
    """{'task/variant/size': [request, ...]} recorded from run_case with a stand-in model."""
    sys.path.insert(0, str(repo))
    import vision_eval as ve
    import vlm_client
    from PIL import Image

    calls, real_chat, real_load, real_save = [], vlm_client.chat, ve.load_image, ve.save_eval_crop
    current = {}

    def fake_chat(spec, prompt, schema=None, images=(), max_tokens=1200, timeout=600, think=False):
        calls.append({"prompt": prompt, "schema": schema, "max_tokens": max_tokens, "think": think,
                      "images": [list(_png_size(b)) for b in images]})
        return (_dummy(schema) if schema else ""), {"seconds": 0.0}

    vlm_client.chat = fake_chat
    ve.load_image = lambda root, case, key="image": Image.new("RGB", current["size"], "white")
    ve.save_eval_crop = lambda root, case, image: ""
    gold_table = "<table><tr><td>a</td><td>1</td></tr><tr><td>b</td><td>2</td></tr></table>"
    cases = {"ocr_crop": {"id": "probe", "task": "ocr_crop", "gold": "abc 12"},
             "page_text": {"id": "probe", "task": "page_text", "gold": "abc 12"},
             "table": {"id": "probe", "task": "table", "gold": gold_table},
             "chart_qa": {"id": "probe", "task": "chart_qa", "question": "What is the highest value?", "gold": "12"},
             "chart_table": {"id": "probe", "task": "chart_table", "gold": [["x", "y"], ["a", "1"]]},
             "layout": {"id": "probe", "task": "layout", "gold": []}}
    out = {}
    try:
        for task in V1_TASKS:
            for variant in V1_VARIANTS:
                for size_name, size in PROBE_SIZES.items():
                    calls.clear()
                    current["size"] = size
                    ve.run_case(None, "openai:contract-probe", cases[task], variant)
                    out[f"{task}/{variant}/{size_name}"] = list(calls)
        import regions
        out["layout/yolo/detector"] = [{"weights": list(regions.YOLO_WEIGHTS), "classes": regions.YOLO_CLASSES, "min_score": regions.MIN_SCORE,
                                        "min_area_fraction": regions.MIN_AREA_FRACTION, "imgsz": 1024, "device": "cpu"}]
    finally:
        vlm_client.chat, ve.load_image, ve.save_eval_crop = real_chat, real_load, real_save
    return out


def client_hash(repo: Path = REPO) -> str:
    tree = ast.parse((repo / "vlm_client.py").read_text(encoding="utf-8"))
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in ("chat", "png_bytes")) or
            (isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "SYSTEM" for t in n.targets))]
    for n in keep:
        if isinstance(n, ast.FunctionDef) and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            n.body = n.body[1:]
    return hashlib.sha256("\n".join(ast.dump(n, include_attributes=False) for n in keep).encode()).hexdigest()


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def fingerprints(repo: Path = REPO) -> dict:
    sys.path.insert(0, str(repo / "tools"))
    import check_conformance as cc  # the golden inputs live there
    out = {"protocol": PROTOCOL, "requests_sha256": _sha(recorded_requests(repo)), "client_sha256": client_hash(repo),
           "scorers_sha256": _sha({"scorers": cc.run_scorers(), "stats": cc.run_stats()})}
    out["prompts_sha256"] = _sha({"requests": out["requests_sha256"], "client": out["client_sha256"]})
    out["method_sha256"] = _sha({k: out[k] for k in ("protocol", "prompts_sha256", "scorers_sha256")})
    return out


def cases_sha256(manifest: dict) -> str:
    return hashlib.sha256(json.dumps(manifest["cases"], sort_keys=True).encode()).hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--detail", action="store_true")
    a = ap.parse_args()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if a.detail:
        print(json.dumps(recorded_requests(), indent=1, ensure_ascii=False))
    print(json.dumps(fingerprints(), indent=1))
