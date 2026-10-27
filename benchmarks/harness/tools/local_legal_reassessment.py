"""The Nemotron reassessment arms, run against a LOCAL Ollama model (round 3, 26 Oct 2026).

Same 24-case public pack, same eight arms, same frozen scorer and the same request builder as
tools/nemotron_reassessment.py (imported, not copied). Only the transport differs: Ollama's native
/api/chat on 127.0.0.1, which is the only way to control thinking for local models. With --confirm it
runs the paired reasoning-on/off contrast on the frozen 60-document pack instead, exactly like
tools/run_nemotron_confirmation.py (alternating arm order, 16k budget, temperature 0).

Thinking control differs per model family and is recorded in every row:
  qwen3 / nemotron   think=false (off) or think=true (on)
  gpt-oss            cannot switch reasoning off; "off" arms run think=low and "on" arms think=high
Public data only. Raw final answers stay in the new local output directory; thinking text is not saved.

  set OLLAMA_MODEL=gpt-oss:20b
  python -X utf8 tools/local_legal_reassessment.py --out <new dir> [--context N] --full-spans handoff/legal-comparison-24/full_spans.json --run
  python -X utf8 tools/local_legal_reassessment.py --confirm --pack <60-doc pack dir> --out <new dir> --run
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
from nemotron_reassessment import ARMS, make_body, sha, summarize  # noqa: E402
from nim_evaluation import frozen  # noqa: E402
from campaign_control import paused, durable_json, checkpoint_rows, append_row, acquire_lock

OLLAMA = "http://127.0.0.1:11434"
CONTEXT = 32768  # default; the run records the value actually used (--context)
# Default context per family: the published window, capped where the KV cache would not fit a 32 GB card.
DEFAULT_CONTEXT = {"gpt-oss": 65536, "nemotron": 65536, "qwen3": 40960}
PACK24 = REPO / "handoff" / "legal-comparison-24"


def ollama(path, payload=None, timeout=1800):
    request = urllib.request.Request(OLLAMA + path, data=None if payload is None else json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def think_value(model, on):
    """What to send in Ollama's `think` field for this family. gpt-oss only has levels."""
    if model.startswith("gpt-oss"):
        return "high" if on else "low"
    return bool(on)


def translate(body, model, context=CONTEXT, seed=None):
    """OpenAI-style body from make_body -> Ollama /api/chat body. Nothing else changes."""
    fmt = body["response_format"]
    native = {"model": model, "messages": body["messages"], "stream": False, "keep_alive": "10m",
              "think": think_value(model, body["chat_template_kwargs"]["enable_thinking"]),
              "format": fmt["json_schema"]["schema"] if fmt["type"] == "json_schema" else "json",
              "options": {"temperature": body["temperature"], "top_p": body["top_p"],
                          "num_predict": body["max_tokens"], "num_ctx": context}}
    if seed is not None:
        native["options"]["seed"] = seed  # repeat runs of the sampling arms; recorded in PLAN.json
    return native


def measure_prompt(model, body, context):
    """Exact prompt length by the model's own tokenizer: a one-token prefill, no reasoning, nothing scored.
    Replaces the byte guard, which rejected token-feasible requests (docs/round3/LOCAL_CONTEXT_PREFLIGHT.json)."""
    native = translate(body, model, context)
    native["think"] = think_value(model, False)
    native["options"]["num_predict"] = 1
    raw = ollama("/api/chat", native, timeout=600)
    return raw.get("prompt_eval_count")


def residency(model):
    """Where the loaded weights sit (Ollama /api/ps). A run counts only when everything is on the GPU."""
    for m in ollama("/api/ps", timeout=20).get("models", []):
        if model in (m.get("name"), m.get("model")):
            return {"size": m.get("size"), "size_vram": m.get("size_vram"), "context_length": m.get("context_length"),
                    "fully_on_gpu": bool(m.get("size")) and m.get("size_vram") == m.get("size")}
    return {"fully_on_gpu": False, "note": "model not listed as loaded"}


def snapshot(model, context=CONTEXT):
    tags = ollama("/api/tags", timeout=20)["models"]
    tag = next((m for m in tags if m["name"] == model), None)
    if tag is None:
        raise SystemExit("Model is not installed in Ollama: " + model)
    info = {"model": tag, "runtime": ollama("/api/version", timeout=20), "context": context,
            "thinking_control": "levels low/high" if model.startswith("gpt-oss") else "boolean"}
    return info, sha(info)


def call(model, body, context=CONTEXT, seed=None):
    native = translate(body, model, context, seed)
    raw = ollama("/api/chat", native)
    message = raw.get("message", {})
    return {"content": message.get("content"), "done_reason": raw.get("done_reason"),
            "reasoning_present": bool(message.get("thinking")),
            "usage": {"prompt_tokens": raw.get("prompt_eval_count"), "completion_tokens": raw.get("eval_count")},
            "think_sent": native["think"]}


def load_pack24(arms, db_path, full_spans_path):
    requests = json.loads((PACK24 / "requests.json").read_text(encoding="utf8"))
    references = json.loads((PACK24 / "references.DO_NOT_SEND_TO_MODEL.json").read_text(encoding="utf8"))
    assert len(requests) == len(references) == 24
    for request, ref in zip(requests, references):
        assert request["case_id"] == ref["case"]["id"]
        assert ref["case"]["dataset"] in ("cuad", "contractnli")
        assert request["request_sha256"] == sha({"messages": request["messages"], "schema": request["schema"]})
        request["question"] = request["messages"][-1]["content"].split("\nQuestion: ", 1)[1].split("\nSOURCE:\n", 1)[0]
    full = {}
    if any(ARMS[a].get("full") for a in arms):
        if full_spans_path:
            full = json.loads(Path(full_spans_path).read_text(encoding="utf8"))
        elif db_path:
            db = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
            for ref in references:
                case = ref["case"]
                dataset = db.execute("SELECT dataset FROM documents WHERE id=?", (case["doc_id"],)).fetchone()
                if not dataset or dataset[0] not in ("cuad", "contractnli"):
                    raise ValueError("Non-public or missing source refused")
                full[case["id"]] = json.loads(db.execute("SELECT spans FROM document_spans WHERE doc_id=?", (case["doc_id"],)).fetchone()[0])
            db.close()
        else:
            raise SystemExit("The full_document arm needs --db or --full-spans; or drop it with --arms")
        missing = [r["case_id"] for r in requests if r["case_id"] not in full]
        if missing:
            raise SystemExit(f"full spans missing for {len(missing)} cases")
    return requests, references, full


def load_pack60(pack):
    receipt = json.loads((pack / "RECEIPT.json").read_text(encoding="utf8"))
    for name, digest in receipt["files"].items():
        assert hashlib.sha256((pack / name).read_bytes()).hexdigest() == digest, name
    requests = json.loads((pack / "requests.json").read_text(encoding="utf8"))
    references = json.loads((pack / "references.DO_NOT_SEND_TO_MODEL.json").read_text(encoding="utf8"))
    assert len(requests) == len(references) == 60
    assert len({r["case"]["doc_id"] for r in references}) == 60
    for request, reference in zip(requests, references):
        assert request["case_id"] == reference["case"]["id"]
        assert reference["case"]["dataset"] in ("cuad", "contractnli")
        assert request["request_sha256"] == sha({"messages": request["messages"], "schema": request["schema"]})
    return receipt, requests, references


def retained_result(result):
    """Persist final output and stop metadata before validation can fail. No thinking text."""
    return {"final_answer": result["content"],
            "finish_reason": "length" if result["done_reason"] == "length" else result["done_reason"],
            "usage": result["usage"], "reasoning_present": result["reasoning_present"],
            "think_sent": result["think_sent"]}


def score_row(scorer, request, ref, config, visible, result):
    row = {"final_answer": result["content"], "finish_reason": "stop" if result["done_reason"] == "stop" else result["done_reason"],
           "usage": result["usage"], "reasoning_present": result["reasoning_present"], "think_sent": result["think_sent"]}
    if result["done_reason"] != "stop":
        raise ValueError("non_stop_generation")
    prediction = json.loads(result["content"])
    if config.get("ids") and request["task"] == "extraction":
        evidence = scorer.validate_response(prediction, visible, "ids")
    else:
        evidence = scorer.validate_response(prediction, visible, request["task"])
    row.update(status="complete", metrics=scorer.score(ref["case"], prediction, evidence, visible))
    if request["task"] == "extraction":
        row["presence_correct"] = bool(evidence) == bool(json.loads(ref["case"]["gold"])["answers"])
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=list(ARMS))
    parser.add_argument("--db", type=Path, help="lab database holding document_spans (full_document arm)")
    parser.add_argument("--full-spans", type=Path, help="JSON {case_id: spans} exported from the lab database (full_document arm)")
    parser.add_argument("--confirm", action="store_true", help="60-document reasoning on/off contrast instead of the 24-case arms")
    parser.add_argument("--pack", type=Path, help="frozen 60-document pack directory (with --confirm)")
    parser.add_argument("--context", type=int, help="num_ctx sent to Ollama; default per family (DEFAULT_CONTEXT), recorded in PLAN.json")
    parser.add_argument("--control-dir", type=Path, required=True, help="Shared campaign pause flag directory")
    parser.add_argument("--seed", type=int, help="sampling seed for repeat runs of the temperature-1 arms (new output directory)")
    parser.add_argument("--resume", action="store_true", help="Continue same-plan journal, never rerun completed failures")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if paused(args.control_dir):
        print("PAUSED: no inference or model loading performed")
        return
    acquire_lock(args.out.parent / (hashlib.sha256(str(args.out.resolve()).encode()).hexdigest() + ".LOCAL_ONLY.lock"))
    model = os.environ.get("OLLAMA_MODEL")
    if not model:
        raise SystemExit("Set OLLAMA_MODEL to the exact Ollama tag, e.g. gpt-oss:20b")
    context = args.context or next((v for k, v in DEFAULT_CONTEXT.items() if model.startswith(k)), CONTEXT)
    scorer = frozen()
    builder_sha = hashlib.sha256((HERE / "nemotron_reassessment.py").read_bytes()).hexdigest()
    script_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    scorer_sha = hashlib.sha256((REPO / "protocols/evaluation_v3.py").read_bytes()).hexdigest()

    if args.confirm:
        if not args.pack:
            raise SystemExit("--confirm needs --pack")
        receipt, requests, references = load_pack60(args.pack)
        arms = {"off_16000": {"thinking": False, "budget": 16000, "temperature": 0, "top_p": 1},
                "on_16000": {"thinking": True, "budget": 16000, "temperature": 0, "top_p": 1}}
        plan = {"purpose": "fixed reasoning control on a local model; no selection or tuning on these cases",
                "arms": arms, "pack_receipt_sha256": sha(receipt), "cases": 60, "documents": 60,
                "limitations": receipt["limitations"], "full": {}}
        schedule = [(request, ref, name, arms[name], ref["visible"])
                    for index, (request, ref) in enumerate(zip(requests, references))
                    for name in (list(arms) if index % 2 == 0 else list(reversed(arms)))]
    else:
        requests, references, full = load_pack24(args.arms, args.db, args.full_spans)
        plan = {"role": "exploratory; 24 previously exposed cases, not promotion evidence",
                "arms": {a: ARMS[a] for a in args.arms}, "case_ids": [r["case_id"] for r in requests],
                "requests_sha256": sha(requests), "references_sha256": sha(references),
                "full_sources_sha256": sha(full) if full else None}
        schedule = [(request, ref, arm, ARMS[arm], full[request["case_id"]] if ARMS[arm].get("full") else ref["visible"])
                    for request, ref in zip(requests, references) for arm in args.arms]
    plan.update({"model": "ollama/" + model, "transport": "ollama native /api/chat on 127.0.0.1, think field per family",
                 "thinking_control": "levels low/high" if model.startswith("gpt-oss") else "boolean",
                 "comparison_limits": "GPT-OSS contrasts low versus high reasoning, never off versus on. Local versus hosted runs confound checkpoint, quantization, runtime and context unless independently matched. Context fit is measured per request with the model's own tokenizer (one-token prefill); a request whose measured prompt plus budget exceeds the context is recorded as context_exceeded, never silently truncated, and is not model-quality evidence.",
                 "context": context, "context_guard": "measured prompt tokens + budget + 64 <= context", "seed": args.seed,
                 "script_sha256": script_sha, "request_builder_sha256": builder_sha, "scorer_sha256": scorer_sha})
    if args.run:
        info, digest = snapshot(model, context)
        plan["deployment_snapshot"] = info
        plan["deployment_snapshot_sha256"] = digest
    rows = checkpoint_rows(args.out, plan, args.resume)
    if args.run:  # load once up front: everything must sit on the GPU or the run does not count (no request is in flight here)
        ollama("/api/chat", {"model": model, "messages": [{"role": "user", "content": "ok"}], "stream": False, "keep_alive": "10m",
                             "think": think_value(model, False), "options": {"num_predict": 1, "num_ctx": context}}, timeout=1800)
        plan["residency"] = residency(model)
        durable_json(args.out / "PLAN.json", plan)
        if not plan["residency"]["fully_on_gpu"]:
            raise SystemExit("Model is not fully resident on the GPU at this context; lower --context or stop: " + json.dumps(plan["residency"]))
    completed = {(row["arm"], row["case_id"]) for row in rows}
    expected = {(arm, request["case_id"]) for request, _, arm, _, _ in schedule}
    if not completed <= expected:
        raise ValueError("Checkpoint contains attempts outside the schedule")
    for request, ref, arm, config, visible in schedule:
        if paused(args.control_dir):
            break
        if (arm, request["case_id"]) in completed:
            continue
        body = make_body(request, config, model, visible if config.get("full") else None)
        if not args.run:
            continue
        row = {"arm": arm, "case_id": request["case_id"], "dataset": ref["case"]["dataset"], "request_sha256": sha(body),
               "status": "failed", "metrics": {"correct": False, "evidence_f1": 0},
               "source_spans": len(visible), "source_bytes": sum(len(s["text"].encode()) for s in visible)}
        durable_json(args.out / "IN_FLIGHT.LOCAL_ONLY.json", {"arm": arm, "case_id": request["case_id"], "request_sha256": sha(body)})
        started = time.perf_counter()
        try:
            tokens = measure_prompt(model, body, context)
            row["prompt_tokens_measured"] = tokens
            # Ollama truncates a prompt longer than num_ctx and then reports the truncated count, which lands within
            # a few tokens of num_ctx; every budget here is >= 2000 tokens, so a truncated prefill can never pass.
            if tokens is None or tokens >= context - 256 or tokens + config["budget"] + 64 > context:
                raise ValueError("context_exceeded")
            result = call(model, body, context, args.seed)
            row.update(retained_result(result))
            row.update(score_row(scorer, request, ref, config, visible, result))
        except urllib.error.URLError:
            row["error_type"] = "ServiceError"
        except Exception as exc:  # failures stay in the denominator
            row["error_type"] = type(exc).__name__
            if isinstance(exc, ValueError) and str(exc) in ("context_exceeded", "non_stop_generation"):
                row["error_code"] = str(exc)
        row["seconds"] = time.perf_counter() - started
        rows.append(row)
        append_row(args.out, row)
        (args.out / "IN_FLIGHT.LOCAL_ONLY.json").unlink()
        durable_json(args.out / "summary.json", summarize(rows))
        print(json.dumps({k: row.get(k) for k in ("arm", "dataset", "status", "error_code", "seconds")}), flush=True)
    state = {"status": "complete" if len(rows) == len(schedule) else "paused" if paused(args.control_dir) else "planned", "planned_requests": len(schedule), "executed": len(rows), "plan_sha256": sha(plan)}
    durable_json(args.out / "STATUS.LOCAL_ONLY.json", state)
    print(json.dumps(state))


if __name__ == "__main__":
    main()
