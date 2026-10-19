import json
from pathlib import Path
import tempfile
import unittest
from document_lab import connect
from build_local_model_report import build


class LocalReportTests(unittest.TestCase):
    def test_current_protocol_only_and_no_double_count_on_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); connect(root).close()
            directory = root / 'reports/local-models'; directory.mkdir(parents=True)
            row = {'model': 'ollama/test', 'case_id': 'chart-image:x.png', 'task': 'chartqa_image_only', 'status': 'complete',
                   'error': None, 'gold': '5', 'observed': '5', 'correct': True, 'seconds': 1,
                   'protocol_hash': 'current', 'deployment_snapshot_sha256': 'model', 'generation_info': {}}
            old = dict(row, protocol_hash='superseded', correct=False, status='failed')
            (directory / 'vision-events.jsonl').write_text('\n'.join(json.dumps(r) for r in [old, row, row]) + '\n')
            result = build(root)['results'][0]
            self.assertEqual(result['attempted'], 1)
            self.assertEqual(result['accuracy'], 1)
            self.assertEqual(result['status'], 'running')
            self.assertEqual(result['expected'], 20)

    def test_private_evidence_is_not_exported_to_aggregate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); db = connect(root)
            db.execute('INSERT INTO findings VALUES (?,?,?,?,?,?,?)', ('run', 'private-doc', 'ollama/test', 'payment', '["PRIVATE_QUOTE_SENTINEL"]', 'evidence_selected_review_required', '{}'))
            db.commit(); db.close()
            build(root)
            exported = (root / 'reports/local-models/vision-summary.json').read_text()
            self.assertNotIn('PRIVATE_QUOTE_SENTINEL', exported)
            self.assertNotIn('private-doc', exported)
            self.assertIn('evidence_selected_review_required', exported)


if __name__ == '__main__':
    unittest.main()
