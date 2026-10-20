"""Run the existing 101 routing/table/arithmetic diagnostic cases on NIM."""
from collections import defaultdict
import argparse
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import statistics
import time
from types import SimpleNamespace

import additional_evaluations as tasks
from document_lab import DEFAULT_ROOT, digest
from nim_evaluation import Client, ServiceError, Transport


def run(root, client):
    cases = tasks.build_cases(root)
    tasks.urllib = SimpleNamespace(request=Transport(client))
    protocol = digest(json.dumps(cases, sort_keys=True) + Path(tasks.__file__).read_text(encoding='utf8'))
    directory = root / 'reports/nim'; directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'additional-events.jsonl'
    existing = [json.loads(line) for line in path.read_text(encoding='utf8').splitlines()] if path.exists() else []
    model = client.label
    cache = {r['case_id']: r for r in existing if r['protocol_hash'] == protocol and r['deployment_snapshot_sha256'] == client.revision}
    rows = []
    for index, case in enumerate(cases):
        if case['id'] in cache:
            rows.append(cache[case['id']]); continue
        started = time.perf_counter(); observed = None; error = None
        try:
            prediction = tasks.ask(model, case['prompt'], case['schema'])
            if case['task'] == 'clause_query_routing':
                if set(prediction) != {'category'} or prediction['category'] not in case['categories']:
                    raise ValueError('Invalid routing response')
                observed = prediction['category']; correct = observed == case['gold']
            elif case['task'] == 'safe_financial_arithmetic':
                if set(prediction) != {'steps'}:
                    raise ValueError('Invalid program schema')
                observed = str(tasks.safe_program(prediction['steps'], case['source']))
                expected = Decimal(str(case['gold']))
                correct = abs(Decimal(observed) - expected) <= max(Decimal('0.00001'), abs(expected) * Decimal('0.0001'))
            else:
                if set(prediction) != {'answer'} or not isinstance(prediction['answer'], str):
                    raise ValueError('Invalid answer schema')
                observed = prediction['answer'].strip().lower(); expected = case['gold'].strip().lower()
                try:
                    correct = Decimal(observed.replace(',', '')) == Decimal(expected.replace(',', ''))
                except InvalidOperation:
                    correct = observed == expected
            status = 'complete'
        except ServiceError:
            raise
        except Exception as exc:
            correct = False; status = 'failed'; error = str(exc)
        row = {'model': model, 'case_id': case['id'], 'task': case['task'], 'gold': case['gold'], 'observed': observed,
               'correct': bool(correct), 'status': status, 'error': error, 'seconds': time.perf_counter() - started,
               'protocol_hash': protocol, 'deployment_snapshot_sha256': client.revision, 'role': 'api_task_diagnostic'}
        with path.open('a', encoding='utf8') as stream:
            stream.write(json.dumps(row) + '\n')
        rows.append(row)
        print(json.dumps({'diagnostic_progress': index + 1, 'total': len(cases), 'task': case['task'], 'status': status}), flush=True)
    groups = defaultdict(list)
    for row in rows:
        groups[row['task']].append(row)
    summary = []
    for task, group in groups.items():
        result = {'model': model, 'task': task, 'attempted': len(group), 'accuracy': statistics.mean(r['correct'] for r in group),
                  'failure_rate': statistics.mean(r['status'] != 'complete' for r in group), 'p50_seconds': statistics.median(r['seconds'] for r in group), 'role': 'api_task_diagnostic'}
        if task == 'clause_query_routing':
            f1 = []
            for label in sorted({r['gold'] for r in group}):
                tp = sum(r['gold'] == label and r['observed'] == label for r in group)
                fp = sum(r['gold'] != label and r['observed'] == label for r in group)
                fn = sum(r['gold'] == label and r['observed'] != label for r in group)
                f1.append(2 * tp / max(1, 2 * tp + fp + fn))
            result['macro_f1'] = statistics.mean(f1)
        summary.append(result)
    summary_path = directory / 'additional-summary.json'
    prior = json.loads(summary_path.read_text(encoding='utf8')).get('results', []) if summary_path.exists() else []
    combined = [r for r in prior if r['model'] != model] + summary
    summary_path.write_text(json.dumps({'results': combined, 'note': 'Same existing diagnostic cases; labels distinguish generation settings. Table-only chart QA is not vision; arithmetic is constrained tool-protocol performance.'}, indent=2), encoding='utf8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-http', action='store_true')
    args = parser.parse_args()
    client = Client(os.environ['NIM_BASE_URL'], os.getenv('NIM_API_KEY', ''), os.getenv('NIM_MODEL'), allow_http=args.allow_http)
    client.discover()
    run(DEFAULT_ROOT, client)
