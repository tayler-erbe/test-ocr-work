"""Checks isolation of model inputs and validity of absence handling."""
import json
from pathlib import Path
import unittest

from nemotron_reassessment import ARMS, REPO, make_body, summarize


class ReassessmentTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((REPO / 'handoff/legal-comparison-24/requests.json').read_text())[0]
        self.request['question'] = 'Which clause applies?'

    def test_frozen_baseline_keeps_exact_input_and_schema(self):
        body = make_body(self.request, ARMS['baseline'], 'model')
        self.assertEqual(body['messages'], self.request['messages'])
        self.assertEqual(body['response_format']['json_schema']['schema'], self.request['schema'])
        self.assertEqual(body['max_tokens'], 2000)

    def test_model_input_has_no_scoring_channel(self):
        for arm, config in ARMS.items():
            body = make_body(self.request, config, 'model', [{'id': 's1', 'text': 'Public source.'}])
            self.assertNotIn('gold', body)
            self.assertNotIn('reference', body)
            self.assertIn('messages', body)

    def test_full_context_replaces_source_and_allowed_ids(self):
        body = make_body(self.request, ARMS['full_document'], 'model', [{'id': 'ONLY', 'text': 'Complete source.'}])
        self.assertTrue(body['messages'][-1]['content'].endswith('[ONLY] Complete source.'))
        self.assertEqual(body['response_format']['json_schema']['schema']['properties']['matches']['items']['properties']['id']['enum'], ['ONLY'])

    def test_empty_selection_stays_valid_and_unknown_id_is_rejected(self):
        from nim_evaluation import frozen
        scorer = frozen()
        self.assertEqual(scorer.validate_response({'matches': []}, [], 'extraction'), [])
        with self.assertRaises(ValueError):
            scorer.validate_response({'ids': ['unknown']}, [{'id': 's1', 'text': 'source'}], 'ids')

    def test_failures_remain_in_summary_denominator(self):
        rows = [{'arm': 'baseline', 'dataset': 'cuad', 'status': 'failed', 'finish_reason': 'length'},
                {'arm': 'baseline', 'dataset': 'cuad', 'status': 'complete', 'metrics': {'correct': True, 'evidence_f1': 1}}]
        summary = summarize(rows)[0]
        self.assertEqual((summary['attempted'], summary['correct'], summary['failed'], summary['truncated']), (2, 1, 1, 1))
        self.assertEqual(summary['evidence_f1'], .5)


if __name__ == '__main__':
    unittest.main()
