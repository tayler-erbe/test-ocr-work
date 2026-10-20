"""Merge desktop and laptop vision-v1 exports into one evaluation, and measure how well the two sides agree.

Refuses to merge unless every row was produced under the same contract: the same frozen case set
(cases_sha256), the same prompts and budgets (prompts_sha256) and the same scorers (scorers_sha256).

Writes to --out (a folder that is itself a valid lab root, so vision_eval.py can be pointed at it):
  merged.jsonl                       every row from every input, unchanged
  library.sqlite3                    vision_results with models labelled 'model@side [variant]'
  evaluation/                        the frozen manifests, copied from --root (needed for the ChartQA split columns)
  reports/vision-evaluation-summary.json and reports/vision-variant-comparison.json   from vision_eval report / compare
  reports/reproducibility.json       same model + variant + case on both sides: identical answers, score agreement
  MERGED_REPORT.md                   the standard report tables, generated from the files above

  python tools/merge_results.py --root C:/dev/ocr-lab --out merged/2026-10-21 exports/desktop.jsonl exports/laptop.jsonl
"""
import argparse
import contextlib
import io
import json
import random
import shutil
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import eval_contract  # noqa: E402

CONTRACT_KEYS = ("protocol", "prompts_sha256", "scorers_sha256", "method_sha256")
SEED = 20261019


class Refused(SystemExit):
    pass


def load(paths):
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            rows += [json.loads(line) for line in f if line.strip()]
    return rows


def refuse_mismatches(rows, allow_round2=False):
    contract = json.loads((REPO / "tools" / "contract.json").read_text(encoding="utf-8"))
    problems = []
    for k in CONTRACT_KEYS:
        values = {r[k] for r in rows}
        if len(values) != 1:
            problems.append(f"{k} differs between rows: {sorted(v[:16] for v in values)}")
        elif k != "protocol" and values != {contract[k]}:
            problems.append(f"{k} is not this repository's contract ({next(iter(values))[:16]} vs {contract[k][:16]})")
    frozen = {s["cases_sha256"] for s in eval_contract.FROZEN.values()}
    bad = {r["cases_sha256"][:16] for r in rows if r["cases_sha256"] not in frozen}
    if bad:
        problems.append(f"rows from unfrozen case sets: {sorted(bad)}")
    r2 = sum(1 for r in rows if r["case_set"] == "v2" or r["variant"] not in eval_contract.V1_VARIANTS)
    if r2 and not allow_round2:
        problems.append(f"{r2} round-2 rows (v2 cases or round-2 variants); pass --round2 to include them")
    keys = {}
    for r in rows:
        k = (r["side"], r["case_id"], r["model"], r["variant"], r["mode"], r["run"])
        if k in keys:
            problems.append(f"duplicate row {k}")
            break
        keys[k] = r
    if problems:
        raise Refused("REFUSED to merge:\n  - " + "\n  - ".join(problems))


def case_score(task, metrics):
    """One per-case number for agreement checks (higher is better except ocr_crop, where it is the error rate)."""
    if metrics is None:
        return 0.0
    t = task.replace("_confirm", "")
    if t == "chart_qa":
        return float(bool(metrics.get("correct")))
    if t == "table":
        return float(metrics.get("teds") or 0)
    if t == "chart_table":
        return float(metrics.get("value_recall") or 0)
    if t == "page_text":
        return float(metrics.get("word_f1") or 0)
    if t == "ocr_crop":
        return metrics["errors"] / max(1, metrics["reference_chars"])
    if t == "layout":
        m = sum(metrics[k]["matched"] for k in ("figure", "table"))
        d = sum(metrics[k]["gold"] + metrics[k]["predicted"] for k in ("figure", "table"))
        return 2 * m / d if d else 1.0
    raise ValueError(task)


def reproducibility(rows):
    sides = sorted({r["side"] for r in rows})
    index = {}
    for r in rows:
        index.setdefault((r["case_id"], r["task"], r["model"], r["variant"], r["mode"], r["run"]), {})[r["side"]] = r
    groups = {}
    for (case, task, model, variant, mode, run), by_side in index.items():
        if len(by_side) < 2:
            continue
        a, b = by_side[sides[0]], by_side[sides[1]]
        g = groups.setdefault((model, task, variant, mode), {"pairs": [], "weights": set()})
        g["weights"].add((a["weights"], b["weights"]))
        g["pairs"].append((a, b))
    rng = random.Random(SEED)
    out = []
    for (model, task, variant, mode), g in sorted(groups.items()):
        pairs = g["pairs"]
        sa = [case_score(task, a["metrics"]) if a["status"] == "complete" else 0.0 for a, _ in pairs]
        sb = [case_score(task, b["metrics"]) if b["status"] == "complete" else 0.0 for _, b in pairs]
        diffs = [y - x for x, y in zip(sa, sb)]
        boot = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(2000))
        same_weights = all(wa == wb for wa, wb in g["weights"])
        out.append({"model": model, "task": task, "variant": variant, "mode": mode, "shared_cases": len(pairs),
                    "same_weights": same_weights, "weights": sorted({w for pair in g["weights"] for w in pair if w}),
                    "identical_prediction": round(sum(a["prediction"] == b["prediction"] for a, b in pairs) / len(pairs), 4),
                    "identical_case_score": round(sum(abs(x - y) < 1e-9 for x, y in zip(sa, sb)) / len(pairs), 4),
                    f"mean_{sides[0]}": round(sum(sa) / len(sa), 4), f"mean_{sides[1]}": round(sum(sb) / len(sb), 4),
                    "difference": round(sum(diffs) / len(diffs), 4), "difference_ci95": [round(boot[50], 4), round(boot[1949], 4)],
                    "status_mismatches": sum(a["status"] != b["status"] for a, b in pairs),
                    "verdict": ("reproduced" if boot[50] <= 0 <= boot[1949] else "sides disagree") if same_weights else "different weights: not a reproduction test"})
    return {"sides": sides, "difference_is": f"{sides[1]} minus {sides[0]}", "metric_note": "ocr_crop is per-case CER (lower is better); others higher is better",
            "results": out}


def write_sqlite(rows, out):
    db_path = out / "library.sqlite3"
    if db_path.exists():
        db_path.unlink()
    import vision_eval as ve
    db = ve.connect(out)
    db.execute(ve.RESULT_SCHEMA)
    for r in rows:
        label = f"{r['model']}@{r['side']}" + ("" if r["run"] == 1 else f"#run{r['run']}") + \
                ("" if r["mode"] == "image" else " [table only]") + ("" if r["variant"] == "baseline" else f" [{r['variant']}]")
        run_id = f"{r['side']}:{r['run']}:{r['run_id']}"
        db.execute("INSERT OR REPLACE INTO vision_results VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (run_id, r["case_id"], r["task"], label, r["status"], json.dumps(r["prediction"]), json.dumps(r["metrics"]),
                    r["seconds"], r["error"], r["created"]))
    db.commit()
    db.close()


def fmt(v, pct=False):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{100 * v:.1f}%" if pct else f"{v:.3f}"
    return str(v)


def markdown(out, summary, comparison, repro):
    lines = ["# OCR vision evaluation (vision-v1): merged desktop + laptop results", "",
             f"Contract: prompts `{summary['contract']['prompts_sha256'][:12]}`, scorers `{summary['contract']['scorers_sha256'][:12]}`, "
             f"cases v1 `{eval_contract.FROZEN['v1']['cases_sha256'][:12]}`, confirm `{eval_contract.FROZEN['confirm']['cases_sha256'][:12]}`.",
             "Model labels are `model@side [variant]`. Failed cases count as zero. No model graded another model.", ""]
    blocks = {
        "chart_qa": ("Chart questions (ChartQA, relaxed accuracy)", ["correct", "correct_human", "correct_augmented"], True),
        "chart_qa_confirm": ("Chart questions, held-out confirmation set", ["correct", "correct_human", "correct_augmented"], True),
        "table": ("Table transcription (TEDS, cell F1)", ["teds", "teds_structure", "cell_f1", "numeric_recall"], False),
        "table_confirm": ("Table transcription, held-out confirmation set", ["teds", "teds_structure", "cell_f1", "numeric_recall"], False),
        "chart_table": ("Chart data extraction (values within 5%)", ["value_recall", "value_precision", "label_recall"], False),
        "ocr_crop": ("Prose crops (character error rate, lower is better)", ["cer_completed", "numeric_recall", "numeric_precision"], False),
        "page_text": ("Whole pages (word F1)", ["word_f1", "numeric_recall"], False),
    }
    for task, (title, keys, pct) in blocks.items():
        rows = [r for r in summary["results"] if r["task"] == task]
        if not rows:
            continue
        lines += [f"## {title}", "", "| model | cases | failed | " + " | ".join(keys) + " | median s |",
                  "|---|---|---|" + "---|" * len(keys) + "---|"]
        for r in rows:
            lines.append(f"| {r['model']} | {r['cases']} | {r['failed']} | " + " | ".join(fmt(r.get(k), pct) for k in keys) + f" | {fmt(r['median_seconds'])} |")
        lines.append("")
    lay = [r for r in summary["results"] if r["task"] == "layout"]
    if lay:
        lines += ["## Layout (figures and tables, IoU >= 0.5)", "", "| model | figure P | figure R | figure F1 | table P | table R | table F1 |", "|---|---|---|---|---|---|---|"]
        for r in lay:
            lines.append(f"| {r['model']} | " + " | ".join(fmt(r[k].get(m)) for k in ("figure", "table") for m in ("precision", "recall", "f1")) + " |")
        lines.append("")
    if comparison:
        lines += ["## Variants against baseline (paired, same cases)", "",
                  "| model | task | variant | cases | baseline | variant | change | 95% CI | better/worse | test | p | family | p (Holm) | verdict |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in comparison:
            lines.append(f"| {r['model']} | {r['task']} | {r['variant']} | {r['cases']} | {r['baseline']} | {r['variant_score']} | {r['change']:+.4f} | "
                         f"[{r['ci95'][0]}, {r['ci95'][1]}] | {r['better']}/{r['worse']} | {r['test']} | {r['p_value']} | {r['family']} | {r['p_holm']} | {r['verdict_after_correction']} |")
        lines.append("")
    if repro["results"]:
        s0, s1 = repro["sides"]
        lines += [f"## Reproducibility: the same model run on both machines ({repro['difference_is']})", "",
                  f"| model | task | variant | shared cases | same weights | identical answers | identical scores | {s0} | {s1} | difference [95% CI] | verdict |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in repro["results"]:
            lines.append(f"| {r['model']} | {r['task']} | {r['variant']} | {r['shared_cases']} | {'yes' if r['same_weights'] else 'NO'} | "
                         f"{fmt(r['identical_prediction'], True)} | {fmt(r['identical_case_score'], True)} | {r['mean_' + s0]} | {r['mean_' + s1]} | "
                         f"{r['difference']:+.4f} [{r['difference_ci95'][0]}, {r['difference_ci95'][1]}] | {r['verdict']} |")
        lines.append("")
    (out / "MERGED_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("exports", nargs="+", type=Path)
    ap.add_argument("--root", type=Path, required=True, help="a lab root holding evaluation/ (the frozen manifests)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--round2", action="store_true", help="include round-2 rows")
    a = ap.parse_args()
    rows = load(a.exports)
    refuse_mismatches(rows, a.round2)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "evaluation").mkdir(exist_ok=True)
    for spec in eval_contract.FROZEN.values():
        shutil.copy2(a.root / spec["file"], a.out / spec["file"])
    with open(a.out / "merged.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    write_sqlite(rows, a.out)
    import vision_eval as ve
    with contextlib.redirect_stdout(io.StringIO()):
        ve.report(a.out)
        ve.compare(a.out)
    summary = json.loads((a.out / "reports" / "vision-evaluation-summary.json").read_text(encoding="utf-8"))
    summary["contract"] = {k: rows[0][k] for k in CONTRACT_KEYS}
    comparison = json.loads((a.out / "reports" / "vision-variant-comparison.json").read_text(encoding="utf-8"))["results"]
    repro = reproducibility(rows) if len({r["side"] for r in rows}) == 2 else {"sides": [], "results": []}
    (a.out / "reports" / "reproducibility.json").write_text(json.dumps(repro, indent=1), encoding="utf-8")
    markdown(a.out, summary, comparison, repro)
    print(json.dumps({"rows": len(rows), "sides": sorted({r["side"] for r in rows}), "out": str(a.out),
                      "reproducibility_groups": len(repro["results"])}))


if __name__ == "__main__":
    main()
