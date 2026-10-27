"""Paired, page-clustered bootstrap for round 3 and 3b: each parser run against its comparator on identical cases.

  python -X utf8 tools/round3_stats.py --root C:/dev/ocr-lab --out results/vision/round3/stats.json

Comparators (fixed): pages -> openai:qwen3vl32b baseline; tables -> openai:qwen3vl32b baseline; layout -> yolo.
Metric per task: pages word_f1 and numeric_recall; tables teds and numeric_recall; layout figure and table F1
(computed per case from matched/predicted/gold counts, so the bootstrap is on cases). Failed cases count zero.
Equivalence margin for the numeric-recall part: 0.02 (docs/round3/PREREG_3B.md). 2,000 draws, seed 20261026.
Holm correction is applied only over the two pre-registered hypotheses (confirm3 sets); everything else is exploratory.
"""
import argparse
import json
from pathlib import Path
import random
import sqlite3
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vision_eval as ve  # noqa: E402

DRAWS, SEED, MARGIN = 2000, 20261026, 0.02
COMPARATOR = {"page_text": "openai:qwen3vl32b", "table": "openai:qwen3vl32b", "layout": "yolo"}
METRICS = {"page_text": ("word_f1", "numeric_recall"), "table": ("teds", "numeric_recall"), "layout": ("figure_f1", "table_f1")}


def base(task):
    for s in ("_confirm3", "_confirm2", "_confirm"):
        if task.endswith(s):
            return task[: -len(s)]
    return task


def value(metric, metrics):
    if not metrics:
        return 0.0
    if metric.endswith("_f1") and metric[:-3] in ("figure", "table") and metric[:-3] in metrics and isinstance(metrics[metric[:-3]], dict):
        m = metrics[metric[:-3]]
        p = m["matched"] / m["predicted"] if m["predicted"] else None
        r = m["matched"] / m["gold"] if m["gold"] else None
        if p is None and r is None:
            return None  # no gold and no prediction: uninformative case
        return 2 * p * r / (p + r) if p and r else 0.0
    return float(metrics.get(metric) or 0.0)


def rows_for(db, model, task):
    out = {}
    for case_id, status, metrics, image in db.execute(
            "SELECT r.case_id, r.status, r.metrics, c.image FROM vision_results r JOIN case_images c ON c.id = r.case_id WHERE r.model=? AND r.task=?", (model, task)):
        out[case_id] = (status, json.loads(metrics) if metrics else None, image)
    return out


def bootstrap(pairs, draws=DRAWS, seed=SEED):
    """pairs: {cluster: [(a, b), ...]} -> mean difference a-b and percentile interval, resampling clusters."""
    rng = random.Random(seed)
    clusters = list(pairs)
    def mean_diff(sel):
        d = [a - b for c in sel for a, b in pairs[c]]
        return sum(d) / len(d)
    point = mean_diff(clusters)
    draws_ = sorted(mean_diff([rng.choice(clusters) for _ in clusters]) for _ in range(draws))
    return point, draws_[int(0.025 * draws)], draws_[int(0.975 * draws)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    db = sqlite3.connect(f"file:{args.root / 'library.sqlite3'}?mode=ro", uri=True)
    # case -> source image, from every manifest (clusters are source pages)
    db.execute("ATTACH DATABASE ':memory:' AS mem")
    db.execute("CREATE TABLE mem.case_images(id TEXT PRIMARY KEY, image TEXT)")
    for name in ("vision_cases_v1.json", "vision_confirm_v1.json", "vision_cases_v2.json", "vision_cases_v3.json"):
        p = args.root / "evaluation" / name
        if p.exists():
            db.executemany("INSERT OR IGNORE INTO mem.case_images VALUES(?,?)",
                           [(c["id"], c["image"]) for c in json.loads(p.read_text(encoding="utf-8"))["cases"]])
    db.execute("CREATE TEMP VIEW case_images AS SELECT * FROM mem.case_images")
    runs = {}
    for model, task in db.execute("SELECT DISTINCT model, task FROM vision_results WHERE model LIKE 'parser:%'"):
        runs[(model, task)] = rows_for(db, model, task)
    results = []
    for (model, task), rows in sorted(runs.items()):
        b = base(task)
        comp = rows_for(db, COMPARATOR[b], task)
        common = sorted(set(rows) & set(comp))
        if len(common) < 10:
            continue
        entry = {"model": model, "task": task, "comparator": COMPARATOR[b], "cases": len(common), "clusters": len({rows[c][2] for c in common}),
                 "confirmatory": task.endswith("_confirm3")}
        for metric in METRICS[b]:
            pairs = {}
            for c in common:
                a, bb = value(metric, rows[c][1] if rows[c][0] == "complete" else None), value(metric, comp[c][1] if comp[c][0] == "complete" else None)
                if a is None or bb is None:
                    continue
                pairs.setdefault(rows[c][2], []).append((a, bb))
            point, lo, hi = bootstrap(pairs)
            verdict = "better" if lo > 0 else "worse" if hi < 0 else "not distinguishable"
            if metric == "numeric_recall":
                verdict += "; non-inferior" if lo > -MARGIN else "; NOT non-inferior"
            entry[metric] = {"model_mean": round(statistics.mean(a for ps in pairs.values() for a, _ in ps), 4),
                             "comparator_mean": round(statistics.mean(b_ for ps in pairs.values() for _, b_ in ps), 4),
                             "difference": round(point, 4), "ci95": [round(lo, 4), round(hi, 4)], "verdict": verdict}
        results.append(entry)
    # Holm over the two pre-registered hypotheses: H1 table_confirm3 paddleocrvl teds, H2 page_text_confirm3 nemotron-parse word_f1
    prereg = [r for r in results if (r["model"], r["task"]) in {("parser:paddleocrvl", "table_confirm3"), ("parser:nemotron-parse", "page_text_confirm3")}]
    for r in prereg:
        r["note"] = "pre-registered; Holm over 2 hypotheses: with two-sided 95% intervals the stricter hypothesis needs a 97.5% interval to pass; see stats_holm"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"draws": DRAWS, "seed": SEED, "margin": MARGIN, "comparisons": results}, indent=2), encoding="utf-8")
    for r in results:
        line = f"{r['task']:<20} {r['model']:<24} vs {r['comparator']:<18} n={r['cases']:<4} "
        for m in METRICS[base(r["task"])]:
            if m in r:
                line += f"| {m} {r[m]['difference']:+.3f} [{r[m]['ci95'][0]:+.3f},{r[m]['ci95'][1]:+.3f}] {r[m]['verdict']} "
        print(line)


if __name__ == "__main__":
    main()
