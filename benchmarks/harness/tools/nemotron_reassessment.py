"""Public-only, paired exploratory reassessment. Never overwrites frozen results.

Model input construction does not receive references. Scores are computed afterward.
Raw final answers stay in a new local output directory; reasoning text is not saved.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from nim_evaluation import Client, frozen


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


ARMS = {
    'baseline': dict(thinking=False, budget=2000, temperature=0, top_p=1),
    'budget': dict(thinking=False, budget=16000, temperature=0, top_p=1),
    'reasoning': dict(thinking=True, budget=16000, temperature=0, top_p=1),
    'sampling': dict(thinking=True, budget=16000, temperature=1, top_p=1),
    'definitions': dict(thinking=True, budget=16000, temperature=1, top_p=1, definitions=True),
    'full_document': dict(thinking=True, budget=16000, temperature=1, top_p=1, full=True),
    'ids': dict(thinking=True, budget=16000, temperature=1, top_p=1, ids=True),
    'schema_in_prompt': dict(thinking=True, budget=16000, temperature=1, top_p=1, prompt_schema=True),
}
DEFINITIONS = ('Entailment means the text supports the hypothesis. Contradiction means the text '
               'supports its negation, not merely that support is missing. NotMentioned means neither '
               'is established. Distinguish obligations from permissions, exceptions, scope and parties. '
               'For extraction, return evidence only for the requested clause category; related language '
               'is insufficient. Empty evidence is valid. Do not infer an unstated clause.\n')


def make_body(request, config, model, spans=None):
    # No reference labels or annotation-derived context enters this function.
    messages = [dict(m) for m in request['messages']]
    schema = json.loads(json.dumps(request['schema']))
    if config.get('full'):
        prefix, separator, _ = messages[-1]['content'].partition('\nSOURCE:\n')
        if not separator:
            raise ValueError('Source delimiter missing')
        messages[-1]['content'] = prefix + separator + '\n'.join(f"[{s['id']}] {s['text']}" for s in spans)
        array = schema['properties'].get('ids')
        if array is None:
            array = schema['properties']['matches']['items']['properties']['id']
            array['enum'] = [s['id'] for s in spans]
        else:
            array['items']['enum'] = [s['id'] for s in spans]
    if config.get('definitions'):
        messages[-1]['content'] = DEFINITIONS + messages[-1]['content']
    if config.get('ids') and request['task'] == 'extraction':
        enum = schema['properties']['matches']['items']['properties']['id']['enum']
        schema = {'type': 'object', 'properties': {'ids': {'type': 'array', 'items': {'type': 'string', 'enum': enum}, 'maxItems': 30}}, 'required': ['ids'], 'additionalProperties': False}
        _, separator, source = messages[-1]['content'].partition('\nSOURCE:\n')
        messages[-1]['content'] = ('Select all source IDs answering the question. Return ids: [] if absent. '
                                  'Code will copy each selected span exactly.\nQuestion: ' + request['question']
                                  + separator + source)
    body = {'model': model, 'messages': messages, 'temperature': config['temperature'],
            'top_p': config['top_p'], 'max_tokens': config['budget'], 'stream': False,
            'chat_template_kwargs': {'enable_thinking': config['thinking']},
            'response_format': {'type': 'json_schema', 'json_schema': {'name': 'evidence', 'strict': True, 'schema': schema}}}
    if config.get('prompt_schema'):
        messages[-1]['content'] += '\nReturn JSON matching this schema:\n' + json.dumps(schema)
        body['response_format'] = {'type': 'json_object'}
    return body


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['arm'], row['dataset'])].append(row)
    return [{'arm': arm, 'dataset': dataset, 'attempted': len(group),
             'correct': sum(bool(r.get('metrics', {}).get('correct')) for r in group),
             'failed': sum(r['status'] != 'complete' for r in group),
             'truncated': sum(r.get('finish_reason') == 'length' for r in group),
             'evidence_f1': sum(r.get('metrics', {}).get('evidence_f1', 0) for r in group) / len(group),
             'presence_correct': sum(r.get('presence_correct') is True for r in group),
             'presence_scored': sum(r.get('presence_correct') is not None for r in group)}
            for (arm, dataset), group in sorted(groups.items())]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--arms', nargs='+', choices=ARMS, default=list(ARMS))
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Use a NEW output directory; never reuse stale results')
    pack = REPO / 'handoff/legal-comparison-24'
    requests = json.loads((pack / 'requests.json').read_text(encoding='utf8'))
    references = json.loads((pack / 'references.DO_NOT_SEND_TO_MODEL.json').read_text(encoding='utf8'))
    assert len(requests) == len(references) == 24
    for request, ref in zip(requests, references):
        assert request['case_id'] == ref['case']['id']
        assert ref['case']['dataset'] in ('cuad', 'contractnli')
        assert request['request_sha256'] == sha({'messages': request['messages'], 'schema': request['schema']})
        # The field is not present in the model-facing handoff; recover the question
        # from its exact prompt, not from the scoring reference.
        request['question'] = request['messages'][-1]['content'].split('\nQuestion: ', 1)[1].split('\nSOURCE:\n', 1)[0]
    db = sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True)
    full = {}
    for ref in references:
        case = ref['case']
        dataset = db.execute('SELECT dataset FROM documents WHERE id=?', (case['doc_id'],)).fetchone()
        if not dataset or dataset[0] not in ('cuad', 'contractnli'):
            raise ValueError('Non-public or missing source refused')
        full[case['id']] = json.loads(db.execute('SELECT spans FROM document_spans WHERE doc_id=?', (case['doc_id'],)).fetchone()[0])
    db.close()
    model = os.environ.get('NIM_MODEL', 'nvidia/nemotron-3-nano')
    plan = {'role': 'exploratory; 24 previously exposed cases, not promotion evidence',
            'arms': {a: ARMS[a] for a in args.arms}, 'case_ids': [r['case_id'] for r in requests],
            'requests_sha256': sha(requests), 'references_sha256': sha(references),
            'full_sources_sha256': sha(full), 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'model': model, 'scorer_sha256': hashlib.sha256((REPO / 'protocols/evaluation_v3.py').read_bytes()).hexdigest()}
    scorer = frozen()
    client = None
    if args.run:
        client = Client(os.environ['NIM_BASE_URL'], key=os.environ.get('NIM_API_KEY', ''), model=model, allow_http=True)
        snapshot = client.discover()
        plan['deployment_snapshot_sha256'] = snapshot['deployment_snapshot_sha256']
        limits = [m.get('max_model_len') for m in snapshot['models']['data'] if m['id'] == model]
        context_limit = limits[0] if limits and isinstance(limits[0], int) else 32768
    else:
        context_limit = 32768
    args.out.mkdir(parents=True)
    (args.out / 'PLAN.json').write_text(json.dumps(plan, indent=2), encoding='utf8')
    events = []
    for request, ref in zip(requests, references):
        for arm in args.arms:
            config = ARMS[arm]
            visible = full[request['case_id']] if config.get('full') else ref['visible']
            body = make_body(request, config, model, visible)
            if not args.run:
                continue
            row = {'arm': arm, 'case_id': request['case_id'], 'dataset': ref['case']['dataset'],
                   'request_sha256': sha(body), 'status': 'failed', 'metrics': {'correct': False, 'evidence_f1': 0},
                   'source_spans': len(visible), 'source_bytes': sum(len(s['text'].encode()) for s in visible)}
            started = time.perf_counter()
            try:
                # Conservative byte allowance plus output/template reserve. Never silently truncate.
                if len(json.dumps(body).encode()) + config['budget'] + 2048 > context_limit:
                    raise ValueError('conservative_context_budget_exceeded')
                raw = client.request('/chat/completions', body)
                choice = raw['choices'][0]
                message = choice['message']
                row.update(final_answer=message.get('content'), finish_reason=choice.get('finish_reason'),
                           usage=raw.get('usage', {}), reasoning_present=bool(message.get('reasoning_content') or message.get('reasoning')))
                if row['finish_reason'] != 'stop':
                    raise ValueError('non_stop_generation')
                prediction = json.loads(message['content'])
                if config.get('ids') and request['task'] == 'extraction':
                    evidence = scorer.validate_response(prediction, visible, 'ids')
                else:
                    evidence = scorer.validate_response(prediction, visible, request['task'])
                row.update(status='complete', metrics=scorer.score(ref['case'], prediction, evidence, visible))
                if request['task'] == 'extraction':
                    row['presence_correct'] = bool(evidence) == bool(json.loads(ref['case']['gold'])['answers'])
            except Exception as exc:
                # No exception strings with server URLs, credentials or response content.
                row['error_type'] = type(exc).__name__
                if isinstance(exc, ValueError) and str(exc) in ('conservative_context_budget_exceeded', 'non_stop_generation'):
                    row['error_code'] = str(exc)
            row['seconds'] = time.perf_counter() - started
            events.append(row)
            with (args.out / 'events.LOCAL_ONLY.jsonl').open('a', encoding='utf8') as f:
                f.write(json.dumps(row) + '\n')
            (args.out / 'summary.json').write_text(json.dumps(summarize(events), indent=2), encoding='utf8')
            print(json.dumps({k: row[k] for k in ('arm', 'dataset', 'status', 'seconds')}), flush=True)
    print(json.dumps({'planned_requests': len(requests) * len(args.arms), 'executed': len(events), 'plan_sha256': sha(plan)}))


if __name__ == '__main__':
    main()
