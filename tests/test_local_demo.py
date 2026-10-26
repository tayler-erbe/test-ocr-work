import unittest
from local_demo import FIELDS, materialize

class EvidenceTests(unittest.TestCase):
    def test_model_cannot_replace_amount_or_create_page(self):
        spans = [{"id": "p3:l2", "page": 3, "text": "The fee is $5000."}]
        selected = {key: [] for key in FIELDS}
        selected["payment"] = ["p3:l2"]
        result = next(r for r in materialize(selected, spans) if r["field"] == "payment")
        self.assertEqual(result["evidence"], spans)
        selected["payment"] = ["p1:l2"]
        with self.assertRaises(ValueError):
            materialize(selected, spans)

    def test_free_text_and_missing_fields_rejected(self):
        with self.assertRaises(ValueError):
            materialize({"payment": "$9000"}, [])

    def test_absence_is_unconfirmed(self):
        results = materialize({key: [] for key in FIELDS}, [])
        self.assertTrue(all(r["status"] == "not_found_unconfirmed" for r in results))

if __name__ == "__main__":
    unittest.main()
