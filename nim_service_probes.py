"""Bounded synthetic schema and public reasoning probes; final answers only."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

from document_lab import DEFAULT_ROOT, connect
from nim_failure_audit import Capture
from nim_evaluation import Transport, frozen


def main():
    out = DEFAULT_ROOT / 'reports/nim-audit'
    client = Capture(os.environ['NIM_BASE_URL'], key=os.environ.get('NIM_API_KEY', ''), model='nvidia/nemotron-3-nano', allow_http=True, thinking=False, max_tokens=2000)
    rows = []
    schema = {'type': 'object', 'properties': {'answer': {'type': 'string', 'enum': ['SCHEMA_SENTINEL']}}, 'required': ['answer'], 'additionalProperties': False}
    for mode in ['json_schema', 'json_object']:
        for prompt in ['Return {"answer":"SCHEMA_SENTINEL"}.', 'Return {"answer":"OTHER_VALUE"}.']:
            body = {'model': client.model, 'temperature': 0, 'max_tokens': 300, 'stream': False,
                    'chat_template_kwargs': {'enable_thinking': False}, 'messages': [{'role': 'user', 'content': prompt}],
                    'response_format': {'type': 'json_schema', 'json_schema': {'name': 'probe', 'strict': True, 'schema': schema}} if mode == 'json_schema' else {'type': 'json_object'}}
            try:
                client.request('/chat/completions', body)
                rows.append({'mode': mode, 'prompt': prompt, 'raw': client.raw})
            except Exception as exc:
                rows.append({'mode': mode, 'prompt': prompt, 'error': str(exc)})
    # Three CUAD cases (two annotated-present, one absent) and one NLI per
    # reference label, taken deterministically from already exposed probes.
    old = [json.loads(line) for line in (out / 'events.jsonl').read_text().splitlines()]
    db = connect(DEFAULT_ROOT)
    selected, counts = [], {}
    for row in old:
        if row['arm'] != 'original_6000':
            continue
        case = dict(db.execute('SELECT * FROM cases WHERE id=?', (row['case_id'],)).fetchone())
        gold = json.loads(case['gold'])
        key = gold.get('label', 'present' if gold.get('answers') else 'absent')
        limit = 2 if key == 'present' else 1
        if counts.get(key, 0) < limit:
            selected.append((case, row['visible']))
            counts[key] = counts.get(key, 0) + 1
    protocol = frozen()
    existing_path = out / 'service-probes.json'
    previous = json.loads(existing_path.read_text()) if existing_path.exists() else []
    for role in ['reasoning_on_6000_paired_subset', 'json_object_off_6000_paired_subset']:
        client.thinking, client.max_tokens = role.startswith('reasoning'), 6000
        saved_request = client.request
        if role.startswith('json_object'):
            def json_request(path, payload=None):
                if payload is not None:
                    payload = dict(payload, response_format={'type': 'json_object'})
                return saved_request(path, payload)
            client.request = json_request
        protocol.urllib = SimpleNamespace(request=Transport(client))
        for case, visible in selected:
            prior = next((r for r in previous if r.get('role') == role and r.get('case_id') == case['id']), None)
            if prior:
                rows.append(prior)
                continue
            event = {'role': role, 'case_id': case['id'], 'dataset': case['dataset']}
            client.raw = None
            try:
                prediction, _ = protocol.ollama(client.label, case['question'], visible, case['task'])
                evidence = protocol.validate_response(prediction, visible, case['task'])
                event.update(status='complete', metrics=protocol.score(case, prediction, evidence, visible))
            except Exception as exc:
                event.update(status='failed', error=str(exc), metrics={'correct': False, 'evidence_f1': 0})
            event['raw'] = client.raw
            rows.append(event)
            print(json.dumps({k: v for k, v in event.items() if k != 'raw'}), flush=True)
            existing_path.write_text(json.dumps(rows, indent=2), encoding='utf8')
        client.request = saved_request
    db.close()


if __name__ == '__main__':
    main()
