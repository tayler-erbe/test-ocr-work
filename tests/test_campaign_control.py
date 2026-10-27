"""No inference: verify pause boundaries, checkpoint integrity and parser resume."""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks/harness"))
sys.path.insert(0, str(ROOT / "benchmarks/harness/tools"))
import campaign_control as control
import parser_eval

class PauseTests(unittest.TestCase):
    def test_pause_before_start_dispatches_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "PAUSE").touch()
            calls = []
            self.assertEqual(list(control.bounded_results(range(8), lambda x: calls.append(x), 2, td)), [])
            self.assertEqual(calls, [])

    def test_pause_at_first_result_prevents_remaining_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            calls = []
            def work(item):
                calls.append(item)
                (Path(td) / "PAUSE").touch()
                return item
            self.assertEqual(list(control.bounded_results(range(10), work, 1, td)), [(0, 0)])
            self.assertEqual(calls, [0])

    def test_resume_keeps_failed_attempt_and_rejects_changed_plan(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "run"
            plan = {"model": "fixed", "context": 100}
            self.assertEqual(control.checkpoint_rows(out, plan, False), [])
            failed = {"arm": "low", "case_id": "a", "status": "failed"}
            control.append_row(out, failed)
            self.assertEqual(control.checkpoint_rows(out, plan, True), [failed])
            with self.assertRaises(ValueError):
                control.checkpoint_rows(out, {**plan, "context": 101}, True)
            control.durable_json(out / "IN_FLIGHT.LOCAL_ONLY.json", {"case": "b"})
            with self.assertRaises(ValueError):
                control.checkpoint_rows(out, plan, True)

    def test_duplicate_checkpoint_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "run"
            control.checkpoint_rows(out, {}, False)
            row = {"arm": "high", "case_id": "a"}
            control.append_row(out, row)
            control.append_row(out, row)
            with self.assertRaises(ValueError):
                control.checkpoint_rows(out, {}, True)

    def test_legal_pause_resume_counts_each_failed_attempt_once(self):
        import contextlib
        import io
        import os
        import local_legal_reassessment as legal
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            flag = root / "control"
            flag.mkdir()
            out = root / "legal"
            calls = []
            def fake_call(*args):
                calls.append(1)
                if len(calls) == 1:
                    (flag / "PAUSE").touch()
                return {"content": "bad json", "done_reason": "stop", "usage": {}, "reasoning_present": True, "think_sent": "low"}
            argv = ["local", "--out", str(out), "--arms", "baseline", "--control-dir", str(flag), "--run"]
            with patch.dict(os.environ, {"OLLAMA_MODEL": "gpt-oss:20b"}), patch.object(legal, "snapshot", return_value=({"model": "fixed"}, "fixed")), patch.object(legal, "measure_prompt", return_value=5), patch.object(legal, "residency", return_value={"fully_on_gpu": True}), patch.object(legal, "acquire_lock"), patch.object(legal, "ollama", return_value={}), patch.object(legal, "call", side_effect=fake_call), contextlib.redirect_stdout(io.StringIO()):
                with patch.object(sys, "argv", argv):
                    legal.main()
                self.assertEqual(len(calls), 1)
                self.assertEqual(json.loads((out / "STATUS.LOCAL_ONLY.json").read_text())["status"], "paused")
                (flag / "PAUSE").unlink()
                with patch.object(sys, "argv", argv + ["--resume"]):
                    legal.main()
            rows = [json.loads(line) for line in (out / "events.LOCAL_ONLY.jsonl").read_text().splitlines()]
            self.assertEqual(len(calls), 24)
            self.assertEqual(len(rows), 24)
            self.assertEqual(len({(row["arm"], row["case_id"]) for row in rows}), 24)
            self.assertTrue(all(row["status"] == "failed" and row["final_answer"] == "bad json" for row in rows))
            self.assertEqual(json.loads((out / "STATUS.LOCAL_ONLY.json").read_text())["status"], "complete")

    def test_parser_pause_resume_does_not_repeat_failed_case(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            flag = root / "control"
            flag.mkdir()
            db = sqlite3.connect(":memory:")
            db.execute("CREATE TABLE runs(id TEXT PRIMARY KEY, model TEXT, started TEXT, config TEXT, status TEXT)")
            manifest = {"cases_sha256": "frozen", "cases": [{"task": "table", "id": "one"}, {"task": "table", "id": "two"}]}
            calls = []
            def fake_case(*args):
                case = args[-1]
                calls.append(case["id"])
                if case["id"] == "one":
                    (flag / "PAUSE").touch()
                    raise ValueError("record this failure once")
                return {"header": [], "rows": []}, {"teds": 1.0}
            with patch.object(parser_eval, "connect", return_value=db), patch.object(parser_eval, "served_model", return_value=("frozen", {"id": "frozen"})), patch.object(parser_eval.ve, "load_cases", return_value=manifest), patch.object(parser_eval, "run_case", side_effect=fake_case), patch.object(parser_eval, "acquire_lock"):
                parser_eval.run(root, "olmocr2", "unused", ["table"], workers=1, control=flag)
                self.assertEqual(db.execute("SELECT status FROM runs").fetchone()[0], "paused")
                (flag / "PAUSE").unlink()
                parser_eval.run(root, "olmocr2", "unused", ["table"], workers=1, control=flag)
                self.assertEqual(db.execute("SELECT status FROM runs").fetchone()[0], "complete")
            self.assertEqual(calls, ["one", "two"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM vision_results").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM vision_results WHERE status='failed'").fetchone()[0], 1)
            db.close()

if __name__ == "__main__":
    unittest.main()
