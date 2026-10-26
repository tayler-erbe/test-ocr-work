"""Unit tests for retrieval_v2.py on a FABRICATED contract (no real documents, no model calls)."""
import unittest

import retrieval_v2 as R

FILLER = ("The parties acknowledge that this paragraph describes ordinary operational matters, schedules and "
          "internal procedures of the engagement in general terms only, without creating further obligations.")


def build_spans():
    texts = [
        "MASTER SERVICES AGREEMENT",
        "This Agreement is entered into as of 1 March 2030 by and between Fictional Supply Co. and Imaginary Buyer LLC.",
        "1. Services",
        "The Supplier shall deliver the deliverables described in each statement of work.",
    ]
    for k in range(40):
        texts.append(f"{FILLER} Item {k}.")
    texts += [
        "12. Governing Law",
        "This Agreement is governed by the laws of the State of Nowhere, and venue lies in its courts.",
        "13. Miscellaneous",
        "Notices must be in writing.",
    ]
    for k in range(10):
        texts.append(f"{FILLER} Addendum {k}.")
    texts += ["IN WITNESS WHEREOF the parties have signed.", "Signed: A. Person", "Signed: B. Person"]
    out, pos = [], 0
    for i, t in enumerate(texts):
        out.append({"id": f"s{i}", "text": t, "page": 1 + i // 8, "start": pos, "end": pos + len(t)})
        pos += len(t) + 1
    return out


def nbytes(spans_by_id, ids):
    return sum(len(spans_by_id[i]["text"].encode()) for i in ids)


class Retrieval(unittest.TestCase):
    def setUp(self):
        self.spans = build_spans()
        self.by_id = {s["id"]: s for s in self.spans}
        self.fields = list(R.FIELD_QUERIES)

    def test_buried_governing_law_clause_retrieved_with_heading(self):
        ids, rep = R.select_context(self.spans, ["governing_law", "payment"], budget_bytes=1500, per_field_min_bytes=400)
        texts = [self.by_id[i]["text"] for i in ids]
        self.assertTrue(any("laws of the State of Nowhere" in t for t in texts))
        self.assertIn("12. Governing Law", texts)
        self.assertTrue(rep["per_field"]["governing_law"]["heading_hits"])

    def test_heading_pulls_following_span(self):
        ids, rep = R.select_context(self.spans, ["governing_law"], budget_bytes=1500, per_field_min_bytes=100,
                                    opening_lines=1, closing_lines=1)
        self.assertEqual(rep["reasons"]["s45"], "heading_follow")  # the clause text after "12. Governing Law" (s44)

    def test_budget_respected(self):
        for budget in (600, 1500, 5000):
            ids, rep = R.select_context(self.spans, self.fields, budget_bytes=budget, per_field_min_bytes=200)
            self.assertLessEqual(nbytes(self.by_id, ids), budget)
            self.assertEqual(rep["selected_bytes"], nbytes(self.by_id, ids))

    def test_per_field_minimum_holds(self):
        ids, rep = R.select_context(self.spans, self.fields, budget_bytes=4000, per_field_min_bytes=250)
        for f in ("governing_law", "effective_date", "deliverables", "parties"):
            self.assertGreater(rep["per_field"][f]["bytes"], 100, f)
            self.assertTrue(rep["per_field"][f]["min_bytes_met"], f)

    def test_opening_and_closing_always_included(self):
        ids, _ = R.select_context(self.spans, self.fields, budget_bytes=1200, per_field_min_bytes=100, opening_lines=2)
        self.assertIn("s0", ids)
        self.assertIn("s1", ids)
        self.assertIn(self.spans[-1]["id"], ids)

    def test_deterministic_and_document_order(self):
        a = R.select_context(self.spans, self.fields, budget_bytes=3000)
        b = R.select_context(list(self.spans), self.fields, budget_bytes=3000)
        self.assertEqual(a, b)
        idx = [int(i[1:]) for i in a[0]]
        self.assertEqual(idx, sorted(idx))

    def test_report_labels_coverage_honestly(self):
        _, rep = R.select_context(self.spans, self.fields, budget_bytes=3000)
        self.assertIn("not answer recall", rep["label"])
        self.assertTrue(0 < rep["context_coverage"] < 1)

    def test_heading_detection(self):
        self.assertTrue(R.looks_like_heading("12. Governing Law"))
        self.assertTrue(R.looks_like_heading("TERMINATION"))
        self.assertFalse(R.looks_like_heading("This Agreement is governed by the laws of the State of Nowhere."))

    def test_unknown_field_rejected(self):
        with self.assertRaises(ValueError):
            R.select_context(self.spans, ["nope"])


if __name__ == "__main__":
    unittest.main()
