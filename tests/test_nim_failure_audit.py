import json
import unittest

from build_nim_audit_report import quote_diagnostics
from nim_failure_audit import coverage


class AuditTests(unittest.TestCase):
    def test_coverage_requires_entire_reference_not_only_overlap(self):
        case = {'task': 'extract', 'gold': json.dumps({'answers': [{'answer_start': 0, 'text': 'abcd'}]})}
        self.assertEqual(coverage(case, [{'start': 0, 'end': 2}]), 0)
        self.assertEqual(coverage(case, [{'start': 0, 'end': 2}, {'start': 2, 'end': 4}]), 1)

    def test_cross_span_quote_is_not_mislabeled_paraphrase(self):
        raw = {'content': json.dumps({'matches': [{'id': 's1', 'quote': 'abc def'}]})}
        spans = [{'id': 's1', 'text': 'abc '}, {'id': 's2', 'text': 'def'}]
        self.assertEqual(quote_diagnostics(raw, spans), {'literal_in_visible_context_but_wrong_span': 1})

    def test_ambiguous_quote_is_distinguished(self):
        raw = {'content': json.dumps({'matches': [{'id': 's1', 'quote': 'abc'}]})}
        self.assertEqual(quote_diagnostics(raw, [{'id': 's1', 'text': 'abc abc'}]), {'ambiguous_literal_quote': 1})


if __name__ == '__main__':
    unittest.main()
