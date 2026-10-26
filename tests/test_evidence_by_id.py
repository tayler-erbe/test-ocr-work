"""Unit tests for evidence_by_id.py on fabricated documents (no real contracts, no model calls)."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import evidence_by_id as E

HERE = Path(__file__).resolve().parent
PACK = HERE.parent / "benchmarks" / "harness" / "handoff" / "legal-comparison-24"

DOC = ("1. Definitions. The Supplier is Acme Widgets, Inc. of Springfield. "
       "The Customer is Example Corp. 2. Term: This Agreement starts on 1 May 2026; it renews each year. "
       "3. Fees. The Customer pays $12,500.00 per year. The Customer pays $12,500.00 per year.")


def spans_of(text, size=120):
    """Fabricated spans in the frozen scorer's shape (cut at spaces, like split_spans)."""
    out, start = [], 0
    while start < len(text):
        stop = min(start + size, len(text))
        if stop < len(text):
            sp = text.rfind(" ", start, stop)
            stop = sp if sp > start else stop
        out.append({"id": f"s{len(out)}", "text": text[start:stop], "start": start, "end": stop})
        start = stop
    return out


def frozen_scorer():
    spec = importlib.util.spec_from_file_location("frozen_evaluation_v3", PACK / "frozen_evaluation_v3.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(PACK))
    spec.loader.exec_module(mod)
    return mod


class Blocks(unittest.TestCase):
    def setUp(self):
        self.spans = spans_of(DOC)
        self.store = E.SourceStore("doc", self.spans, DOC)

    def test_blocks_reproduce_spans_exactly(self):
        for s in self.spans:
            self.assertEqual("".join(b.text for b in E.split_blocks(s)), s["text"])
        for b in self.store.blocks():
            self.assertEqual(DOC[b.start:b.end], b.text)

    def test_abbreviations_and_clause_numbers_not_cut(self):
        texts = [b.text for b in E.split_blocks({"id": "s", "text": DOC, "start": 0, "end": len(DOC)})]
        self.assertTrue(any("Acme Widgets, Inc. of Springfield." in t for t in texts))
        self.assertFalse(any(t.strip() in ("1.", "2.", "3.") for t in texts))

    def test_stable_ids(self):
        again = E.SourceStore("doc", spans_of(DOC), DOC)
        self.assertEqual(self.store.block_ids, again.block_ids)

    def test_store_detects_mismatch_with_document(self):
        bad = [dict(s) for s in self.spans]
        bad[0]["text"] = bad[0]["text"].replace("Acme", "Acne")
        with self.assertRaises(E.EvidenceError):
            E.SourceStore("doc", bad, DOC)

    def test_store_detects_source_change(self):
        self.store._text = DOC + " tampered"
        with self.assertRaises(E.EvidenceError):
            self.store.materialize(self.store.block_ids[0])

    def test_ocr_lines_to_blocks_keep_page_and_bbox(self):
        lines = [{"page": 1, "text": "Payment terms.", "bbox": (10, 10, 200, 20)},
                 {"page": 1, "text": "Net thirty days.", "bbox": (10, 22, 200, 32)},
                 {"page": 1, "text": "Termination.", "bbox": (10, 80, 200, 90)},
                 {"page": 2, "text": "Either party may end it.", "bbox": (10, 10, 200, 20)}]
        doc, spans = E.blocks_from_ocr_lines(lines)
        self.assertEqual([s["page"] for s in spans], [1, 1, 2])
        store = E.SourceStore("ocr", spans, doc)
        b = store.blocks()[0]
        self.assertEqual(b.page, 1)
        self.assertEqual(b.bbox, (10, 10, 200, 32))
        self.assertEqual(doc[b.start:b.end], b.text)


class Rejections(unittest.TestCase):
    def setUp(self):
        self.store = E.SourceStore("doc", spans_of(DOC), DOC)
        self.ids = list(self.store.block_ids)

    def bad(self, response, full=False, selection="ids"):
        with self.assertRaises(E.EvidenceError):
            E.validate_field(self.store, response, full, selection)

    def test_unknown_id(self):
        self.bad({"outcome": "found", "evidence": ["s99.0"]})

    def test_duplicate_id(self):
        self.bad({"outcome": "found", "evidence": [self.ids[0], self.ids[0]]})

    def test_too_many_items(self):
        self.bad({"outcome": "found", "evidence": [self.ids[0]] * 31})

    def test_extra_or_missing_keys(self):
        self.bad({"outcome": "found", "evidence": [self.ids[0]], "quote": "x"})
        self.bad({"evidence": [self.ids[0]]})

    def test_found_requires_evidence(self):
        self.bad({"outcome": "found", "evidence": []})

    def test_absent_requires_no_evidence(self):
        self.bad({"outcome": "not_found_in_excerpts", "evidence": [self.ids[0]]})
        self.bad({"outcome": "unreadable", "evidence": [self.ids[0]]})

    def test_full_review_claim_needs_full_document(self):
        self.bad({"outcome": "not_present_after_full_review", "evidence": []}, full=False)
        self.bad({"outcome": "not_found_in_excerpts", "evidence": []}, full=True)

    def test_unknown_outcome(self):
        self.bad({"outcome": "maybe", "evidence": []})

    def test_bad_offsets(self):
        bid = self.ids[0]
        n = len(self.store.blocks()[0].text)
        for s, e in [(-1, 3), (0, n + 1), (5, 5), (6, 2), (True, 3), ("0", 3)]:
            self.bad({"outcome": "found", "evidence": [{"id": bid, "start": s, "end": e}]}, selection="offsets")

    def test_whitespace_only_selection(self):
        b = next(x for x in self.store.blocks() if x.text.endswith(" "))
        n = len(b.text)
        self.bad({"outcome": "found", "evidence": [{"id": b.id, "start": n - 1, "end": n}]}, selection="offsets")

    def test_overlapping_offsets(self):
        bid = self.ids[0]
        self.bad({"outcome": "found", "evidence": [{"id": bid, "start": 0, "end": 8}, {"id": bid, "start": 4, "end": 10}]}, selection="offsets")

    def test_anchor_absent_ambiguous_or_reversed(self):
        b = next(x for x in self.store.blocks() if "Acme" in x.text)
        self.bad({"outcome": "found", "evidence": [{"id": b.id, "first": "Acmee", "last": "Springfield"}]}, selection="anchors")
        fees = next(x for x in self.store.blocks() if "$12,500.00" in x.text and x.text.count("The Customer") > 1) if any(
            x.text.count("The Customer") > 1 for x in self.store.blocks()) else None
        if fees:
            self.bad({"outcome": "found", "evidence": [{"id": fees.id, "first": "The Customer", "last": "year."}]}, selection="anchors")
        self.bad({"outcome": "found", "evidence": [{"id": b.id, "first": "Springfield", "last": "Acme"}]}, selection="anchors")

    def test_no_fuzzy_repair_of_anchor(self):
        b = next(x for x in self.store.blocks() if "Acme" in x.text)
        self.bad({"outcome": "found", "evidence": [{"id": b.id, "first": "acme widgets", "last": "Springfield"}]}, selection="anchors")

    def test_wrong_item_shape_for_selection(self):
        self.bad({"outcome": "found", "evidence": [{"id": self.ids[0]}]}, selection="ids")
        self.bad({"outcome": "found", "evidence": [self.ids[0]]}, selection="offsets")

    def test_nli_inconsistency_and_label(self):
        with self.assertRaises(E.EvidenceError):
            E.validate_nli(self.store, {"label": "NotMentioned", "evidence": [self.ids[0]]})
        with self.assertRaises(E.EvidenceError):
            E.validate_nli(self.store, {"label": "Entailment", "evidence": []})
        with self.assertRaises(E.EvidenceError):
            E.validate_nli(self.store, {"label": "Maybe", "evidence": []})

    def test_presence_and_evidence_stage_rules(self):
        with self.assertRaises(E.EvidenceError):
            E.validate_presence({"outcome": "not_present_after_full_review"}, full_document=False)
        with self.assertRaises(E.EvidenceError):
            E.validate_evidence_only(self.store, {"evidence": []})

    def test_value_must_be_verbatim_in_evidence(self):
        with self.assertRaises(E.EvidenceError):
            E.normalize_money("The Customer pays $12,500.00 per year.", "$12,000.00")
        self.assertEqual(E.normalize_money("pays $12,500.00 per year", "$12,500.00")["amount"], "12500.00")


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.spans = spans_of(DOC)
        self.store = E.SourceStore("doc", self.spans, DOC)

    def test_found_materialises_exact_text(self):
        b = next(x for x in self.store.blocks() if "Acme" in x.text)
        r = E.validate_field(self.store, {"outcome": "found", "evidence": [b.id]}, False)
        self.assertTrue(r.accepted)
        self.assertEqual(r.evidence[0]["text"], b.text)
        self.assertEqual(DOC[r.evidence[0]["start"]:r.evidence[0]["end"]], b.text)

    def test_insufficient_keeps_candidates_unaccepted(self):
        r = E.validate_field(self.store, {"outcome": "insufficient_evidence", "evidence": [self.store.block_ids[0]]}, False)
        self.assertFalse(r.accepted)
        self.assertEqual(len(r.candidates), 1)
        self.assertEqual(E.to_frozen_prediction(self.store, r), {"matches": []})

    def test_anchor_trim(self):
        b = next(x for x in self.store.blocks() if "Acme" in x.text)
        r = E.validate_field(self.store, {"outcome": "found", "evidence": [{"id": b.id, "first": "Acme", "last": "Inc."}]}, False, "anchors")
        self.assertEqual(r.evidence[0]["text"], "Acme Widgets, Inc.")

    def test_several_trims_in_one_block(self):
        b = next(x for x in self.store.blocks() if "Acme" in x.text)
        r = E.validate_field(self.store, {"outcome": "found", "evidence": [{"id": b.id, "first": "Acme", "last": "Inc."},
                                                                          {"id": b.id, "first": "Springfield", "last": "Springfield"}]}, False, "anchors")
        self.assertEqual([m["text"] for m in r.evidence], ["Acme Widgets, Inc.", "Springfield"])
        with self.assertRaises(E.EvidenceError):  # identical repeat is still a duplicate
            E.validate_field(self.store, {"outcome": "found", "evidence": [{"id": b.id, "first": "Acme", "last": "Inc."}] * 2}, False, "anchors")

    def test_multifield_isolates_errors(self):
        good = {"outcome": "found", "evidence": [self.store.block_ids[0]]}
        out = E.validate_multifield(self.store, {"fields": {"a": good, "b": {"outcome": "found", "evidence": []}}}, ["a", "b"], False)
        self.assertTrue(out["a"].accepted)
        self.assertIsInstance(out["b"], E.EvidenceError)

    def test_frozen_scorer_accepts_converted_prediction(self):
        sc = frozen_scorer()
        ids = list(self.store.block_ids)
        r = E.validate_field(self.store, {"outcome": "found", "evidence": ids[:3]}, False)
        pred = E.to_frozen_prediction(self.store, r)
        evidence = sc.validate_response(pred, self.spans, "extraction")
        self.assertTrue(evidence)
        for m in pred["matches"]:
            self.assertIn(m["quote"], self.store.span_text(m["id"]))

    def test_cross_span_selection_becomes_one_quote_per_span(self):
        blocks = self.store.blocks()
        pair = next((a, b) for a, b in zip(blocks, blocks[1:]) if a.span_id != b.span_id)
        r = E.validate_field(self.store, {"outcome": "found", "evidence": [pair[0].id, pair[1].id]}, False)
        pred = E.to_frozen_prediction(self.store, r)
        self.assertEqual([m["id"] for m in pred["matches"]], [pair[0].span_id, pair[1].span_id])

    def test_nli_maps_blocks_to_span_ids(self):
        ids = list(self.store.block_ids)
        label, items = E.validate_nli(self.store, {"label": "Entailment", "evidence": ids[:2]})
        out = E.to_frozen_nli(label, items)
        self.assertEqual(out["label"], "Entailment")
        self.assertEqual(len(out["ids"]), len(set(out["ids"])))
        sc = frozen_scorer()
        sc.validate_response(out, self.spans, "nli")

    def test_coverage(self):
        self.assertAlmostEqual(E.source_coverage(self.spans, len(DOC)), 1.0)
        rc = E.reference_coverage(self.spans[:1], [{"answer_start": 0, "text": DOC[:10]}, {"answer_start": len(DOC) - 10, "text": DOC[-10:]}])
        self.assertEqual(rc["fully_visible"], 1)
        self.assertEqual(rc["none_visible"], 1)

    def test_request_schema_limits_ids_and_outcomes(self):
        _, schema = E.build_field_request(self.store, "Who is the supplier?", full_document=False)
        self.assertEqual(schema["properties"]["outcome"]["enum"], list(E.OUTCOMES_EXCERPT))
        self.assertEqual(schema["properties"]["evidence"]["items"]["enum"], list(self.store.block_ids))
        msgs, schema_full = E.build_field_request(self.store, "Who is the supplier?", full_document=True)
        self.assertIn("not_present_after_full_review", schema_full["properties"]["outcome"]["enum"])
        self.assertIn("complete document", msgs[1]["content"])


class DuplicatePolicyV2(unittest.TestCase):
    def setUp(self):
        self.store = E.SourceStore("doc", spans_of(DOC), DOC)
        self.ids = list(self.store.block_ids)
        self.b = next(x for x in self.store.blocks() if "Acme" in x.text)

    def test_policy_version(self):
        self.assertEqual(E.EVIDENCE_POLICY_VERSION, "2")

    def test_exact_duplicate_id_dropped_with_audit(self):
        resp = {"outcome": "found", "evidence": [self.ids[0], self.ids[1], self.ids[0]]}
        r = E.validate_field(self.store, resp, False, duplicates="drop_exact")
        self.assertTrue(r.accepted)
        self.assertEqual(len(r.evidence), 2)
        self.assertEqual(r.normalizations, [{"type": "exact_duplicate_removed", "id": self.ids[0], "position": 2, "policy_version": "2"}])
        self.assertEqual(r.raw_response, resp)
        self.assertIsNot(r.raw_response, resp)
        self.assertEqual(len(r.raw_response["evidence"]), 3)

    def test_default_still_rejects_and_has_empty_audit(self):
        resp = {"outcome": "found", "evidence": [self.ids[0], self.ids[0]]}
        with self.assertRaises(E.EvidenceError):
            E.validate_field(self.store, resp, False)
        with self.assertRaises(E.EvidenceError):
            E.validate_field(self.store, resp, False, duplicates="reject")
        ok = E.validate_field(self.store, {"outcome": "found", "evidence": [self.ids[0]]}, False)
        self.assertEqual(ok.normalizations, [])

    def test_unknown_policy_is_a_programming_error(self):
        with self.assertRaises(ValueError):
            E.validate_field(self.store, {"outcome": "found", "evidence": [self.ids[0]]}, False, duplicates="merge")

    def test_same_id_disjoint_offsets_passes_under_both(self):
        resp = {"outcome": "found", "evidence": [{"id": self.b.id, "start": 0, "end": 4}, {"id": self.b.id, "start": 10, "end": 14}]}
        for pol in ("reject", "drop_exact"):
            r = E.validate_field(self.store, resp, False, "offsets", duplicates=pol)
            self.assertEqual(len(r.evidence), 2, pol)
            self.assertEqual(r.normalizations, [], pol)

    def test_overlapping_offsets_still_rejected_under_drop_exact(self):
        resp = {"outcome": "found", "evidence": [{"id": self.b.id, "start": 0, "end": 8}, {"id": self.b.id, "start": 4, "end": 10}]}
        with self.assertRaises(E.EvidenceError):
            E.validate_field(self.store, resp, False, "offsets", duplicates="drop_exact")

    def test_identical_offset_repeat_dropped(self):
        item = {"id": self.b.id, "start": 0, "end": 8}
        resp = {"outcome": "found", "evidence": [item, dict(item)]}
        with self.assertRaises(E.EvidenceError):
            E.validate_field(self.store, resp, False, "offsets")
        r = E.validate_field(self.store, resp, False, "offsets", duplicates="drop_exact")
        self.assertEqual(len(r.evidence), 1)
        self.assertEqual(r.normalizations[0]["position"], 1)

    def test_identical_anchor_repeat_dropped_after_resolution(self):
        item = {"id": self.b.id, "first": "Acme", "last": "Inc."}
        r = E.validate_field(self.store, {"outcome": "found", "evidence": [item, dict(item)]}, False, "anchors", duplicates="drop_exact")
        self.assertEqual(len(r.evidence), 1)
        self.assertEqual(len(r.normalizations), 1)

    def test_multifield_and_evidence_only_pass_policy_through(self):
        resp = {"fields": {"a": {"outcome": "found", "evidence": [self.ids[0], self.ids[0]]}}}
        self.assertIsInstance(E.validate_multifield(self.store, resp, ["a"], False)["a"], E.EvidenceError)
        out = E.validate_multifield(self.store, resp, ["a"], False, duplicates="drop_exact")
        self.assertTrue(out["a"].accepted)
        norms = []
        items = E.validate_evidence_only(self.store, {"evidence": [self.ids[0], self.ids[0]]}, duplicates="drop_exact", normalizations=norms)
        self.assertEqual((len(items), len(norms)), (1, 1))
        with self.assertRaises(E.EvidenceError):
            E.validate_evidence_only(self.store, {"evidence": [self.ids[0], self.ids[0]]})

    def test_frozen_prediction_unchanged_by_audit_fields(self):
        r = E.validate_field(self.store, {"outcome": "found", "evidence": [self.ids[0]]}, False)
        self.assertEqual(set(E.to_frozen_prediction(self.store, r)), {"matches"})


if __name__ == "__main__":
    unittest.main()
