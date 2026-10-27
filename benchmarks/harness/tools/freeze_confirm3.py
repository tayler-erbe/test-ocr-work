"""Freeze the round-3b confirmation sets (docs/round3/PREREG_3B.md) from OmniDocBench pages unused so far.

  python -X utf8 tools/freeze_confirm3.py --root C:/dev/ocr-lab

Writes evaluation/vision_cases_v3.json once; refuses to overwrite. Selection is by sorted content hash,
the same rule vision_eval.py used for every earlier set, so nothing here depends on any model's output.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vision_eval as ve  # noqa: E402
from document_lab import digest, now  # noqa: E402

PAGES, TABLES = 80, 100


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    out = args.root / "evaluation" / "vision_cases_v3.json"
    if out.exists():
        raise SystemExit(f"{out} exists; frozen sets are never rebuilt")
    used_pages, used_tables = set(), set()
    for name in ("vision_cases_v1.json", "vision_confirm_v1.json", "vision_cases_v2.json"):
        for c in json.loads((args.root / "evaluation" / name).read_text(encoding="utf-8"))["cases"]:
            if c["task"].startswith("page_text"):
                used_pages.add(c["image"])
            if c["task"].startswith("table"):
                used_tables.add(c["image"])
    pages = ve.omni_pages(args.root)
    fresh_pages = [p for p in pages if f"{ve.OMNI}/images/{Path(p['page_info']['image_path']).name}" not in used_pages]
    page_cases = ve.build_page_text(args.root, fresh_pages, PAGES)
    fresh_table_pages = [p for p in pages if f"{ve.OMNI}/images/{Path(p['page_info']['image_path']).name}" not in used_tables]
    table_cases = ve.build_table(args.root, fresh_table_pages, TABLES)
    assert len(page_cases) == PAGES and len(table_cases) == TABLES, (len(page_cases), len(table_cases))
    for c in page_cases:
        c["task"], c["score_as"] = "page_text_confirm3", "page_text"
        c["id"] = "p3:" + c["id"].split(":", 1)[1]
    for c in table_cases:
        c["task"], c["score_as"] = "table_confirm3", "table"
        c["id"] = "t3:" + c["id"].split(":", 1)[1]
    cases = page_cases + table_cases
    assert not ({c["image"] for c in page_cases} & used_pages) and not ({c["image"] for c in table_cases} & used_tables)
    manifest = {"protocol": "vision-v3-confirm", "created": now(), "counts": {"page_text_confirm3": PAGES, "table_confirm3": TABLES},
                "rule": "unused in vision_cases_v1, vision_confirm_v1 and vision_cases_v2; sorted content hash; see docs/round3/PREREG_3B.md",
                "cases_sha256": hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(), "cases": cases}
    out.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"written": str(out), "cases_sha256": manifest["cases_sha256"], "pages": PAGES, "tables": TABLES,
                      "table_source_pages": len({c["image"] for c in table_cases})}))


if __name__ == "__main__":
    main()
