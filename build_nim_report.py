"""Export aggregate-only NIM comparison results; never export private evidence."""
from collections import Counter
import csv
import json
from pathlib import Path
import sqlite3
import statistics
from document_lab import DEFAULT_ROOT, now


def build(root=DEFAULT_ROOT):
    db = sqlite3.connect(root / 'library.sqlite3'); db.row_factory = sqlite3.Row
    runs = []
    for run in db.execute('SELECT * FROM runs ORDER BY started'):
        config = json.loads(run['config'])
        role = config.get('evaluation_role')
        if role not in ['fresh_public_holdout', 'api_comparison_same_public_holdout'] or (role.startswith('api_') and config.get('cases') != 200):
            continue
        for dataset in ['cuad', 'contractnli']:
            rows = db.execute('SELECT r.*,c.doc_id FROM results r JOIN cases c ON c.id=r.case_id WHERE run_id=? AND c.dataset=?', (run['id'], dataset)).fetchall()
            if not rows:
                continue
            metrics = [json.loads(r['metrics']) for r in rows]
            runs.append({'model': run['model'], 'dataset': dataset, 'run_id': run['id'], 'run_status': run['status'],
                         'role': role, 'attempted': len(rows), 'documents': len({r['doc_id'] for r in rows}),
                         'accuracy': statistics.mean(bool(m['correct']) for m in metrics),
                         'evidence_f1': statistics.mean(m['evidence_f1'] for m in metrics),
                         'failure_rate': statistics.mean(r['status'] != 'complete' for r in rows),
                         'truncations': sum(bool(r['error']) and 'generation: length' in r['error'] for r in rows),
                         'generation_profile': config.get('generation_profile', {'server_reasoning': 'default', 'max_tokens': config.get('num_predict')}),
                         'p50_seconds': statistics.median(r['seconds'] for r in rows),
                         'errors': dict(Counter(r['error'] for r in rows if r['error']))})
    private_rows = db.execute("SELECT f.*,d.status AS source_status FROM findings f JOIN documents d ON d.id=f.doc_id WHERE f.model LIKE 'nim/%'").fetchall()
    active = [r for r in private_rows if not json.loads(r['metadata']).get('superseded')]
    private = {'documents_accounted_for': len({r['doc_id'] for r in active}), 'fields': len(active),
               'status_counts': dict(Counter(r['status'] for r in active)), 'accuracy': None, 'gold_status': 'unlabeled'}
    private['by_model_configuration'] = {model: {'fields': sum(r['model'] == model for r in active),
                                              'status_counts': dict(Counter(r['status'] for r in active if r['model'] == model))}
                                         for model in sorted({r['model'] for r in active})}
    extra_path = root / 'reports/nim/additional-summary.json'
    extra = json.loads(extra_path.read_text(encoding='utf8')) if extra_path.exists() else {'results': [], 'status': 'pending'}
    discovery_path = root / 'reports/nim/deployment.json'
    discovery = json.loads(discovery_path.read_text(encoding='utf8')) if discovery_path.exists() else {}
    metadata = discovery.get('deployment', {}).get('/metadata', {})
    model = discovery.get('selected_model')
    model_info = next((m for m in discovery.get('models', {}).get('data', []) if m.get('id') == model), {})
    deployment = {'model_alias': model, 'artifacts': [m.get('shortName') for m in metadata.get('modelInfo', [])],
                  'nim_release': discovery.get('deployment', {}).get('/version', {}).get('release'),
                  'advertised_context': model_info.get('max_model_len'), 'gpu_hardware': 'unknown',
                  'deployment_snapshot_sha256': discovery.get('deployment_snapshot_sha256')}
    report = {'generated_at': now(), 'public': runs, 'private': private, 'additional': extra,
              'deployment': deployment,
              'limits': ['Public scores are strict local evidence proxies, not official leaderboard results.', 'API reuses previously exposed public cases; tuning after observing failures is exploratory.', 'Baseline: 600 public and 1500 private output tokens with server-default reasoning. Tuned: 2000 tokens and enable_thinking=false; the two settings change together.', 'Local task diagnostics used 500 output tokens; tuned API diagnostics use 2000. This is a configuration comparison, not a controlled parameter-count experiment.', 'Latency includes network and queueing; it cannot identify hardware.', 'Two unread source pages remain blocked.', 'Private gold labels are absent.', 'ChartQA is table-only, not image understanding.', 'No production promotion.']}
    dest = root / 'reports/nim'; dest.mkdir(exist_ok=True, parents=True)
    (dest / 'aggregate-summary.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    columns = ['model', 'dataset', 'attempted', 'accuracy', 'evidence_f1', 'failure_rate', 'truncations', 'p50_seconds', 'run_status', 'role']
    with (dest / 'model-comparison.csv').open('w', newline='', encoding='utf8') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore'); writer.writeheader(); writer.writerows(runs)
    lines = ['# Institutional Nemotron API comparison', '', 'Generated ' + report['generated_at'], '',
             'This is a measured API comparison against the saved local runs. It is not a fresh institutional holdout or production approval. Public scoring, prompts, retrieval and output budgets are retained; transport, backend defaults, quantization and hardware differ.', '',
             '## Public evidence tasks', '', '| Model / configuration | Task | Cases | Correctness | Evidence F1 | Failed | Truncated | Median seconds | Run status |', '|---|---|---:|---:|---:|---:|---:|---:|---|']
    for row in runs:
        lines.append(f"| {row['model']} | {row['dataset']} | {row['attempted']} | {row['accuracy']:.1%} | {row['evidence_f1']:.3f} | {row['failure_rate']:.1%} | {row['truncations']} | {row['p50_seconds']:.2f} | {row['run_status']} |")
    lines += ['', 'CUAD has a 50% always-empty baseline; ContractNLI has a 34% majority-label baseline on these cases. Errors count as incorrect. These scores do not establish normalized private field accuracy.', '', '## API error breakdown', '']
    for row in runs:
        if row['model'].startswith('nim/'):
            lines.append('- ' + row['dataset'] + ': ' + json.dumps(row['errors']))
    lines += ['', '## Supplied PDFs', '', f"Documents accounted for: {private['documents_accounted_for']} of 12. Active fields: {private['fields']}.", '', json.dumps(private['status_counts']), '', 'Private fields are evidence proposals or explicit failures/blocks. Human gold labels are absent, so private accuracy is unknown.', '', '## Additional task diagnostics', '', '| Task | Cases | Accuracy | Failed | Median seconds |', '|---|---:|---:|---:|---:|']
    lines[-3:] = ['', '| Model / configuration | Task | Cases | Accuracy | Failed | Median seconds |', '|---|---|---:|---:|---:|---:|']
    for row in extra.get('results', []):
        lines.append(f"| {row['model']} | {row['task']} | {row['attempted']} | {row['accuracy']:.1%} | {row['failure_rate']:.1%} | {row['p50_seconds']:.2f} |")
    lines += ['', 'Private results by configuration: ' + json.dumps(private['by_model_configuration']), '']
    lines += ['', 'Routing is clause-query category routing, not institutional document classification. ChartQA uses supplied tables, not chart images. FinQA measures a restricted arithmetic tool protocol, not general math ability.', '', '## Deployment and interpretation', '', 'Observed deployment: ' + json.dumps(deployment) + '. The metadata did not establish GPU model/count or free VRAM. The service URL and raw infrastructure metadata are retained locally, not published.', '']
    lines += ['- ' + limit for limit in report['limits']]
    (dest / 'RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    db.close()
    return report


if __name__ == '__main__':
    report = build()
    print(json.dumps({'public_rows': len(report['public']), 'private': report['private'], 'additional_tasks': len(report['additional'].get('results', []))}))
