"""Rebuild round-2 page presentation aggregates without inference or scoring changes."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks/harness"))
from vision_eval import aggregate


def rebuild(write=False):
    path = ROOT / "site/data/benchmark.json"
    data = json.loads(path.read_text(encoding="utf8"))
    groups = collections.defaultdict(list)
    hashes = {}
    for side in ("desktop", "laptop"):
        source = ROOT / f"results/vision/exports/{side}.jsonl"
        hashes[side] = hashlib.sha256(source.read_bytes()).hexdigest()
        with source.open(encoding="utf8") as stream:
            for line in stream:
                row = json.loads(line)
                if row["task"] == "page_text_confirm2":
                    assert row["case_set"] == "v2" and row["side"] == side
                    groups[(side, row["model"], row["variant"])].append(row)
    audited = []
    for row in data["rows"]:
        if row["task"] != "page_text" or row["split"] != "confirmation v2":
            continue
        rows = groups.pop((row["side"], row["model_id"], row["variant"]))
        assert len(rows) == 80 and len({r["case_id"] for r in rows}) == 80
        values = aggregate("page_text_confirm2", [(r["status"], r["metrics"], r["seconds"]) for r in rows])
        assert abs(values["word_f1"] - row["score"]) < 0.001, "Published score mismatch"
        row.update(score=values["word_f1"], failed=values["failed"], median_seconds=values["median_seconds"], numeric_recall=values["numeric_recall"])
        row["source"] = "round2-audit"
        row["source_section"] = "80 attempts; failures score zero; latency median over completed scored attempts"
        audited.append({**row, "export_sha256": hashes[row["side"]], "run_ids": sorted({r["run_id"] for r in rows})})
    assert len(audited) == 6 and not groups
    data["sources"]["round2-audit"] = {"url": "data/round2-audit.json", "title": "Round-2 export audit"}
    audit = {"method": "Existing vision_eval.aggregate; failures score zero; median seconds excludes failed/unscored attempts. No predictions or references inspected or rescored.", "export_sha256": hashes, "rows": audited}
    output = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    audit_path = ROOT / "site/data/round2-audit.json"
    audit_output = json.dumps(audit, indent=2, ensure_ascii=False) + "\n"
    if write:
        path.write_text(output, encoding="utf8")
        audit_path.write_text(audit_output, encoding="utf8")
    else:
        assert path.read_text(encoding="utf8") == output, "Dashboard differs; run with --write"
        assert audit_path.read_text(encoding="utf8") == audit_output, "Audit differs"
    print("PASS: six round-2 configurations, 480 attempts, source hashes and aggregates")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    rebuild(parser.parse_args().write)
