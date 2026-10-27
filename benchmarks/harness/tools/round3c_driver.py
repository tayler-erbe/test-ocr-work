"""Round 3b follow-up (3c): remove two harness-error runs and rerun them correctly. Runs after round3b_driver.py.

Why: in 3b the 16,384-token recovery arm was rejected by every parser server (HTTP 400: the served context window
is 16,384, so prompt plus budget cannot fit) and the Nemotron Parse double/triple passes died on a missing import
before any model call. Neither produced a model output, so those rows are harness errors, not model failures.
They are deleted (logged in results/vision/round3/PURGED.json) and rerun: the recovery arm at 12,288 tokens, the
multipass modes as written. The pre-registration records this amendment.

  python -X utf8 tools/round3c_driver.py run
"""
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import round3_driver as r3  # noqa: E402
import round3b_driver as r3b  # noqa: E402

PURGE_ERRORS = ("HTTPError: HTTP Error 400", "NameError: name 'os' is not defined")
PURGED = r3.REPO / "results" / "vision" / "round3" / "PURGED.json"


def purge():
    db = sqlite3.connect(str(r3.LAB / "library.sqlite3"))
    purged = []
    for run_id, model, config in db.execute("SELECT id, model, config FROM runs WHERE model LIKE 'parser:%'").fetchall():
        rows = db.execute("SELECT status, error FROM vision_results WHERE run_id=?", (run_id,)).fetchall()
        if not rows:
            continue
        if all(st == "failed" and err and err.startswith(PURGE_ERRORS) for st, err in rows):
            cfg = json.loads(config)
            purged.append({"run_id": run_id, "model": model, "task": cfg.get("task"), "max_tokens": cfg.get("max_tokens"), "mode": cfg.get("mode"),
                           "rows": len(rows), "error": rows[0][1][:80], "reason": "harness error before any model output; rerun in round 3c"})
            db.execute("DELETE FROM vision_results WHERE run_id=?", (run_id,))
            db.execute("DELETE FROM runs WHERE id=?", (run_id,))
    db.commit()
    db.close()
    PURGED.parent.mkdir(parents=True, exist_ok=True)
    earlier = json.loads(PURGED.read_text(encoding="utf-8")) if PURGED.exists() else []
    PURGED.write_text(json.dumps(earlier + purged, indent=2), encoding="utf-8")
    r3.log(f"round 3c purge: {len(purged)} harness-error runs removed and logged")


def stage(key, backend):
    name = f"parser3c_{backend}"
    if r3.done(name):
        return True
    if not r3b.card():
        return False
    proc = r3.start_server(key)
    if not r3.server_ready():
        r3.stop_server(proc, key)
        r3.mark(name, ok=False)
        return True
    steps = [("budget_12288", r3b.parser_cmd(backend, ["page_text_confirm2"], 12288), r3.HARNESS)]
    if backend == "nemotron-parse":
        steps += [("double", r3b.parser_cmd(backend, r3b.FRESH, 8192, "double", workers=1), r3.HARNESS),
                  ("triple", r3b.parser_cmd(backend, r3b.FRESH, 8192, "triple", workers=1), r3.HARNESS)]
    ok = r3b.run_steps(name, steps)
    r3.stop_server(proc, key)
    if not ok:
        return False
    r3.mark(name)
    return True


def main():
    if len(sys.argv) < 2 or sys.argv[1] != "run":
        print(__doc__)
        return 2
    while not r3.done("stats3b"):  # never share the card with a running round 3b
        time.sleep(60)
    r3.log("round 3c start")
    if not r3.done("purge3c"):
        purge()
        r3.mark("purge3c")
    for key, backend in r3b.PARSERS:
        if not stage(key, backend):
            r3.log("paused")
            return 75
    r3b.stage_stats()
    r3.restore_original_server()
    r3.log("round 3c complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
