import json
import unittest
from unittest.mock import patch
import urllib.request
from nim_evaluation import Client, ServiceError, Transport, frozen


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


if __name__ == '__main__':
    unittest.main()
