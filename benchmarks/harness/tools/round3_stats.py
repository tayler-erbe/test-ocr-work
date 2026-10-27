"""Paired, page-clustered bootstrap for round 3 and 3b: each parser run against its comparator on identical cases.

  python -X utf8 tools/round3_stats.py --root C:/dev/ocr-lab --out results/vision/round3/stats.json

Comparators (fixed): pages and tables -> openai:qwen3vl32b; layout -> yolo. On the fresh confirm3 sets the comparator
is the 32B at the same 8,192 budget (label "openai:qwen3vl32b [budget8192]"); on the earlier sets it is the 32B
baseline at its 6,000 budget. On page_text_confirm2 the parsers' default-budget rows are also paired with the 32B
at 8,744 (the budget-matched arm). Metric per task: pages word_f1 and numeric_recall; tables teds and numeric_recall;
layout figure and table F1 (computed per case from matched/predicted/gold counts). Failed cases count zero.
Equivalence margin for the numeric-recall part: 0.02 (docs/round3/PREREG_3B.md). 2,000 draws, seed 20261026.

Holm over the two pre-registered hypotheses (H1 PaddleOCR-VL tables on table_confirm3, H2 Nemotron Parse pages on
page_text_confirm3): the hypothesis with the smaller two-sided bootstrap p-value on its primary metric is tested at
alpha 0.025, the other at 0.05, sequentially; each passes only if, at its Holm level, the primary difference's lower
bound is above 0 and the numeric-recall difference's lower bound is above -0.02. Everything else is exploratory.
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
VLM, VLM_8192, VLM_8744 = "openai:qwen3vl32b", "openai:qwen3vl32b [budget8192]", "openai:qwen3vl32b [budget8744]"
METRICS = {"page_text": ("word_f1", "numeric_recall"), "table": ("teds", "numeric_recall"), "layout": ("figure_f1", "table_f1")}
HYPOTHESES = {"H1": ("parser:paddleocrvl [budget8192]", "table_confirm3", "teds"),
              "H2": ("parser:nemotron-parse [budget8192]", "page_text_confirm3", "word_f1")}


def base(task):
    for s in ("_confirm3", "_confirm2", "_confirm"):
        if task.endswith(s):
            return task[: -len(s)]
    return task


def comparator(task):
    if base(task) == "layout":
        return "yolo"
    return VLM_8192 if task.endswith("_confirm3") else VLM


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
    """pairs: {cluster: [(a, b), ...]} -> point estimate of mean(a-b) and the sorted bootstrap draws (clusters resampled)."""
    rng = random.Random(seed)
    clusters = list(pairs)

    def mean_diff(sel):
        d = [a - b for c in sel for a, b in pairs[c]]
        return sum(d) / len(d)

    point = mean_diff(clusters)
    return point, sorted(mean_diff([rng.choice(clusters) for _ in clusters]) for _ in range(draws))


def interval(draws_, alpha):
    n = len(draws_)
    return draws_[int(alpha / 2 * n)], draws_[min(n - 1, int((1 - alpha / 2) * n))]


def p_two_sided(draws_):
    n = len(draws_)
    return min(1.0, 2 * min(sum(d <= 0 for d in draws_), sum(d >= 0 for d in draws_)) / n)


def compare(db, model, task, comp_label, draws_store):
    rows, comp = rows_for(db, model, task), rows_for(db, comp_label, task)
    common = sorted(set(rows) & set(comp))
    if len(common) < 10:
        return None
    entry = {"model": model, "task": task, "comparator": comp_label, "cases": len(common), "clusters": len({rows[c][2] for c in common}),
             "confirmatory": task.endswith("_confirm3") and (model, task) in {(m, t) for m, t, _ in HYPOTHESES.values()}}
    for metric in METRICS[base(task)]:
        pairs = {}
        for c in common:
            a = value(metric, rows[c][1] if rows[c][0] == "complete" else None)
            b = value(metric, comp[c][1] if comp[c][0] == "complete" else None)
            if a is None or b is None:
                continue
            pairs.setdefault(rows[c][2], []).append((a, b))
        point, draws_ = bootstrap(pairs)
        draws_store[(model, task, comp_label, metric)] = draws_
        lo, hi = interval(draws_, 0.05)
        verdict = "better" if lo > 0 else "worse" if hi < 0 else "not distinguishable"
        if metric == "numeric_recall":
            verdict += "; non-inferior" if lo > -MARGIN else "; NOT non-inferior"
        entry[metric] = {"model_mean": round(statistics.mean(a for ps in pairs.values() for a, _ in ps), 4),
                         "comparator_mean": round(statistics.mean(b_ for ps in pairs.values() for _, b_ in ps), 4),
                         "difference": round(point, 4), "ci95": [round(lo, 4), round(hi, 4)], "p_two_sided": round(p_two_sided(draws_), 4), "verdict": verdict}
    return entry


def holm(results, draws_store):
    """Sequential Holm over H1 and H2; returns the decision block."""
    found = {}
    for name, (model, task, metric) in HYPOTHESES.items():
        entry = next((r for r in results if r["model"] == model and r["task"] == task and r["comparator"] == comparator(task)), None)
        if entry and metric in entry:
            found[name] = (entry, metric)
    order = sorted(found, key=lambda n: found[n][0][found[n][1]]["p_two_sided"])
    levels, out, blocked = [0.05 / (len(order) - i) for i in range(len(order))], {}, False
    for name, alpha in zip(order, levels):
        entry, metric = found[name]
        model, task = entry["model"], entry["task"]
        lo_primary, hi_primary = interval(draws_store[(model, task, entry["comparator"], metric)], alpha)
        lo_numeric, hi_numeric = interval(draws_store[(model, task, entry["comparator"], "numeric_recall")], alpha)
        beats = lo_primary > 0 and not blocked
        non_inferior = lo_numeric > -MARGIN and not blocked
        passed = beats and non_inferior
        out[name] = {"model": model, "task": task, "primary_metric": metric, "holm_alpha": alpha,
                     "primary_interval": [round(lo_primary, 4), round(hi_primary, 4)], "primary_p": entry[metric]["p_two_sided"],
                     "numeric_recall_interval": [round(lo_numeric, 4), round(hi_numeric, 4)], "margin": MARGIN,
                     "beats": beats, "numeric_non_inferior": non_inferior, "passed": passed,
                     "reading": ("passed" if passed else "cleaner output, fewer numbers: lead on the primary metric without numeric non-inferiority" if beats
                                 else "blocked by the earlier Holm step" if blocked else "no lead on the primary metric at the Holm level")}
        if not (lo_primary > 0):
            blocked = True  # Holm stops at the first non-rejection
    for name in HYPOTHESES:
        out.setdefault(name, {"passed": False, "reading": "rows not found (comparison not run yet)"})
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    db = sqlite3.connect(f"file:{args.root / 'library.sqlite3'}?mode=ro", uri=True)
    db.execute("ATTACH DATABASE ':memory:' AS mem")
    db.execute("CREATE TABLE mem.case_images(id TEXT PRIMARY KEY, image TEXT)")
    for name in ("vision_cases_v1.json", "vision_confirm_v1.json", "vision_cases_v2.json", "vision_cases_v3.json"):
        p = args.root / "evaluation" / name
        if p.exists():
            db.executemany("INSERT OR IGNORE INTO mem.case_images VALUES(?,?)",
                           [(c["id"], c.get("cluster") or c["image"]) for c in json.loads(p.read_text(encoding="utf-8"))["cases"]])
    db.execute("CREATE TEMP VIEW case_images AS SELECT * FROM mem.case_images")
    labels = sorted(db.execute("SELECT DISTINCT model, task FROM vision_results WHERE model LIKE 'parser:%'").fetchall())
    results, draws_store = [], {}
    for model, task in labels:
        entry = compare(db, model, task, comparator(task), draws_store)
        if entry:
            results.append(entry)
        if task == "page_text_confirm2" and "[" not in model:  # budget-matched arm: parser default budget vs the 32B at 8,744
            entry = compare(db, model, task, VLM_8744, draws_store)
            if entry:
                entry["note"] = "budget-matched arm: parser at its default budget against the 32B at 8,744 tokens"
                results.append(entry)
    decisions = holm(results, draws_store)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"draws": DRAWS, "seed": SEED, "margin": MARGIN, "holm": decisions, "comparisons": results}, indent=2), encoding="utf-8")
    for r in results:
        line = f"{r['task']:<20} {r['model']:<40} vs {r['comparator']:<32} n={r['cases']:<4} "
        for m in METRICS[base(r["task"])]:
            if m in r:
                line += f"| {m} {r[m]['difference']:+.3f} [{r[m]['ci95'][0]:+.3f},{r[m]['ci95'][1]:+.3f}] {r[m]['verdict']} "
        print(line)
    for name, d in decisions.items():
        print(name, json.dumps(d))


if __name__ == "__main__":
    main()
