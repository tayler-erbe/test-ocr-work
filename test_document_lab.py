import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from document_lab import connect, digest, gates, overlap, put_doc, score, split_spans, validate_response
from acquire_datasets import safe_target, transfer
from benchmark_tasks import edit_distance

class EvidenceIntegrity(unittest.TestCase):
    def setUp(self):
        self.spans = [{"id": "p3:l2", "page": 3, "start": 10, "end": 27, "text": "The fee is $5000."}]

    def test_altered_money_cannot_pass(self):
        for quote in ["The fee is $9000.", "The fee is $5,000.", "the fee is $5000."]:
            with self.assertRaises(ValueError):
                validate_response({"matches": [{"id": "p3:l2", "quote": quote}]}, self.spans, "extraction")

    def test_exact_quote_copies_page_and_offsets(self):
        evidence = validate_response({"matches": [{"id": "p3:l2", "quote": "$5000"}]}, self.spans, "extraction")
        self.assertEqual(evidence[0]["text"], "$5000")
        self.assertEqual((evidence[0]["page"], evidence[0]["start"], evidence[0]["end"]), (3, 21, 26))

    def test_unknown_and_duplicate_evidence_rejected(self):
        for ids in [["not-in-context"], ["p3:l2", "p3:l2"]]:
            with self.assertRaises(ValueError):
                validate_response({"ids": ids, "label": "Entailment"}, self.spans, "nli")

    def test_absence_cannot_have_supporting_evidence(self):
        with self.assertRaises(ValueError):
            validate_response({"ids": ["p3:l2"], "label": "NotMentioned"}, self.spans, "nli")

    def test_supported_label_requires_evidence(self):
        with self.assertRaises(ValueError):
            validate_response({"ids": [], "label": "Entailment"}, self.spans, "nli")

    def test_repeated_quote_is_ambiguous(self):
        with self.assertRaises(ValueError):
            validate_response({"matches": [{"id": "s0", "quote": "fee"}]}, [{"id": "s0", "text": "fee and fee", "start": 0}], "extraction")

    def test_empty_extraction_is_valid_but_not_a_fact(self):
        self.assertEqual(validate_response({"matches": []}, self.spans, "extraction"), [])

class Scoring(unittest.TestCase):
    def test_numeric_mutation_reduces_overlap(self):
        self.assertLess(overlap("$9000", "$5000"), 1)

    def test_ocr_edit_distance_handles_insertions(self):
        self.assertEqual(edit_distance("5000", "5000"), 0)
        self.assertEqual(edit_distance("5000", "9000"), 1)
        self.assertEqual(edit_distance("", "abc"), 3)

    def test_gold_absent_false_positive_is_incorrect(self):
        case = {"task": "extraction", "gold": json.dumps({"answers": []})}
        result = score(case, {"matches": []}, [{"text": "A clause"}], [])
        self.assertFalse(result["correct"])

    def test_nested_gold_annotations_not_double_counted(self):
        case = {"task": "extraction", "gold": json.dumps({"answers": [{"text": "Airspan Networks", "answer_start": 0}, {"text": "Airspan", "answer_start": 0}]})}
        result = score(case, {}, [{"text": "Airspan Networks"}], [{"start": 0, "end": 16}])
        self.assertEqual(result["evidence_f1"], 1)
        self.assertTrue(result["correct"])

    def test_zero_attempts_never_pass(self):
        self.assertEqual(gates({"attempted": 0}, {})["status"], "not_tested")

    def test_small_perfect_sample_never_promotes(self):
        policy = {"min_documents": 30, "min_cases": 100, "max_failure_rate": .02, "min_accuracy": .9, "min_evidence_f1": .9}
        metrics = {"attempted": 12, "documents": 12, "failure_rate": 0, "accuracy": 1, "evidence_f1": 1}
        self.assertEqual(gates(metrics, policy)["status"], "insufficient_evidence")
        metrics.update(attempted=100, documents=30)
        self.assertEqual(gates(metrics, policy)["status"], "requires_human_holdout_review")
        metrics.update(failure_rate=.1)
        self.assertEqual(gates(metrics, policy)["status"], "failed")

class Storage(unittest.TestCase):
    def test_frozen_protocol_remains_byte_identical(self):
        snapshot=Path(__file__).with_name('protocols')/'evaluation_v3.py'
        self.assertEqual(digest(snapshot.read_bytes()),'43f78d7f122a6c1c0df5a484a49569ff20858ad72f0fac784b86615ca1e0d27f')

    def test_source_span_offsets_reconstruct_exact_source(self):
        text = "First line\n" + "a long paragraph " * 90
        spans = split_spans(text, max_chars=70)
        self.assertTrue(all(text[s["start"]:s["end"]] == s["text"] for s in spans))
        self.assertEqual("".join(s["text"] for s in spans), text.replace("\n", ""))

    def test_reimport_is_idempotent_and_searchable(self):
        with tempfile.TemporaryDirectory() as directory:
            db = connect(Path(directory))
            for _ in range(2):
                put_doc(db, "synthetic", "1", "Synthetic", "The fee is $5000")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM documents").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM search WHERE search MATCH 'fee'").fetchone()[0], 1)
            db.close()

    def test_destination_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                safe_target(Path(directory), "../outside")

    def test_existing_wrong_checksum_never_marked_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "example/raw/test.txt"; target.parent.mkdir(parents=True); target.write_text("altered")
            with patch("acquire_datasets.time.sleep"):
                result = transfer({"dataset": "example", "path": "test.txt", "url": "https://invalid.invalid", "expected_sha256": digest("original")}, root)
            self.assertEqual(result["status"], "failed")
            self.assertIn("SHA-256", result["error"])

if __name__ == "__main__":
    unittest.main()
