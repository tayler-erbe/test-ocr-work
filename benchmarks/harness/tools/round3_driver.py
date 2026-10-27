"""Round 3 driver (26 Oct 2026): runs the desktop campaign stage by stage, and can be paused at any moment.

  python -X utf8 tools/round3_driver.py run            # start or continue; waits for a free GPU first
  python -X utf8 tools/round3_driver.py run --smoke    # 3 cases per parser task only, to measure speed
  python -X utf8 tools/round3_driver.py pause          # stop after the request in flight and free the GPU
  python -X utf8 tools/round3_driver.py resume         # clear the pause and continue where it stopped
  python -X utf8 tools/round3_driver.py status         # what is done, what is running, GPU memory

Pause: the shared control directory C:/dev/ocr-lab/round3-control (tools/campaign_control.py, the
cooperative request-boundary pause every runner honours). A pause flag stops dispatch; active requests
drain and are checkpointed; the runner returns. The driver then does the part the runners deliberately do
not: it stops the parser server it started, or unloads the Ollama model it loaded, so the GPU is free.
Resume clears the flag and relaunches the same commands; finished requests, failures included, are skipped.

Stages, in order: three parsers (Nemotron 3.5 Parse, PaddleOCR-VL-1.6, olmOCR-2), gpt-oss-20b legal arms,
gpt-oss-20b 60-document contrast, parser report, restore of the original port-8001 server.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
HARNESS = HERE.parent
REPO = HARNESS.parent.parent
LAB = Path("C:/dev/ocr-lab")
STATE = LAB / "round3"
CONTROL = LAB / "round3-control"  # shared with every runner (--control-dir)
PAUSE = CONTROL / "PAUSE"
LOG = STATE / "driver.log"
WSL = ["wsl", "-d", "Ubuntu-24.04", "-u", "tayle", "--"]
SERVE = "/mnt/c/dev/test-ocr-work/benchmarks/harness/tools/round3_serve.sh"
RESTORE = "/mnt/c/dev/skyrule-fresh/docs/05_platform_and_data_engineering/ocr_bakeoff/serve_ocr_vllm.sh"
URL = "http://127.0.0.1:8001/v1"
OLLAMA = "http://127.0.0.1:11434"
PY = [sys.executable, "-X", "utf8"]
PARSERS = [("nemotronparse", "nemotron-parse", ["page_text", "page_text_confirm2", "table", "table_confirm", "layout"]),
           ("paddleocrvl16", "paddleocrvl", ["page_text", "page_text_confirm2", "table", "table_confirm"]),
           ("olmocr2", "olmocr2", ["page_text", "page_text_confirm2", "table", "table_confirm"])]
LEGAL_MODEL = "gpt-oss:20b"
LEGAL_OUT = REPO / "results" / "legal" / "round3"


def log(msg):
    STATE.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def gpu_used_mib():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=20).stdout
        return int(out.strip().splitlines()[0])
    except Exception:
        return None


def paused():
    return PAUSE.exists()


def wait_for_gpu(limit_mib=3000):
    """The card must be free before a model is loaded (one model on the GPU at a time)."""
    said = False
    while True:
        if paused():
            return False
        used = gpu_used_mib()
        if used is not None and used < limit_mib:
            return True
        if not said:
            log(f"waiting for the GPU: {used} MiB in use (another server is holding it); checking every 30 s")
            said = True
        time.sleep(30)


def done(stage):
    return (STATE / f"done_{stage}").exists()


def mark(stage, ok=True):
    (STATE / (f"done_{stage}" if ok else f"failed_{stage}")).write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")


def server_ready(timeout=1200):
    started = time.time()
    while time.time() - started < timeout:
        try:
            with urllib.request.urlopen(URL + "/models", timeout=5) as r:
                json.load(r)
            return True
        except Exception:
            time.sleep(5)
        if paused():
            return False
    return False


def start_server(key):
    log(f"starting vLLM server {key} on 127.0.0.1:8001")
    return subprocess.Popen(WSL + ["bash", SERVE, key])


def stop_server(proc, key):
    log(f"stopping vLLM server {key}")
    subprocess.run(WSL + ["pkill", "-f", "vllm serve.*--port 8001"], timeout=60)
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
    for _ in range(30):
        used = gpu_used_mib()
        if used is not None and used < 3000:
            break
        time.sleep(2)
    log(f"server {key} stopped; GPU {gpu_used_mib()} MiB")


def run_parser(key, backend, tasks, smoke):
    stage = f"parser_{backend}" + ("_smoke" if smoke else "")
    if done(stage):
        log(f"skip {stage}: done")
        return True
    if not wait_for_gpu():
        return False
    proc = start_server(key)
    if not server_ready():
        log(f"server {key} did not become ready")
        stop_server(proc, key)
        mark(stage, ok=False)
        return True  # move on; the report shows the gap
    cmd = PY + [str(HARNESS / "parser_eval.py"), "--root", str(LAB), "run", "--backend", backend, "--url", URL,
                "--workers", "4", "--control-dir", str(CONTROL)]
    for t in tasks:
        cmd += ["--task", t]
    if smoke:
        cmd += ["--limit", "3"]
    started = time.time()
    rc = subprocess.run(cmd, cwd=HARNESS).returncode
    stop_server(proc, key)
    log(f"{stage}: exit {rc} after {time.time() - started:.0f} s")
    if paused():  # the runner drained and returned; the server above is already stopped
        return False
    mark(stage, ok=(rc == 0))
    return True


def ollama_has(model):
    try:
        with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=10) as r:
            return any(m["name"] == model for m in json.load(r)["models"])
    except Exception:
        return False


def unload(model):
    try:
        req = urllib.request.Request(OLLAMA + "/api/generate", data=json.dumps({"model": model, "keep_alive": 0}).encode(), headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=60).read()
    except Exception:
        pass


def run_legal(confirm):
    stage = "legal_gptoss_" + ("confirm" if confirm else "arms")
    if done(stage):
        log(f"skip {stage}: done")
        return True
    while not ollama_has(LEGAL_MODEL):
        if paused():
            return False
        log(f"waiting for {LEGAL_MODEL} to finish downloading into Ollama; checking every 60 s")
        time.sleep(60)
    if not wait_for_gpu():
        return False
    out = LEGAL_OUT / ("gpt-oss-20b-confirm" if confirm else "gpt-oss-20b-arms")
    env = dict(os.environ, OLLAMA_MODEL=LEGAL_MODEL)
    cmd = PY + [str(HERE / "local_legal_reassessment.py"), "--out", str(out), "--run", "--control-dir", str(CONTROL)]
    if out.exists():
        cmd.append("--resume")
    if confirm:
        cmd += ["--confirm", "--pack", str(HARNESS / "handoff" / "legal-confirmation-60")]
    else:
        cmd += ["--full-spans", str(HARNESS / "handoff" / "legal-comparison-24" / "full_spans.json")]
    started = time.time()
    rc = subprocess.run(cmd, cwd=HARNESS, env=env).returncode
    unload(LEGAL_MODEL)  # the runner leaves the weights loaded; the driver owns that model and frees the GPU
    log(f"{stage}: exit {rc} after {time.time() - started:.0f} s")
    status_file = out / "STATUS.LOCAL_ONLY.json"
    state = json.loads(status_file.read_text(encoding="utf-8")).get("status") if status_file.exists() else None
    if paused() or state == "paused":
        return False
    mark(stage, ok=(rc == 0 and state == "complete"))
    return True


def run_report():
    out = REPO / "results" / "vision" / "round3" / "parsers.json"
    rc = subprocess.run(PY + [str(HARNESS / "parser_eval.py"), "--root", str(LAB), "report", "--out", str(out)], cwd=HARNESS).returncode
    log(f"parser report: exit {rc} -> {out}")


def restore_original_server():
    if done("restore"):
        return
    log("restoring the original port-8001 server (Qwen3-VL 32B AWQ) as it was before round 3")
    subprocess.Popen(WSL + ["bash", RESTORE, "qwen3vl32b"], creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    mark("restore")


def status():
    STATE.mkdir(parents=True, exist_ok=True)
    print("paused:", paused())
    print("GPU MiB used:", gpu_used_mib())
    print("stages:", sorted(p.name for p in STATE.glob("done_*")) + sorted(p.name for p in STATE.glob("failed_*")))
    try:
        import sqlite3
        db = sqlite3.connect(f"file:{LAB / 'library.sqlite3'}?mode=ro", uri=True)
        for model, task, n, ok, sec in db.execute("SELECT model, task, COUNT(*), SUM(status='complete'), AVG(seconds) FROM vision_results WHERE model LIKE 'parser:%' GROUP BY model, task"):
            print(f"  {model:<24} {task:<20} {n:>4} rows, {ok} complete, {sec:.1f} s/case")
    except Exception as exc:
        print("  (no parser rows yet:", type(exc).__name__ + ")")
    for d in sorted(LEGAL_OUT.glob("*")) if LEGAL_OUT.exists() else []:
        events = d / "events.LOCAL_ONLY.jsonl"
        n = sum(1 for _ in events.open(encoding="utf-8")) if events.exists() else 0
        print(f"  {d.name}: {n} requests done")
    if LOG.exists():
        print("log tail:")
        print("\n".join(LOG.read_text(encoding="utf-8").splitlines()[-6:]))


def run(smoke):
    STATE.mkdir(parents=True, exist_ok=True)
    log("driver start" + (" (smoke)" if smoke else ""))
    for key, backend, tasks in PARSERS:
        if not run_parser(key, backend, tasks, smoke):
            log("paused; run `round3_driver.py resume` to continue")
            return 75
    if smoke:
        run_report()
        log("smoke done; measured seconds per case are in `status`")
        return 0
    for confirm in (False, True):
        if not run_legal(confirm):
            log("paused; run `round3_driver.py resume` to continue")
            return 75
    run_report()
    restore_original_server()
    log("round 3 desktop campaign complete")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--smoke", action="store_true")
    sub.add_parser("pause")
    rs = sub.add_parser("resume")
    rs.add_argument("--smoke", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args()
    if args.cmd == "pause":
        CONTROL.mkdir(parents=True, exist_ok=True)
        PAUSE.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
        print("pause requested; the running stage drains its active requests, then the driver frees the GPU")
        return 0
    if args.cmd == "status":
        status()
        return 0
    if args.cmd == "resume" and PAUSE.exists():
        PAUSE.unlink()
    return run(args.smoke)


if __name__ == "__main__":
    sys.exit(main())
