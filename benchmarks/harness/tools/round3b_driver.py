"""Round 3b driver: the pre-registered confirmation and the supporting arms (docs/round3/PREREG_3B.md), pausable
exactly like round 3 (same control directory, same runners; see round3_driver.py).

  python -X utf8 tools/round3b_driver.py run        # start or continue; waits for a free GPU
  python -X utf8 tools/round3b_driver.py status
  (pause / resume / reclaim: tools/round3_driver.py)

Stages, in order (each marked done in C:/dev/ocr-lab/round3/ when complete):
  parser3b_<backend>   bare parser on the fresh sets at 8,192; budget arms 6,000 and 16,384 on page_text_confirm2;
                       Nemotron Parse double and triple pass on the fresh sets; PaddleOCR official pipeline on the fresh
                       sets; packet latency for that parser
  vlm3b_qwen3vl32b     the 32B comparator on the fresh sets at 8,192 and the 8,744 budget arm on page_text_confirm2;
                       packet latency
  replay_7b            the two unreproduced Qwen2.5-VL 7B groups, rerun on this machine
  legal_gptoss_seeds   the five temperature-1 arms of gpt-oss-20b with two more seeds
  legal_qwen32b_confirm Qwen3 32B on the 60-document reasoning contrast
  stats3b              paired bootstrap, parser report, latency table
  restore              the original port-8001 server
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import round3_driver as r3  # noqa: E402

LAB, CONTROL, PY, HARNESS, REPO, URL = r3.LAB, r3.CONTROL, r3.PY, r3.HARNESS, r3.REPO, r3.URL
LATENCY = REPO / "results" / "vision" / "round3" / "latency.json"
PARSERS = [("nemotronparse", "nemotron-parse"), ("paddleocrvl16", "paddleocrvl"), ("olmocr2", "olmocr2")]
FRESH = ["page_text_confirm3", "table_confirm3"]
PADDLE_PY = "/home/tayle/paddle_venv/bin/python"
PADDLE_SCRIPT = "/mnt/c/dev/test-ocr-work/benchmarks/harness/tools/paddle_pipeline_v3.py"
PADDLE_OUT = LAB / "round3" / "paddle_pipeline_v3.jsonl"


def parser_cmd(backend, tasks, max_tokens=None, mode="single", workers=4):
    cmd = PY + [str(HARNESS / "parser_eval.py"), "--root", str(LAB), "run", "--backend", backend, "--url", URL,
                "--workers", str(workers), "--control-dir", str(CONTROL)]
    for t in tasks:
        cmd += ["--task", t]
    if max_tokens:
        cmd += ["--max-tokens", str(max_tokens)]
    if mode != "single":
        cmd += ["--mode", mode]
    return cmd


def run_steps(stage, steps):
    """steps: list of (name, argv, cwd). Stops at a pause; returns False then."""
    for name, argv, cwd in steps:
        if r3.paused():
            return False
        started = time.time()
        rc = subprocess.run(argv, cwd=cwd).returncode
        r3.log(f"{stage}/{name}: exit {rc} after {time.time() - started:.0f} s")
        if r3.paused():
            return False
    return True


def stage_parser(key, backend):
    stage = f"parser3b_{backend}"
    if r3.done(stage):
        r3.log(f"skip {stage}: done")
        return True
    if not r3.wait_for_gpu():
        return False
    proc = r3.start_server(key)
    if not r3.server_ready():
        r3.stop_server(proc, key)
        r3.mark(stage, ok=False)
        return True
    steps = [("fresh_8192", parser_cmd(backend, FRESH, 8192), HARNESS),
             ("budget_6000", parser_cmd(backend, ["page_text_confirm2"], 6000), HARNESS),
             ("budget_16384", parser_cmd(backend, ["page_text_confirm2"], 16384), HARNESS)]
    if backend == "nemotron-parse":
        steps += [("double", parser_cmd(backend, FRESH, 8192, "double", workers=1), HARNESS),
                  ("triple", parser_cmd(backend, FRESH, 8192, "triple", workers=1), HARNESS)]
    if backend == "paddleocrvl":
        steps += [("official_pipeline", r3.WSL + [PADDLE_PY, PADDLE_SCRIPT, "--manifest", "/mnt/c/dev/ocr-lab/evaluation/vision_cases_v3.json",
                                                  "--root", "/mnt/c/dev/ocr-lab", "--task", "page_text_confirm3", "--task", "table_confirm3",
                                                  "--out", "/mnt/c/dev/ocr-lab/round3/paddle_pipeline_v3.jsonl"], HARNESS),
                  ("import_pipeline", PY + [str(HARNESS / "parser_eval.py"), "--root", str(LAB), "import", "--backend", "paddle-pipeline", "--jsonl", str(PADDLE_OUT)], HARNESS)]
    steps.append(("latency", PY + [str(HARNESS / "tools" / "packet_latency.py"), "--root", str(LAB), "--backend", backend, "--url", URL, "--out", str(LATENCY)], HARNESS))
    ok = run_steps(stage, steps)
    r3.stop_server(proc, key)
    if not ok:
        return False
    r3.mark(stage)
    return True


def stage_vlm():
    stage = "vlm3b_qwen3vl32b"
    if r3.done(stage):
        r3.log(f"skip {stage}: done")
        return True
    if not r3.wait_for_gpu():
        return False
    r3.log("starting the Qwen3-VL 32B AWQ server (the round-1/2 comparator build) on 127.0.0.1:8001")
    proc = subprocess.Popen(r3.WSL + ["bash", r3.RESTORE, "qwen3vl32b"])
    if not r3.server_ready():
        r3.stop_server(proc, "qwen3vl32b")
        r3.mark(stage, ok=False)
        return True
    vlm = PY + [str(HARNESS / "tools" / "vlm_v3.py"), "--root", str(LAB), "--model", "openai:qwen3vl32b", "--control-dir", str(CONTROL), "--workers", "4"]
    steps = [("fresh_8192", vlm + ["--task", "page_text_confirm3", "--task", "table_confirm3", "--max-tokens", "8192"], HARNESS),
             ("budget_8744", vlm + ["--task", "page_text_confirm2", "--max-tokens", "8744"], HARNESS),
             ("latency", PY + [str(HARNESS / "tools" / "packet_latency.py"), "--root", str(LAB), "--vlm", "openai:qwen3vl32b", "--out", str(LATENCY)], HARNESS)]
    ok = run_steps(stage, steps)
    r3.stop_server(proc, "qwen3vl32b")
    if not ok:
        return False
    r3.mark(stage)
    return True


def stage_replay():
    stage = "replay_7b"
    if r3.done(stage):
        return True
    if not r3.wait_for_gpu():
        return False
    ok = run_steps(stage, [("replay", PY + [str(HARNESS / "tools" / "replay_7b.py"), "--root", str(LAB), "--control-dir", str(CONTROL), "--workers", "4"], HARNESS)])
    r3.unload("qwen2.5vl:7b")
    if not ok:
        return False
    r3.mark(stage)
    return True


def legal(stage, model, out, extra):
    if r3.done(stage):
        return True
    if not r3.wait_for_gpu():
        return False
    env = dict(os.environ, OLLAMA_MODEL=model)
    cmd = PY + [str(HARNESS / "tools" / "local_legal_reassessment.py"), "--out", str(out), "--run", "--control-dir", str(CONTROL)] + extra
    if out.exists():
        cmd.append("--resume")
    started = time.time()
    rc = subprocess.run(cmd, cwd=HARNESS, env=env).returncode
    r3.unload(model)
    r3.log(f"{stage}: exit {rc} after {time.time() - started:.0f} s")
    status_file = out / "STATUS.LOCAL_ONLY.json"
    state = json.loads(status_file.read_text(encoding="utf-8")).get("status") if status_file.exists() else None
    if r3.paused() or state == "paused":
        return False
    r3.mark(stage, ok=(rc == 0 and state == "complete"))
    return True


def stage_legal_seeds():
    arms = ["sampling", "definitions", "full_document", "ids", "schema_in_prompt"]
    for seed in (1, 2):
        ok = legal(f"legal_gptoss_seed{seed}", "gpt-oss:20b", r3.LEGAL_OUT / f"gpt-oss-20b-arms-seed{seed}",
                   ["--arms", *arms, "--seed", str(seed), "--full-spans", str(HARNESS / "handoff" / "legal-comparison-24" / "full_spans.json")])
        if not ok:
            return False
    return True


def stage_legal_qwen():
    return legal("legal_qwen32b_confirm", "qwen3:32b", r3.LEGAL_OUT / "qwen3-32b-confirm",
                 ["--confirm", "--pack", str(HARNESS / "handoff" / "legal-confirmation-60")])


def stage_stats():
    run_steps("stats3b", [("stats", PY + [str(HARNESS / "tools" / "round3_stats.py"), "--root", str(LAB), "--out", str(REPO / "results" / "vision" / "round3" / "stats.json")], HARNESS),
                          ("report", PY + [str(HARNESS / "parser_eval.py"), "--root", str(LAB), "report", "--out", str(REPO / "results" / "vision" / "round3" / "parsers.json")], HARNESS)])
    r3.mark("stats3b")


def run():
    r3.STATE.mkdir(parents=True, exist_ok=True)
    r3.log("round 3b driver start")
    if r3.done("restore"):  # round 3 put the original server back; take the card again for 3b
        r3.reclaim()
    for key, backend in PARSERS:
        if not stage_parser(key, backend):
            r3.log("paused")
            return 75
    for fn in (stage_vlm, stage_replay, stage_legal_seeds, stage_legal_qwen):
        if not fn():
            r3.log("paused")
            return 75
    stage_stats()
    r3.restore_original_server()
    r3.log("round 3b complete")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run")
    sub.add_parser("status")
    args = parser.parse_args()
    if args.cmd == "status":
        r3.status()
        return 0
    return run()


if __name__ == "__main__":
    sys.exit(main())
