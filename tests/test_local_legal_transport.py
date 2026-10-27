"""Provider-free tests for new local transport boundaries; frozen scorer untouched."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks/harness/tools"))
import local_legal_reassessment as adapter

class LocalTransportTests(unittest.TestCase):
    def test_gpt_low_is_not_reasoning_off(self):
        self.assertEqual(adapter.think_value("gpt-oss:20b", False), "low")
        self.assertEqual(adapter.think_value("gpt-oss:20b", True), "high")
        self.assertIs(adapter.think_value("qwen3:14b", False), False)

    def test_native_schema_and_generation_controls(self):
        schema = {"type": "object", "properties": {"ids": {"type": "array"}}}
        body = {"response_format": {"type": "json_schema", "json_schema": {"schema": schema}},
                "messages": [{"role": "user", "content": "public source"}],
                "chat_template_kwargs": {"enable_thinking": True}, "temperature": 0,
                "top_p": 1, "max_tokens": 16000}
        native = adapter.translate(body, "gpt-oss:20b")
        self.assertEqual(native["format"], schema)
        self.assertEqual(native["think"], "high")
        self.assertEqual(native["options"]["num_predict"], 16000)
        self.assertEqual(native["messages"], body["messages"])

    def test_failed_validation_does_not_discard_final_answer(self):
        result = {"content": "invalid json retained locally", "done_reason": "length",
                  "usage": {"completion_tokens": 16000}, "reasoning_present": True, "think_sent": True}
        row = {"status": "failed", "metrics": {"correct": False}}
        row.update(adapter.retained_result(result))
        with self.assertRaises(ValueError):
            adapter.score_row(None, {}, {}, {}, [], result)
        self.assertEqual(row["final_answer"], result["content"])
        self.assertEqual(row["finish_reason"], "length")
        self.assertFalse(row["metrics"]["correct"])
        self.assertNotIn("thinking", row)

    def test_prompt_measurement_is_a_one_token_prefill_without_reasoning(self):
        body = {"response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": "public source"}],
                "chat_template_kwargs": {"enable_thinking": True}, "temperature": 0, "top_p": 1, "max_tokens": 16000}
        calls = []
        adapter.ollama = lambda path, payload=None, timeout=0: calls.append(payload) or {"prompt_eval_count": 4321}
        self.assertEqual(adapter.measure_prompt("gpt-oss:20b", body, 65536), 4321)
        self.assertEqual(calls[0]["options"]["num_predict"], 1)
        self.assertEqual(calls[0]["options"]["num_ctx"], 65536)
        self.assertEqual(calls[0]["think"], "low")
        self.assertEqual(calls[0]["format"], "json")

if __name__ == "__main__":
    unittest.main()
