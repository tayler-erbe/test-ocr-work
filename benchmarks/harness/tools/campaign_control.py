"""Cooperative request-boundary pause; never kills or unloads another service."""
import argparse
import atexit
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import json
import os
from pathlib import Path


def paused(directory):
    return bool(directory) and (Path(directory) / "PAUSE").exists()


def durable_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf8") as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def bounded_results(items, function, workers, control):
    """Never queues the entire campaign. Drain active requests on cooperative pause."""
    iterator = iter(items)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        pending = {}
        def fill():
            while len(pending) < max(1, workers) and not paused(control):
                try:
                    item = next(iterator)
                except StopIteration:
                    break
                pending[pool.submit(function, item)] = item
        fill()
        while pending:
            completed, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                item = pending.pop(future)
                yield item, future.result()
            fill()


def acquire_lock(path):
    """Exclusive local-run lease. A crash leaves the lease for explicit operator audit."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf8") as stream:
            stream.write(str(os.getpid()))
    except FileExistsError as exc:
        raise ValueError("Run lease exists; verify prior worker exited before removing: " + str(path)) from exc
    atexit.register(lambda: path.unlink(missing_ok=True))


def checkpoint_rows(out, plan, resume):
    """Only same-plan resumptions; completed failures are never retried."""
    out = Path(out)
    if not resume:
        if out.exists():
            raise ValueError("New runs require a new output directory")
        out.mkdir(parents=True)
        durable_json(out / "PLAN.json", plan)
        return []
    if not out.is_dir():
        raise ValueError("Resume needs an existing output directory")
    if (out / "IN_FLIGHT.LOCAL_ONLY.json").exists():
        raise ValueError("Uncertain interrupted request: manual audit required, no automatic retry")
    saved = json.loads((out / "PLAN.json").read_text(encoding="utf8"))
    saved.pop("residency", None)
    if saved != plan:
        raise ValueError("Resume refused: model/runtime, inputs, context, code or settings changed")
    journal = out / "events.LOCAL_ONLY.jsonl"
    rows = [json.loads(line) for line in journal.read_text(encoding="utf8").splitlines()] if journal.exists() else []
    keys = [(row["arm"], row["case_id"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate attempt in checkpoint")
    return rows


def append_row(out, row):
    with (Path(out) / "events.LOCAL_ONLY.jsonl").open("a", encoding="utf8") as stream:
        stream.write(json.dumps(row) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-dir", type=Path, required=True)
    parser.add_argument("action", choices=["pause", "resume", "status"])
    args = parser.parse_args()
    args.control_dir.mkdir(parents=True, exist_ok=True)
    flag = args.control_dir / "PAUSE"
    if args.action == "pause":
        flag.touch()
    elif args.action == "resume":
        flag.unlink(missing_ok=True)
    print(json.dumps({"pause_requested": paused(args.control_dir),
                      "note": "Pause drains active requests; resume clears flag only. Relaunch the same command. GPU memory release is separate."}))


if __name__ == "__main__":
    main()
