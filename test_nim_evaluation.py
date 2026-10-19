import json
import unittest
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import urllib.request
from nim_evaluation import Client, ServiceError, Transport, frozen, public, PROTOCOL_SHA
from document_lab import connect, put_doc, add_case


class NIMAdapterTests(unittest.TestCase):
    def test_remote_requires_https_and_no_url_credentials(self):
        for url in ['http://internal.example/v1', 'https://user:key@internal.example', 'https://internal.example/?key=secret']:
            with self.assertRaises(ValueError):
                Client(url)

    def test_schema_and_budget_preserved(self):
        client = Client('https://internal.example', model='test')
        payload = {'messages': [{'role': 'user', 'content': 'source'}], 'format': {'type': 'object'}, 'options': {'num_predict': 600}}
        raw = {'choices': [{'finish_reason': 'stop', 'message': {'content': '{}'}}], 'usage': {'completion_tokens': 12}}
        with patch.object(client, 'request', return_value=raw) as send:
            answer = client.chat(payload)
        body = send.call_args.args[1]
        self.assertEqual(body['max_tokens'], 600)
        self.assertTrue(body['response_format']['json_schema']['strict'])
        self.assertEqual(body['response_format']['json_schema']['schema'], payload['format'])
        self.assertEqual(answer['eval_count'], 12)

    def test_truncation_and_refusal_cannot_pass(self):
        client = Client('https://internal.example', model='test')
        payload = {'messages': [], 'format': {}, 'options': {'num_predict': 600}}
        for choice in [{'finish_reason': 'length', 'message': {'content': '{}'}}, {'finish_reason': 'stop', 'message': {'content': '{}', 'refusal': 'no'}}]:
            with patch.object(client, 'request', return_value={'choices': [choice]}):
                with self.assertRaises(ValueError):
                    client.chat(payload)

    def test_tuned_profile_is_distinct_and_controls_are_sent(self):
        client = Client('https://internal.example', model='test', thinking=False, max_tokens=2000)
        payload = {'messages': [], 'format': {'type': 'object'}, 'options': {'num_predict': 600}}
        with patch.object(client, 'request', return_value={'choices': [{'finish_reason': 'stop', 'message': {'content': '{}'}}]}) as send:
            client.chat(payload)
        body = send.call_args.args[1]
        self.assertEqual(body['max_tokens'], 2000)
        self.assertEqual(body['chat_template_kwargs'], {'enable_thinking': False})
        self.assertTrue(body['response_format']['json_schema']['strict'])
        self.assertNotEqual(client.label, Client('https://internal.example', model='test').label)

    def test_tuned_discovery_does_not_reuse_baseline_identity(self):
        baseline = Client('https://internal.example', model='test')
        tuned = Client('https://internal.example', model='test', thinking=False, max_tokens=2000)
        for client in [baseline, tuned]:
            with patch.object(client, 'request', side_effect=[{'data': [{'id': 'test'}]}, {}, {}]):
                client.discover()
        self.assertNotEqual(baseline.revision, tuned.revision)

    def test_model_selection_does_not_guess_first_endpoint(self):
        client = Client('https://internal.example')
        with patch.object(client, 'request', return_value={'data': [{'id': 'a'}, {'id': 'b'}]}):
            with self.assertRaises(ValueError):
                client.discover()

    def test_bridge_does_not_patch_global_transport(self):
        original = urllib.request.urlopen
        protocol = frozen()
        from types import SimpleNamespace
        client = Client('https://internal.example', model='test')
        client.revision = 'snapshot'
        protocol.urllib = SimpleNamespace(request=Transport(client))
        with patch.object(client, 'chat', return_value={'message': {'content': '{"matches": []}'}}):
            result, _ = protocol.ollama('nim/test', 'question', [{'id': 's0', 'text': 'sample'}], 'extraction')
        self.assertEqual(result, {'matches': []})
        self.assertIs(urllib.request.urlopen, original)

    def test_interrupted_run_resumes_without_repeating_completed_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); db = connect(root)
            doc = put_doc(db, 'cuad', 'one', 'sample', 'source')
            for index in range(2):
                add_case(db, str(index), 'cuad', doc, 'extraction', 'test', 'question', [{'id': 's0', 'text': 'source'}], {'answers': []})
            db.commit(); db.close()
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'source_code_sha256': PROTOCOL_SHA, 'case_ids': ['0', '1']}))
            client = Client('https://internal.example', model='test'); client.revision = 'snapshot'
            protocol = SimpleNamespace(select_context=lambda spans, question: spans,
                                       validate_response=lambda *args: [], score=lambda *args: {'correct': True, 'evidence_f1': 1})
            with patch('nim_evaluation.frozen', return_value=protocol), patch.object(protocol, 'ollama', create=True, side_effect=[({}, {}), ServiceError('offline')]):
                with self.assertRaises(ServiceError):
                    public(root, client, manifest)
            db = connect(root)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM results').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT status FROM runs').fetchone()[0], 'interrupted')
            db.close()
            with patch('nim_evaluation.frozen', return_value=protocol), patch.object(protocol, 'ollama', create=True, return_value=({}, {})) as ask:
                public(root, client, manifest)
                self.assertEqual(ask.call_count, 1)
            db = connect(root)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM results').fetchone()[0], 2)
            self.assertEqual(db.execute('SELECT status FROM runs').fetchone()[0], 'complete')
            db.close()


if __name__ == '__main__':
    unittest.main()
