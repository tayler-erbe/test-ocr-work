"""Aggregate local-model progress without exporting source text or private evidence."""
from collections import Counter
import json
from pathlib import Path
import sqlite3
import statistics
import re
from benchmark_tasks import norm
from document_lab import DEFAULT_ROOT, now


def build(root=DEFAULT_ROOT):
    directory = root / 'reports/local-models'; directory.mkdir(parents=True, exist_ok=True)
    journal = directory / 'vision-events.jsonl'
    events = [json.loads(line) for line in journal.read_text(encoding='utf8').splitlines()] if journal.exists() else []
    latest = {row['model']: (row['protocol_hash'], row['deployment_snapshot_sha256']) for row in events}
    active = [row for row in events if (row['protocol_hash'], row['deployment_snapshot_sha256']) == latest[row['model']]]
    # A resumed run must not count a case twice.
    active = list({(r['model'], r['case_id']): r for r in active}.values())
    summaries = []
    for model in sorted(latest):
        for task, expected in [('chartqa_image_only', 20), ('prose_crop_ocr', 50)]:
            rows = [r for r in active if r['model'] == model and r['task'] == task]
            if not rows:
                continue
            summary = {'model': model, 'task': task, 'attempted': len(rows), 'expected': expected,
                       'status': 'complete' if len(rows) == expected else 'running',
                       'failure_rate': statistics.mean(r['status'] != 'complete' for r in rows),
                       'p50_seconds': statistics.median(r['seconds'] for r in rows),
                       'truncations': sum(r['error'] == 'Truncated generation' for r in rows),
                       'returned_thinking_requests': sum(r['generation_info'].get('returned_reasoning_present', False) for r in rows),
                       'errors': dict(Counter(r['error'] for r in rows if r['error']))}
            if task == 'chartqa_image_only':
                summary['accuracy'] = statistics.mean(r['correct'] and r['status'] == 'complete' for r in rows)
            else:
                numbers = lambda text: Counter(re.findall(r'(?<!\w)\d+(?:[.,]\d+)*(?:%)?', norm(text)))
                reference = sum(sum(numbers(r['gold']).values()) for r in rows)
                predicted = sum(sum(numbers(r['observed']).values()) for r in rows)
                matched = sum(sum((numbers(r['gold']) & numbers(r['observed'])).values()) for r in rows)
                summary.update({'cer': sum(r['character_errors'] for r in rows) / max(1, sum(r['reference_chars'] for r in rows)),
                                'numeric_token_recall': matched / reference if reference else None,
                                'numeric_token_precision': matched / predicted if predicted else None})
            summaries.append(summary)
    shared = root / 'reports/nim/additional-summary.json'
    diagnostics = [r for r in json.loads(shared.read_text(encoding='utf8')).get('results', []) if r['model'].startswith('ollama/')] if shared.exists() else []
    db = sqlite3.connect(root / 'library.sqlite3'); db.row_factory = sqlite3.Row
    public = []
    for run in db.execute("SELECT * FROM runs WHERE model LIKE 'ollama/%' ORDER BY started"):
        for dataset in ['cuad', 'contractnli']:
            rows = db.execute('SELECT r.* FROM results r JOIN cases c ON c.id=r.case_id WHERE run_id=? AND c.dataset=?', (run['id'], dataset)).fetchall()
            if rows:
                metrics = [json.loads(r['metrics']) for r in rows]
                public.append({'model': run['model'], 'dataset': dataset, 'attempted': len(rows), 'expected': 100, 'status': run['status'],
                               'accuracy': statistics.mean(m['correct'] for m in metrics), 'evidence_f1': statistics.mean(m['evidence_f1'] for m in metrics),
                               'failure_rate': statistics.mean(r['status'] != 'complete' for r in rows), 'p50_seconds': statistics.median(r['seconds'] for r in rows),
                               'truncations': sum(bool(r['error']) and ('Truncated generation' in r['error'] or 'generation: length' in r['error']) for r in rows)})
    private = {}
    for row in db.execute("SELECT model,status,metadata FROM findings WHERE model LIKE 'ollama/%'"):
        if not json.loads(row['metadata']).get('superseded'):
            counts = private.setdefault(row['model'], Counter()); counts[row['status']] += 1
    db.close()
    deployments = []
    for path in sorted(directory.glob('deployment-*.json')):
        snapshot = json.loads(path.read_text(encoding='utf8'))
        model = snapshot.get('model', {})
        deployments.append({'model': model.get('name'), 'model_digest': model.get('digest'),
                            'details': model.get('details'), 'runtime': snapshot.get('runtime'),
                            'requested_generation_profile': snapshot.get('requested_generation_profile')})
    note = '20 paired chart-image questions and 50 matched prose crops. Running rows are partial and not final scores. Image/table conditions and text extraction are distinct; no full-page or production approval.'
    report = {'generated_at': now(), 'results': summaries, 'note': note, 'public': public, 'private_status_counts': private, 'task_diagnostics': diagnostics, 'deployments': deployments}
    temporary = directory / 'vision-summary.json.tmp'
    temporary.write_text(json.dumps(report, indent=2), encoding='utf8'); temporary.replace(directory / 'vision-summary.json')
    lines = ['# Local vision-model evaluation status', '', 'Generated ' + report['generated_at'], '', note, '',
             '| Model | Task | Cases | Status | Score | Failed | Truncated |', '|---|---|---:|---|---:|---:|---:|']
    for row in summaries:
        score = f"{row['accuracy']:.1%} accuracy" if 'accuracy' in row else f"{row['cer']:.2%} CER"
        lines.append(f"| {row['model']} | {row['task']} | {row['attempted']}/{row['expected']} | {row['status']} | {score} | {row['failure_rate']:.1%} | {row['truncations']} |")
    lines += ['', 'Lower CER is better. Numeric precision/recall are retained in the JSON summary. Returned thinking was observed despite think=false on this Qwen3-VL package; the label records the requested control, not a guarantee. Latency is not an isolated GPU benchmark.', '', '## Public text comparison', '', '| Model | Dataset | Cases | Status | Correctness | Evidence F1 | Failed |', '|---|---|---:|---|---:|---:|---:|']
    for row in public:
        lines.append(f"| {row['model']} | {row['dataset']} | {row['attempted']}/{row['expected']} | {row['status']} | {row['accuracy']:.1%} | {row['evidence_f1']:.3f} | {row['failure_rate']:.1%} |")
    lines += ['', '## Additional diagnostics', '', '```json', json.dumps(diagnostics, indent=2), '```', '', '## Private field statuses', '', '```json', json.dumps(private, indent=2), '```', '',
              'Private accuracy is unknown: no adjudicated private gold labels. Unknown evidence, duplicate IDs, output truncation and incomplete pages do not pass silently. These runs reuse public test cases and use 2000 output tokens versus 600 for the earlier local text baseline. No production model is selected. The external Qwen3-VL 32B results are not included as locally measured results.', '']
    (directory / 'RESULTS.md').write_text('\n'.join(lines), encoding='utf8')
    return report


if __name__ == '__main__':
    report = build()
    print(json.dumps({'vision': [{k: r[k] for k in ['model', 'task', 'attempted', 'status']} for r in report['results']], 'public_rows': len(report['public'])}))
