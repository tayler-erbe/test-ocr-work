"""Freeze the round-3b confirmation sets (docs/round3/PREREG_3B.md) before any 3b run.

  python -X utf8 tools/freeze_confirm3.py --root C:/dev/ocr-lab

page_text_confirm3: 80 OmniDocBench English pages unused by every earlier page task, chosen by sorted content hash
with vision_eval.build_page_text unchanged.
table_confirm3: 100 FinTabNet.c test tables (no unused English OmniDocBench table exists), chosen by sorted hash
of the annotation file name; gold HTML is built here from the structure annotation (row and column boxes,
spanning cells, words by centre). The builder is part of this frozen file.
Writes evaluation/vision_cases_v3.json once; refuses to overwrite. Every case carries a "cluster" (source page or
source report) for the paired bootstrap.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vision_eval as ve  # noqa: E402
from document_lab import digest, now  # noqa: E402

PAGES, TABLES = 80, 100
FIN = "datasets/fintabnet/raw/FinTabNet.c-Structure"


def boxes(xml_path):
    root = ET.parse(xml_path).getroot()
    out = []
    for obj in root.findall("object"):
        name = obj.findtext("name")
        b = obj.find("bndbox")
        box = [float(b.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax")]
        out.append((name, box))
    size = root.find("size")
    return out, (int(size.findtext("width")), int(size.findtext("height")))


def overlap_1d(a0, a1, b0, b1):
    inter = max(0.0, min(a1, b1) - max(a0, b0))
    return inter / max(1e-6, (b1 - b0))


def table_html(xml_path, words_path):
    """Gold HTML (rowspan/colspan, as the OmniDocBench gold uses) from a FinTabNet.c structure annotation."""
    objs, size = boxes(xml_path)
    rows = sorted([b for n, b in objs if n == "table row"], key=lambda b: b[1])
    cols = sorted([b for n, b in objs if n == "table column"], key=lambda b: b[0])
    spans = [b for n, b in objs if n == "table spanning cell"]
    words = json.loads(Path(words_path).read_text(encoding="utf-8"))
    if not rows or not cols:
        return None
    # which grid cells each spanning cell covers (>= 50% of the row/column extent)
    covered, anchors = {}, {}
    for sb in spans:
        rr = [i for i, r in enumerate(rows) if overlap_1d(sb[1], sb[3], r[1], r[3]) >= 0.5]
        cc = [j for j, c in enumerate(cols) if overlap_1d(sb[0], sb[2], c[0], c[2]) >= 0.5]
        if len(rr) * len(cc) <= 1:
            continue
        anchor = (rr[0], cc[0])
        anchors[anchor] = (len(rr), len(cc), sb)
        for i in rr:
            for j in cc:
                if (i, j) != anchor:
                    covered[(i, j)] = anchor

    def text_in(box):
        inside = [w for w in words if box[0] <= (w["bbox"][0] + w["bbox"][2]) / 2 <= box[2] and box[1] <= (w["bbox"][1] + w["bbox"][3]) / 2 <= box[3]]
        inside.sort(key=lambda w: (round((w["bbox"][1] + w["bbox"][3]) / 2 / 8), w["bbox"][0]))
        return " ".join(w["text"] for w in inside)

    parts = ["<table>"]
    for i, r in enumerate(rows):
        parts.append("<tr>")
        for j, c in enumerate(cols):
            if (i, j) in covered:
                continue
            if (i, j) in anchors:
                rs, cs, sb = anchors[(i, j)]
                attrs = (f' rowspan="{rs}"' if rs > 1 else "") + (f' colspan="{cs}"' if cs > 1 else "")
                parts.append(f"<td{attrs}>{html.escape(text_in(sb))}</td>")
            else:
                parts.append(f"<td>{html.escape(text_in([c[0], r[1], c[2], r[3]]))}</td>")
        parts.append("</tr>")
    parts.append("</table>")
    return "".join(parts)


def build_fintabnet(root, count):
    test = sorted((root / FIN / "test").glob("*.xml"))
    ranked = sorted(test, key=lambda p: digest("fintab-v3:" + p.name))
    cases = []
    for xml_path in ranked:
        name = xml_path.stem
        words_path = root / FIN / "words" / f"{name}_words.json"
        image_rel = f"{FIN}/images/{name}.jpg"
        if not words_path.exists() or not (root / image_rel).exists():
            continue  # only members that were extracted (tools/extract_fintabnet_members.sh) are eligible
        gold = table_html(xml_path, words_path)
        if not gold:
            continue
        parsed = ve.parse_html_table(gold)
        if not (2 <= len(parsed) <= 40) or sum(1 for r in parsed for c in r if c[0]) < 4:
            continue
        company_year = "_".join(name.split("_")[:2])
        cases.append({"id": "t3:" + digest("fintab-v3:" + name)[:16], "task": "table_confirm3", "score_as": "table", "image": image_rel,
                      "source": "fintabnet", "cluster": "fintabnet:" + company_year, "gold": gold})
        if len(cases) == count:
            break
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--list-only", action="store_true", help="print the 100 candidate FinTabNet names to extract, without freezing")
    args = parser.parse_args()
    out = args.root / "evaluation" / "vision_cases_v3.json"
    if out.exists():
        raise SystemExit(f"{out} exists; frozen sets are never rebuilt")
    if args.list_only:
        test = sorted((args.root / FIN / "test").glob("*.xml"))
        ranked = sorted(test, key=lambda p: digest("fintab-v3:" + p.name))[: count_hint()]
        for p in ranked:
            print(p.stem)
        return
    used_pages = set()
    for name in ("vision_cases_v1.json", "vision_confirm_v1.json", "vision_cases_v2.json"):
        for c in json.loads((args.root / "evaluation" / name).read_text(encoding="utf-8"))["cases"]:
            if c["task"].startswith("page_text"):
                used_pages.add(c["image"])
    pages = ve.omni_pages(args.root)
    fresh_pages = [p for p in pages if f"{ve.OMNI}/images/{Path(p['page_info']['image_path']).name}" not in used_pages]
    page_cases = ve.build_page_text(args.root, fresh_pages, PAGES)
    for c in page_cases:
        c["task"], c["score_as"], c["cluster"] = "page_text_confirm3", "page_text", c["image"]
        c["id"] = "p3:" + c["id"].split(":", 1)[1]
    table_cases = build_fintabnet(args.root, TABLES)
    assert len(page_cases) == PAGES and len(table_cases) == TABLES, (len(page_cases), len(table_cases))
    assert not ({c["image"] for c in page_cases} & used_pages)
    cases = page_cases + table_cases
    manifest = {"protocol": "vision-v3-confirm", "created": now(), "counts": {"page_text_confirm3": PAGES, "table_confirm3": TABLES},
                "rule": "pages: unused OmniDocBench English pages by sorted content hash; tables: FinTabNet.c test by sorted name hash, gold built by this file; docs/round3/PREREG_3B.md",
                "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "cases_sha256": hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(), "cases": cases}
    out.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"written": str(out), "cases_sha256": manifest["cases_sha256"], "pages": PAGES, "tables": TABLES,
                      "table_reports": len({c["cluster"] for c in table_cases})}))


def count_hint():
    return 160  # extract more than 100 so filtering (words present, 2..40 rows, >= 4 filled cells) still leaves 100


if __name__ == "__main__":
    main()
