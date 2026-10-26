"""Paired reasoning-on/off confirmation on a previously frozen public pack.

Both arms use 16k output and temperature zero. No tuning on this set.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from nemotron_reassessment import make_body, sha, summarize

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from nim_evaluation import Client, frozen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pack', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Use a new output directory')
    receipt = json.loads((args.pack / 'RECEIPT.json').read_text())
    for name, digest in receipt['files'].items():
        assert hashlib.sha256((args.pack / name).read_bytes()).hexdigest() == digest
    requests = json.loads((args.pack / 'requests.json').read_text())
    references = json.loads((args.pack / 'references.DO_NOT_SEND_TO_MODEL.json').read_text())
    assert len(requests) == len(references) == 60
    assert len({r['case']['doc_id'] for r in references}) == 60
    for request, reference in zip(requests, references):
        assert request['case_id'] == reference['case']['id']
        assert reference['case']['dataset'] in ('cuad', 'contractnli')
        assert request['request_sha256'] == sha({'messages': request['messages'], 'schema': request['schema']})
    arms = {'off_16000': {'thinking': False, 'budget': 16000, 'temperature': 0, 'top_p': 1},
            'on_16000': {'thinking': True, 'budget': 16000, 'temperature': 0, 'top_p': 1}}
    model = os.environ.get('NIM_MODEL', 'nvidia/nemotron-3-nano')
    plan = {'purpose': 'fixed reasoning control; no selection or tuning on these cases',
            'arms': arms, 'pack_receipt_sha256': sha(receipt), 'cases': 60, 'documents': 60,
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'request_builder_sha256': hashlib.sha256((REPO / 'tools/nemotron_reassessment.py').read_bytes()).hexdigest(),
            'model': model, 'limitations': receipt['limitations']}
    scorer = frozen()
    client = None
    if args.run:
        client = Client(os.environ['NIM_BASE_URL'], key=os.environ.get('NIM_API_KEY', ''), model=model, allow_http=True)
        snapshot = client.discover()
        plan['deployment_snapshot_sha256'] = snapshot['deployment_snapshot_sha256']
    args.out.mkdir(parents=True)
    (args.out / 'PLAN.json').write_text(json.dumps(plan, indent=2))
    rows = []
    for index, (request, reference) in enumerate(zip(requests, references)):
        # Balance temporal ordering without changing model settings or cases.
        order = list(arms) if index % 2 == 0 else list(reversed(arms))
        for name in order:
            body = make_body(request, arms[name], model)
            if not args.run:
                continue
            row = {'arm': name, 'case_id': request['case_id'], 'dataset': reference['case']['dataset'],
                   'request_sha256': sha(body), 'status': 'failed', 'metrics': {'correct': False, 'evidence_f1': 0}}
            started = time.perf_counter()
            try:
                raw = client.request('/chat/completions', body)
                choice = raw['choices'][0]
                message = choice['message']
                row.update(final_answer=message.get('content'), finish_reason=choice.get('finish_reason'),
                           usage=raw.get('usage', {}), reasoning_present=bool(message.get('reasoning_content') or message.get('reasoning')))
                if row['finish_reason'] != 'stop':
                    raise ValueError('non_stop_generation')
                prediction = json.loads(message['content'])
                evidence = scorer.validate_response(prediction, reference['visible'], request['task'])
                row.update(status='complete', metrics=scorer.score(reference['case'], prediction, evidence, reference['visible']))
            except Exception as exc:
                row['error_type'] = type(exc).__name__
            row['seconds'] = time.perf_counter() - started
            rows.append(row)
            with (args.out / 'events.LOCAL_ONLY.jsonl').open('a') as f:
                f.write(json.dumps(row) + '\n')
            (args.out / 'summary.json').write_text(json.dumps(summarize(rows), indent=2))
            print(json.dumps({k: row[k] for k in ('arm', 'dataset', 'status', 'seconds')}), flush=True)
    print(json.dumps({'planned': 120, 'executed': len(rows), 'plan_sha256': sha(plan)}))


if __name__ == '__main__':
    main()
