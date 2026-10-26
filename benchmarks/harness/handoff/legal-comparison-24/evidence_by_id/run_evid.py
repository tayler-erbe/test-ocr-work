"""Evidence-by-ID arms on the 24-case public legal pack (exploratory; all 24 cases were seen before).

Arms (new labelled configurations; every case stays in the denominator; no retries):
  id_x      excerpts (the pack's visible spans), model selects sentence/clause block IDs, code copies text
  trim_x    excerpts, model selects block ID + exact first/last words; code locates them (exact, unique) and copies
  two_x     excerpts, stage 1 outcome only, stage 2 (only if 'found') block IDs
  id_full   whole public document (where it fits the model context), block IDs, full-review outcome allowed
  trim_full whole public document, anchors

Model-facing text: excerpt spans are parsed from the pack's requests.json messages (the only model-input file);
whole documents come from the public CUAD / ContractNLI files. references.DO_NOT_SEND_TO_MODEL.json is read only
after the model call, for scoring and the logged coverage diagnostics.

Scoring: accepted evidence is converted to the frozen response shape and scored with the UNCHANGED
frozen_evaluation_v3.validate_response/score. Raw answers stay in ./local (git-ignored).

  python run_evid.py run --model qwen3vl32b --arm id_x
  python run_evid.py summarise
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
ROOT = PACK.parents[1]
LOCAL = HERE / "local"
BASELINE_LOCAL = Path("C:/dev/test-ocr-work-legal/handoff/legal-comparison-24/desktop_results/local")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PACK / "desktop_results"))
import evidence_by_id as E  # noqa: E402
import run_desktop as RD  # noqa: E402  (frozen scorer loader, model clients, whole-document spans, token counts)

ARMS = {"id_x": ("ids", False, False), "trim_x": ("anchors", False, False), "two_x": ("ids", False, True),
        "id_full": ("ids", True, False), "trim_full": ("anchors", True, False)}
MAX_TOKENS = 2000
LINE = re.compile(r"^\[(s\d+)\] (.*)$")


def excerpt_spans(request):
    """Spans exactly as the model saw them in the pack request (pseudo offsets; scoring uses the references)."""
    body = request["messages"][1]["content"].split("\nSOURCE:\n", 1)[1]
    spans, pos = [], 0
    for line in body.split("\n"):
        m = LINE.match(line)
        if not m:
            raise ValueError(f"unexpected source line in {request['case_id']}: {line[:60]!r}")
        spans.append({"id": m.group(1), "text": m.group(2), "start": pos, "end": pos + len(m.group(2))})
        pos += len(m.group(2)) + 1
    return spans


def char_pr(case, prediction, visible):
    """Character-level evidence precision/recall against the union of CUAD gold answers (diagnostic)."""
    gold = json.loads(case["gold"])["answers"]
    want = {a["answer_start"] + i for a in gold for i, ch in enumerate(a["text"]) if not ch.isspace()}
    lookup = {s["id"]: s for s in visible}
    got = set()
    for m in prediction.get("matches", []):
        s = lookup[m["id"]]
        off = s["text"].find(m["quote"])
        if off >= 0:
            got |= {s["start"] + off + i for i, ch in enumerate(m["quote"]) if not ch.isspace()}
    if not want and not got:
        return None, None
    p = len(got & want) / len(got) if got else None
    r = len(got & want) / len(want) if want else None
    return p, r


def item_validity(store, raw_items, selection):
    """Per-item check, independent of whole-response acceptance (diagnostic)."""
    if not isinstance(raw_items, list):
        return None
    ok = 0
    for it in raw_items:
        try:
            E._items(store, [it], selection)
            ok += 1
        except E.EvidenceError:
            pass
    return (ok / len(raw_items)) if raw_items else None


def run(model, arm):
    sc = RD.scorer()
    reqs, refs = RD.load()
    selection, full, two_stage = ARMS[arm]
    out_dir = LOCAL / f"{model.replace(':', '_')}__{arm}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for q, r in zip(reqs, refs):
        case = r["case"]
        task = case["task"]
        if task == "nli" and arm not in ("id_x", "id_full"):
            continue
        path = out_dir / (q["request_sha256"][:16] + ".json")
        if path.exists():
            continue
        if full:
            spans = RD.full_spans(case, sc)
            visible_for_scoring = spans
        else:
            spans = excerpt_spans(q)
            visible_for_scoring = r["visible"]
            assert [s["text"] for s in spans] == [s["text"] for s in r["visible"]], "parsed excerpt differs from scoring spans"
        store = E.SourceStore(case["id"], spans)
        doc_len = max((s["end"] for s in RD.full_spans(case, sc)), default=0)
        rec = {"case_id": q["case_id"], "task": task, "model": model, "arm": arm, "selection": selection, "full_document": full,
               "two_stage": two_stage, "blocks": len(store.block_ids), "max_tokens": MAX_TOKENS, "think_requested": False,
               "context_limit": RD.CTX[model],
               # coverage measured before the model call
               "source_coverage": round(E.source_coverage(r["visible"] if not full else spans, doc_len), 4) if not full else 1.0}
        if task == "extraction":
            rec["reference_coverage"] = E.reference_coverage(visible_for_scoring, json.loads(case["gold"])["answers"])
        if task == "nli":
            messages, schema = E.build_nli_request(store, case["question"])
        elif two_stage:
            messages, schema = E.build_presence_request(store, case["question"], full)
        else:
            messages, schema = E.build_field_request(store, case["question"], full, selection)
        need = RD.n_tokens(model, messages)
        rec["prompt_tokens_est"] = need
        if need + MAX_TOKENS > RD.CTX[model]:
            rec.update(status="not_run_does_not_fit")
            path.write_text(json.dumps(rec, indent=1), encoding="utf-8")
            print(q["case_id"][:60], "not run (does not fit)", flush=True)
            continue
        calls, error, prediction, outcome, raw_items = [], None, None, None, None
        try:
            res = RD.call(model, messages, schema, MAX_TOKENS, False)
            calls.append(res)
            if res.get("error"):
                raise RuntimeError(res["error"])
            if res.get("finish") == "length":
                raise E.EvidenceError("Truncated generation")
            parsed = json.loads(res["content"])
            if task == "nli":
                raw_items = parsed.get("evidence") if isinstance(parsed, dict) else None
                label, items = E.validate_nli(store, parsed)
                prediction = E.to_frozen_nli(label, items)
                outcome = label
            elif two_stage:
                outcome = E.validate_presence(parsed, full)
                if outcome == "found":
                    m2, s2 = E.build_evidence_request(store, case["question"], selection)
                    res2 = RD.call(model, m2, s2, MAX_TOKENS, False)
                    calls.append(res2)
                    if res2.get("finish") == "length":
                        raise E.EvidenceError("Truncated generation (stage 2)")
                    p2 = json.loads(res2["content"])
                    raw_items = p2.get("evidence") if isinstance(p2, dict) else None
                    items = E.validate_evidence_only(store, p2, selection)
                    result = E.FieldResult("found", evidence=items, accepted=True)
                else:
                    result = E.FieldResult(outcome, accepted=outcome != "insufficient_evidence")
                prediction = E.to_frozen_prediction(store, result)
            else:
                raw_items = parsed.get("evidence") if isinstance(parsed, dict) else None
                result = E.validate_field(store, parsed, full, selection)
                outcome = result.outcome
                prediction = E.to_frozen_prediction(store, result)
        except (E.EvidenceError, json.JSONDecodeError, RuntimeError, KeyError, TypeError) as e:
            error = f"{type(e).__name__}: {e}"[:400]
        metrics = {"correct": False, "evidence_f1": 0.0}
        diag = {"outcome": outcome, "item_validity": item_validity(store, raw_items, selection) if task == "extraction" else None}
        if prediction is not None and not error:
            if task == "extraction":
                diag["copy_ambiguous_spans"] = E.copy_ambiguities(store, prediction)
            try:
                evidence = sc.validate_response(prediction, visible_for_scoring, task)
                metrics = sc.score(case, prediction, evidence, visible_for_scoring)
            except Exception as e:
                error = f"FrozenValidation: {e}"
        gold = json.loads(case["gold"])
        if task == "extraction":
            diag["gold_absent"] = not gold["answers"]
            diag["predicted_absent"] = outcome is not None and outcome != "found"
            if prediction is not None and not error:
                diag["char_precision"], diag["char_recall"] = char_pr(case, prediction, visible_for_scoring)
        else:
            diag["gold_label"], diag["predicted_label"] = gold["label"], outcome
            diag["gold_absent"], diag["predicted_absent"] = not gold["ids"], outcome == "NotMentioned"
            if prediction is not None and not error:
                a, b = set(prediction["ids"]), set(gold["ids"])
                diag["id_precision"] = len(a & b) / len(a) if a else None
                diag["id_recall"] = len(a & b) / len(b) if b else None
        rec.update(status="failed" if error else "ok", error=error, metrics=metrics, diagnostics=diag, calls=calls,
                   finish=[c.get("finish") for c in calls], seconds=round(sum(c.get("seconds") or 0 for c in calls), 2),
                   output_tokens=sum(((c.get("usage") or {}).get("eval_count") or (c.get("usage") or {}).get("completion_tokens") or 0) for c in calls),
                   reasoning_observed=any((c.get("reasoning_chars") or 0) > 0 or c.get("think_tag") for c in calls))
        path.write_text(json.dumps(rec, indent=1), encoding="utf-8")
        print(q["case_id"][:55], rec["status"], outcome, metrics.get("correct"), round(metrics.get("evidence_f1") or 0, 3), rec["seconds"], (error or "")[:80], flush=True)


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def summarise():
    rows = []
    for d in sorted(LOCAL.glob("*__*")):
        recs = [json.loads(p.read_text(encoding="utf-8")) for p in d.glob("*.json")]
        if not recs:
            continue
        model, arm = recs[0]["model"], recs[0]["arm"]
        for task, name in (("extraction", "CUAD"), ("nli", "NLI")):
            rs = [x for x in recs if x["task"] == task]
            if not rs:
                continue
            ran = [x for x in rs if x.get("status") != "not_run_does_not_fit"]
            ok = [x for x in ran if x["status"] == "ok"]
            row = {"model": model, "arm": arm, "task": name, "cases": len(rs), "run": len(ran), "not_run_does_not_fit": len(rs) - len(ran),
                   "strict_correct": sum(bool(x["metrics"].get("correct")) for x in ran),
                   "request_accepted": len(ok), "failed": len(ran) - len(ok),
                   "truncated": sum("length" in (x.get("finish") or []) for x in ran),
                   "mean_evidence_f1": _mean([x["metrics"].get("evidence_f1", 0.0) for x in ran]),
                   "presence_absence_correct": sum(x["diagnostics"].get("gold_absent") == x["diagnostics"].get("predicted_absent")
                                                   for x in ok if x["diagnostics"].get("outcome") is not None),
                   "presence_absence_scored": sum(x["diagnostics"].get("outcome") is not None for x in ok),
                   "reasoning_observed": sum(bool(x.get("reasoning_observed")) for x in ran),
                   "median_seconds": sorted(x.get("seconds") or 0 for x in ran)[len(ran) // 2] if ran else None,
                   "mean_output_tokens": _mean([x.get("output_tokens") for x in ran]),
                   "errors": sorted({(x.get("error") or "").split(":")[0] for x in ran if x.get("error")})}
            if task == "extraction":
                row["mean_item_validity"] = _mean([x["diagnostics"].get("item_validity") for x in ran])
                row["mean_char_precision"] = _mean([x["diagnostics"].get("char_precision") for x in ok])
                row["mean_char_recall_positives"] = _mean([x["diagnostics"].get("char_recall") for x in ok if not x["diagnostics"].get("gold_absent")])
                row["outcomes"] = {}
                for x in ok:
                    o = x["diagnostics"].get("outcome")
                    row["outcomes"][o] = row["outcomes"].get(o, 0) + 1
            else:
                row["mean_id_precision"] = _mean([x["diagnostics"].get("id_precision") for x in ok])
                row["mean_id_recall"] = _mean([x["diagnostics"].get("id_recall") for x in ok])
                conf = {}
                for x in ok:
                    k = f"{x['diagnostics'].get('gold_label')}->{x['diagnostics'].get('predicted_label')}"
                    conf[k] = conf.get(k, 0) + 1
                row["label_confusion"] = conf
            rows.append(row)
    (HERE / "summary.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    for r in rows:
        print(json.dumps(r))
    paired()


def paired():
    """Per-case strict outcome against the desktop baseline arms on the same questions (exploratory)."""
    if not BASELINE_LOCAL.exists():
        print("baseline records not found; paired comparison skipped")
        return
    def load(d):
        return {json.loads(p.read_text(encoding="utf-8"))["case_id"]: json.loads(p.read_text(encoding="utf-8")) for p in d.glob("*.json")}
    pairs = {("qwen3vl32b", "id_x"): "qwen3vl32b__baseline", ("qwen3vl32b", "trim_x"): "qwen3vl32b__baseline",
             ("qwen3:32b", "id_x"): "qwen3_32b__baseline", ("qwen3:32b", "trim_x"): "qwen3_32b__baseline",
             ("qwen3:32b", "two_x"): "qwen3_32b__baseline", ("qwen3:32b", "id_full"): "qwen3_32b__fulldoc",
             ("qwen3:32b", "trim_full"): "qwen3_32b__fulldoc"}
    out = []
    for (model, arm), base in pairs.items():
        d = LOCAL / f"{model.replace(':', '_')}__{arm}"
        if not d.exists() or not (BASELINE_LOCAL / base).exists():
            continue
        new, old = load(d), load(BASELINE_LOCAL / base)
        for task in ("extraction", "nli"):
            keys = [k for k in new if new[k]["task"] == task and k in old
                    and new[k].get("status") != "not_run_does_not_fit" and old[k].get("status") != "not_run_does_not_fit"]
            if not keys:
                continue
            b = sum(bool(new[k]["metrics"].get("correct")) and not old[k]["metrics"].get("correct") for k in keys)
            c = sum(not new[k]["metrics"].get("correct") and bool(old[k]["metrics"].get("correct")) for k in keys)
            out.append({"model": model, "arm": arm, "vs": base, "task": task, "paired_cases": len(keys),
                        "new_correct": sum(bool(new[k]["metrics"].get("correct")) for k in keys),
                        "baseline_correct": sum(bool(old[k]["metrics"].get("correct")) for k in keys),
                        "fixed": b, "broken": c, "exact_mcnemar_p": mcnemar(b, c),
                        "new_failed": sum(new[k]["status"] != "ok" for k in keys), "baseline_failed": sum(old[k]["status"] != "ok" for k in keys)})
    (HERE / "paired.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for r in out:
        print(json.dumps(r))


def mcnemar(b, c):
    from math import comb
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return round(min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n), 4)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--model", required=True, choices=sorted(RD.CTX))
    r.add_argument("--arm", required=True, choices=sorted(ARMS))
    sp.add_parser("summarise")
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.model, a.arm)
    else:
        summarise()


if __name__ == "__main__":
    main()
