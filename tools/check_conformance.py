"""Conformance check for vision-v1: run it on BOTH machines before any model run and before merging.

It proves the two sides are running the same evaluation:
  1. code       the prompt, scorer and case-selection fingerprints equal the frozen contract (tools/contract.json)
  2. manifests  both frozen case files are present and their cases_sha256 equal the frozen values
  3. data       (optional, --data) every image a case needs exists; with a case-pack RECEIPT.json, byte hashes too
  4. scorers    fixed, fabricated predictions -> the exact expected scores in tools/golden_scores.json
  5. stats      the paired bootstrap, exact McNemar and Holm steps on a fabricated table -> expected values
  6. results    (optional, --results FILE) an export from tools/export_results.py matches the row schema

No model is called and no real document is read for checks 1, 4 and 5. Exit code 0 only if every check passes.

  python tools/check_conformance.py --root C:/dev/ocr-lab
  python tools/check_conformance.py --root LAB --data --results exports/laptop.jsonl
  python tools/check_conformance.py --freeze-golden     # maintainers only: rewrite golden_scores.json from the current scorers
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import eval_contract  # noqa: E402

GOLDEN = REPO / "tools" / "golden_scores.json"
CONTRACT = REPO / "tools" / "contract.json"
TOL = 1e-9

# ---------------------------------------------------------------- fabricated scorer cases (no real documents)

GOLD_TABLE = ("<table><tr><td colspan=\"2\">Region totals</td></tr><tr><td>North</td><td>1,204</td></tr>"
              "<tr><td>South</td><td>98.5%</td></tr><tr><td>East</td><td>$-3.2</td></tr></table>")
SCORER_CASES = {
    "relaxed_match": [["12", "12.5"], ["12", "13"], ["1,000", "1000"], ["45%", "45"], ["0", "0"], ["0.1", "0"],
                      ["10.5", "10"], ["9.5", "10"], ["10.51", "10"], ["Yes.", "yes"], ["North America", "north  america"], ["−5", "-5"], ["$3.10", "3"], ["abc", "abd"]],
    "edit_distance": [["kitten", "sitting"], ["", "abc"], ["same", "same"], ["Ünïcode", "Unicode"]],
    "norm": ["  a\u00a0b\tc\n\nd  ", "ﬁne ﬂow", "Ｆｕｌｌ ｗｉｄｔｈ"],
    "numbers": ["Revenue rose 12.5% to 1,204 units in 2024 (v2)", "no digits here", "3.14.15 and 007"],
    "words_f1": [["The cat sat on the mat", "the cat sat on a mat mat"], ["", "anything"], ["one two", ""]],
    "score_table": [
        {"header": ["Region totals", "Region totals"], "rows": [["North", "1,204"], ["South", "98.5%"], ["East", "-3.2"]]},
        {"header": [], "rows": [["North", "1204"], ["South", "98.5"]]},
        {"header": [], "rows": []},
    ],
    "score_chart_table": [
        {"gold": [["Year", "Sales", "Cost"], ["2020", "10", "4"], ["2021", "20", "0"], ["2022", "30.5", "n/a"]],
         "out": {"header": ["Year", "Sales", "Cost"], "rows": [["2020", "10.4", "4"], ["2021", "19", "0"], ["2023", "31", "9"]]}},
        {"gold": [["x", "y"], ["a", "1"]], "out": {"rows": []}},
    ],
    "score_layout": [
        {"gold": [{"kind": "figure", "bbox": [0, 0, 100, 100]}, {"kind": "table", "bbox": [200, 200, 400, 300]}],
         "found": [{"kind": "chart", "bbox": [10, 10, 100, 110]}, {"kind": "table", "bbox": [0, 400, 50, 450]},
                   {"kind": "table", "bbox": [210, 200, 400, 310]}]},
        {"gold": [], "found": [{"kind": "figure", "bbox": [0, 0, 10, 10]}]},
    ],
}


def run_scorers():
    import vision_eval as ve
    out = {}
    out["relaxed_match"] = [ve.relaxed_match(p, g) for p, g in SCORER_CASES["relaxed_match"]]
    out["edit_distance"] = [ve.edit_distance(a, b) for a, b in SCORER_CASES["edit_distance"]]
    out["norm"] = [ve.norm(t) for t in SCORER_CASES["norm"]]
    out["numbers"] = [dict(sorted(ve.numbers(t).items())) for t in SCORER_CASES["numbers"]]
    out["words_f1"] = [list(ve.f1(ve.words(a), ve.words(b))) for a, b in SCORER_CASES["words_f1"]]
    out["parse_html_table"] = ve.parse_html_table(GOLD_TABLE)
    out["score_table"] = [ve.score_table(GOLD_TABLE, p) for p in SCORER_CASES["score_table"]]
    out["score_chart_table"] = [ve.score_chart_table(c["gold"], c["out"]) for c in SCORER_CASES["score_chart_table"]]
    out["score_layout"] = [ve.score_layout(c["gold"], c["found"]) for c in SCORER_CASES["score_layout"]]
    # aggregate(): failed cases stay in the denominator as zeros
    out["aggregate_chart_qa"] = ve.aggregate("chart_qa", [("complete", {"correct": True}, 1.0), ("complete", {"correct": False}, 2.0),
                                                          ("failed", None, 3.0), ("complete", {"correct": True}, 4.0)])
    out["aggregate_ocr_crop"] = ve.aggregate("ocr_crop", [
        ("complete", {"errors": 3, "reference_chars": 100, "numeric_expected": 4, "numeric_predicted": 5, "numeric_matched": 3}, 1.5),
        ("complete", {"errors": 10, "reference_chars": 50, "numeric_expected": 0, "numeric_predicted": 1, "numeric_matched": 0}, 0.5)])
    out["aggregate_layout"] = ve.aggregate("layout", [("complete", c, 1.0) for c in out["score_layout"]])
    return json.loads(json.dumps(out))  # tuples -> lists, as stored


# ---------------------------------------------------------------- statistics on a fabricated paired table

def run_stats():
    """Re-implements nothing: drives vision_eval.compare() on an in-memory database of fabricated rows."""
    import tempfile
    import vision_eval as ve

    rng = random.Random(7)
    rows = []
    for i in range(40):  # chart_qa: right/wrong per case
        base = rng.random() < 0.6
        var = base if rng.random() < 0.7 else (rng.random() < 0.8)
        rows.append(("m", "chart_qa", f"c{i}", "baseline", {"correct": base}))
        rows.append(("m", "chart_qa", f"c{i}", "selfcheck", {"correct": var}))
    for i in range(25):  # table: continuous TEDS
        b = round(rng.random(), 3)
        rows.append(("m", "table", f"t{i}", "baseline", {"teds": b}))
        rows.append(("m", "table", f"t{i}", "expert", {"teds": min(1.0, round(b + rng.uniform(-0.05, 0.15), 3))}))
    for i in range(30):  # confirmatory family
        b = rng.random() < 0.5
        rows.append(("m", "chart_qa_confirm", f"q{i}", "baseline", {"correct": b}))
        rows.append(("m", "chart_qa_confirm", f"q{i}", "tuned", {"correct": b or rng.random() < 0.3}))
    import contextlib
    import io
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
            "test", "p_value", "family", "p_holm", "verdict", "verdict_after_correction")
    return [{k: r[k] for k in keep} for r in result]


# ---------------------------------------------------------------- comparison helpers

def same(a, b, path="$"):
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None:
            return [] if a is b else [f"{path}: {a!r} != {b!r}"]
        if isinstance(a, bool) or isinstance(b, bool):
            return [] if a == b else [f"{path}: {a!r} != {b!r}"]
        return [] if math.isclose(float(a), float(b), rel_tol=0, abs_tol=TOL) else [f"{path}: {a!r} != {b!r}"]
    if isinstance(a, dict) and isinstance(b, dict):
        diffs = [f"{path}: keys {sorted(set(a) ^ set(b))}"] if set(a) != set(b) else []
        for k in sorted(set(a) & set(b)):
            diffs += same(a[k], b[k], f"{path}.{k}")
        return diffs
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += same(x, y, f"{path}[{i}]")
        return out
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


# ---------------------------------------------------------------- result-file schema

ROW_FIELDS = {"schema": str, "side": str, "protocol": str, "case_set": str, "cases_sha256": str, "method_sha256": str,
              "prompts_sha256": str, "scorers_sha256": str, "run_id": str, "case_id": str, "task": str, "model": str,
              "variant": str, "mode": str, "run": int, "weights": (str, type(None)), "status": str, "prediction": object,
              "metrics": (dict, type(None)), "seconds": (float, int), "error": (str, type(None)), "created": str}
OPTIONAL_FIELDS = {"r2_method_sha256": str}  # round-2 rows only (tools/eval_contract_r2.py)
CONTRACT_R2 = REPO / "tools" / "contract_r2.json"
GOLDEN_R2 = REPO / "tools" / "golden_r2.json"
VARIANTS = set(eval_contract.V1_VARIANTS)
STATUSES = {"complete", "failed"}


def check_results(path: Path, contract: dict, allow_round2: bool = False) -> list:
    problems, seen = [], set()
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            try:
                row = json.loads(line)
            except ValueError as e:
                problems.append(f"line {n}: not JSON ({e})")
                continue
            for k, t in ROW_FIELDS.items():
                if k not in row:
                    problems.append(f"line {n}: missing {k}")
                elif t is not object and not isinstance(row[k], t):
                    problems.append(f"line {n}: {k} has type {type(row[k]).__name__}")
            if set(row) - set(ROW_FIELDS) - set(OPTIONAL_FIELDS):
                problems.append(f"line {n}: unexpected fields {sorted(set(row) - set(ROW_FIELDS) - set(OPTIONAL_FIELDS))}")
            if problems and len(problems) > 50:
                return problems + ["(stopped after 50 problems)"]
            round2 = row.get("case_set") == "v2" or row.get("variant") not in VARIANTS
            if round2 and not allow_round2:
                problems.append(f"line {n}: round-2 row (case set {row.get('case_set')}, variant {row.get('variant')}); pass --round2 to allow")
            elif round2:
                want = json.loads(CONTRACT_R2.read_text(encoding="utf-8"))["method_sha256"]
                if row.get("r2_method_sha256") != want:
                    problems.append(f"line {n}: round-2 row without the round-2 contract hash (r2_method_sha256 must be {want[:16]})")
            if row.get("status") not in STATUSES or row.get("mode") not in ("image", "table_only"):
                problems.append(f"line {n}: bad status/mode {row.get('status')}/{row.get('mode')}")
            if row.get("status") == "complete" and row.get("metrics") is None:
                problems.append(f"line {n}: complete row without metrics")
            if row.get("case_set") in eval_contract.FROZEN and row.get("cases_sha256") != eval_contract.FROZEN[row["case_set"]]["cases_sha256"]:
                problems.append(f"line {n}: cases_sha256 is not the frozen {row['case_set']} set")
            for k in ("prompts_sha256", "scorers_sha256", "method_sha256"):
                if row.get(k) != contract[k]:
                    problems.append(f"line {n}: {k} differs from the contract (different prompts or scorers)")
            key = (row.get("case_id"), row.get("model"), row.get("variant"), row.get("mode"), row.get("run"))
            if key in seen:
                problems.append(f"line {n}: duplicate row {key}")
            seen.add(key)
    return problems


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, help="the lab folder holding evaluation/ and datasets/ (e.g. C:/dev/ocr-lab)")
    ap.add_argument("--data", action="store_true", help="also check that every case's image is present (and its hash, with a pack receipt)")
    ap.add_argument("--results", type=Path, action="append", default=[], help="an export from tools/export_results.py to validate")
    ap.add_argument("--round2", action="store_true", help="also check the round-2 addendum (tools/contract_r2.json) and allow round-2 rows in result files")
    ap.add_argument("--freeze-golden", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()

    if a.freeze_golden:
        GOLDEN.write_text(json.dumps({"scorers": run_scorers(), "stats": run_stats()}, indent=1, ensure_ascii=False), encoding="utf-8")
        CONTRACT.write_text(json.dumps({**eval_contract.fingerprints(), "frozen_case_sets": eval_contract.FROZEN}, indent=1), encoding="utf-8")
        print(f"wrote {GOLDEN} and {CONTRACT}")
        return 0

    results, failed = [], False

    def report(name, problems):
        nonlocal failed
        failed |= bool(problems)
        results.append({"check": name, "pass": not problems, "problems": problems[:20]})

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    live = eval_contract.fingerprints()
    report("code fingerprints", [f"{k}: live {live[k][:16]} != contract {contract[k][:16]}"
                                 for k in ("requests_sha256", "client_sha256", "scorers_sha256", "prompts_sha256", "method_sha256") if live[k] != contract[k]])

    if a.root:
        problems = []
        for which, spec in eval_contract.FROZEN.items():
            path = a.root / spec["file"]
            if not path.exists():
                if spec["required"]:
                    problems.append(f"{which}: {path} missing (copy it from the desktop; never rebuild it)")
                continue
            m = json.loads(path.read_text(encoding="utf-8"))
            if m.get("protocol") != spec["protocol"]:
                problems.append(f"{which}: protocol {m.get('protocol')} != {spec['protocol']}")
            got = eval_contract.cases_sha256(m)
            if got != spec["cases_sha256"] or m.get("cases_sha256") != spec["cases_sha256"]:
                problems.append(f"{which}: cases_sha256 {got[:16]} (recomputed) / {str(m.get('cases_sha256'))[:16]} (stored) != {spec['cases_sha256'][:16]}")
            counts = {}
            for c in m["cases"]:
                counts[c["task"]] = counts.get(c["task"], 0) + 1
            if counts != spec["counts"]:
                problems.append(f"{which}: counts {counts} != {spec['counts']}")
        report("frozen manifests", problems)

        if a.data:
            import hashlib
            import zipfile
            problems, needed = [], set()
            for spec in eval_contract.FROZEN.values():
                path = a.root / spec["file"]
                if path.exists():
                    for c in json.loads(path.read_text(encoding="utf-8"))["cases"]:
                        needed.add(c["image"])
            zpath = a.root / "datasets/chartqa/raw/ChartQA Dataset.zip"
            zipped = set(zipfile.ZipFile(zpath).namelist()) if zpath.exists() else set()
            if not zpath.exists():
                problems.append(f"{zpath} missing")
            for name in sorted(needed):
                if name.startswith("datasets/"):
                    if not (a.root / name).exists():
                        problems.append(f"missing image {name}")
                elif zipped and name not in zipped:
                    problems.append(f"missing from ChartQA zip: {name}")
            receipt = a.root / "RECEIPT.json"
            if receipt.exists():
                for rel, want in json.loads(receipt.read_text(encoding="utf-8"))["files"].items():
                    p = a.root / rel
                    if not p.exists():
                        problems.append(f"receipt: {rel} missing")
                        continue
                    h = hashlib.sha256()
                    with open(p, "rb") as f:
                        for block in iter(lambda: f.read(1 << 20), b""):
                            h.update(block)
                    if h.hexdigest() != want:
                        problems.append(f"receipt: {rel} hash differs")
            report(f"case data ({len(needed)} images{', receipt hashes' if receipt.exists() else ''})", problems)

    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    report("scorers on golden predictions", same(run_scorers(), golden["scorers"]))
    report("statistics on golden table", same(run_stats(), golden["stats"]))

    if a.round2:
        import eval_contract_r2 as r2
        c2 = json.loads(CONTRACT_R2.read_text(encoding="utf-8"))
        live2 = r2.fingerprints()
        report("round 2: code fingerprints", [f"{k}: live {str(live2[k])[:16]} != contract {str(c2[k])[:16]}" for k in live2 if live2[k] != c2[k]])
        g2 = json.loads(GOLDEN_R2.read_text(encoding="utf-8"))
        report("round 2: requests and stand-in scoring", same(r2.recorded_requests(), g2["requests"]))
        report("round 2: vote3 majority rule", same(r2.run_vote(), g2["vote"]))
        report("round 2: statistics and Holm families", same(r2.run_stats(), g2["stats"]))
        if a.root and not (a.root / eval_contract.FROZEN["v2"]["file"]).exists():
            report("round 2: v2 manifest", [f"{a.root / eval_contract.FROZEN['v2']['file']} missing (it is in case_pack/evaluation/)"])

    for path in a.results:
        report(f"result file {path.name}", check_results(path, contract, a.round2))

    for r in results:
        print(("PASS " if r["pass"] else "FAIL ") + r["check"])
        for p in r["problems"]:
            print("     - " + p)
    if a.round2 and not failed:
        print("Round-2 variant status: " + "; ".join(f"{k} = {v.split(':')[0]}" for k, v in json.loads(CONTRACT_R2.read_text(encoding="utf-8"))["status"].items()))
    print("CONFORMANT" if not failed else "NOT CONFORMANT: do not run or merge until every check passes")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
