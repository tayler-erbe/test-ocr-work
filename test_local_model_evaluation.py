import base64
import json
import unittest
from unittest.mock import patch
from local_model_evaluation import LocalClient, answer, exact_answer


class LocalVLMTests(unittest.TestCase):
    def test_image_bytes_reach_image_input_without_table_or_gold(self):
        client = LocalClient('test-vlm')
        with patch.object(client, 'chat', return_value={'done_reason': 'stop', 'message': {'content': '{"answer":"12"}'}}) as send:
            result = answer(client, 'Question only', {'type': 'object'}, b'image bytes')
        user = send.call_args.args[0]['messages'][-1]
        self.assertEqual(base64.b64decode(user['images'][0]), b'image bytes')
        self.assertEqual(user['content'], 'Question only')
        self.assertEqual(result, {'answer': '12'})

    def test_requested_thinking_control_does_not_hide_returned_thinking(self):
        client = LocalClient('test-vlm')
        with patch('local_model_evaluation.ollama_request', return_value={'message': {'content': '{}', 'thinking': 'reasoning'}, 'done_reason': 'stop'}) as send:
            client.chat({'messages': [], 'options': {'num_predict': 600}, 'format': {'type': 'object'}})
        body = send.call_args.args[1]
        self.assertFalse(body['think'])
        self.assertEqual(body['options']['num_predict'], 2000)
        self.assertEqual(body['options']['num_ctx'], 32768)
        self.assertTrue(client.last_response_info['returned_reasoning_present'])

    def test_truncated_vision_answer_is_not_scored_as_valid(self):
        client = LocalClient('test-vlm')
        with patch.object(client, 'chat', return_value={'done_reason': 'length', 'message': {'content': '{"answer":"12"}'}}):
            with self.assertRaises(ValueError):
                answer(client, 'question', {}, b'image')

    def test_strict_numeric_comparison_keeps_wrong_units_wrong(self):
        self.assertTrue(exact_answer('1,000', '1000'))
        self.assertFalse(exact_answer('55%', '55'))


if __name__ == '__main__':
    unittest.main()
