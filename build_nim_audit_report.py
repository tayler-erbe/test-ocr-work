"""Aggregate public-only failure attribution; no private text is exported."""
import json
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from document_lab import DEFAULT_ROOT


def quote_diagnostics(raw, visible):
    result = Counter()
    try:
        prediction = json.loads(raw['content'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {'not_parseable_json': 1}
    lookup = {s['id']: s for s in visible}
    joined = ''.join(s['text'] for s in visible)
    normalized = lambda x: re.sub(r'\s+', ' ', x).strip()
    for match in prediction.get('matches', []):
        quote, sid = match.get('quote', ''), match.get('id')
        source = lookup.get(sid, {}).get('text', '')
        if sid not in lookup:
            result['unknown_id'] += 1
        elif quote and source.count(quote) == 1:
            result['valid_literal_quote'] += 1
        elif quote and source.count(quote) > 1:
            result['ambiguous_literal_quote'] += 1
        elif quote and quote in joined:
            result['literal_in_visible_context_but_wrong_span'] += 1
        elif quote and normalized(quote) in normalized(joined):
            result['normalized_in_context_not_literal_in_span'] += 1
        elif quote and normalized(quote.replace('\\"', '"')) in normalized(joined):
            result['extra_backslash_escaping_in_quote'] += 1
        else:
            result['not_recovered_by_simple_context_or_escape_checks'] += 1
    return dict(result)


def build(root=DEFAULT_ROOT):
    directory = root / 'reports/nim-audit'
    inventory = json.loads((directory / 'retrieval-audit.json').read_text())
    retrieval = {}
    for dataset in ['cuad', 'contractnli']:
        values = [x['retrieval_recall'] for x in inventory if x['dataset'] == dataset and x['retrieval_recall'] is not None]
        retrieval[dataset] = {'evidence_bearing_cases': len(values), 'all_reference_evidence_visible': sum(v == 1 for v in values),
                              'no_reference_evidence_visible': sum(v == 0 for v in values), 'mean_reference_recall': mean(values)}
    groups = defaultdict(list)
    for row in map(json.loads, (directory / 'events.jsonl').read_text().splitlines()):
        groups[row['arm'], row['dataset']].append(row)
    result = {'role': 'exploratory_posthoc_diagnostic_not_promotion', 'expected_cases_per_arm': 24,
              'retrieval_all_200': retrieval, 'arms': []}
    for (arm, dataset), rows in groups.items():
        quotes = Counter()
        semantic = Counter()
        for row in rows:
            if row.get('raw') and dataset == 'cuad':
                quotes.update(quote_diagnostics(row['raw'], row['visible']))
            reference = next(x['gold'] for x in inventory if x['case_id'] == row['case_id'])
            try:
                parsed = json.loads(row['raw']['content'])
                if dataset == 'contractnli':
                    semantic[reference['label'] + ' -> ' + str(parsed.get('label'))] += 1
                else:
                    absent = not reference['answers']
                    selected = bool(parsed.get('matches', parsed.get('ids')))
                    semantic[('gold_absent' if absent else 'gold_present') + ('_selected' if selected else '_abstained')] += 1
            except (TypeError, KeyError, json.JSONDecodeError):
                semantic['unparseable_final'] += 1
        result['arms'].append({'arm': arm, 'dataset': dataset, 'attempted': len(rows),
                              'correct': sum(bool(r['metrics']['correct']) for r in rows),
                              'failed': sum(r['status'] == 'failed' for r in rows),
                              'truncated': sum(r.get('raw', {}).get('finish_reason') == 'length' for r in rows if r.get('raw')),
                              'evidence_f1': mean(r['metrics']['evidence_f1'] for r in rows),
                              'errors': dict(Counter(r.get('error') for r in rows if r.get('error'))),
                              'quote_diagnostics': dict(quotes), 'semantic_diagnostics': dict(semantic)})
    probes_path = directory / 'service-probes.json'
    if probes_path.exists():
        probes = json.loads(probes_path.read_text())
        roles = sorted({r['role'] for r in probes if r.get('role')})
        result['service_probe_aggregates'] = []
        for role in roles:
            rows = [r for r in probes if r.get('role') == role]
            result['service_probe_aggregates'].append({'role': role, 'attempted': len(rows),
                'correct': sum(bool(r['metrics']['correct']) for r in rows),
                'failed': sum(r['status'] == 'failed' for r in rows),
                'returned_reasoning_present': sum(bool(r.get('raw', {}).get('reasoning_present')) for r in rows if r.get('raw')),
                'truncated': sum(r.get('raw', {}).get('finish_reason') == 'length' for r in rows if r.get('raw'))})
        result['synthetic_schema_probes'] = [{'mode': r['mode'], 'prompt': r['prompt'], 'final': r.get('raw', {}).get('content'),
            'finish_reason': r.get('raw', {}).get('finish_reason')} for r in probes if r.get('mode')]
    result['provenance'] = {'frozen_scoring_sha256': '43f78d7f122a6c1c0df5a484a49569ff20858ad72f0fac784b86615ca1e0d27f',
        'diagnostic_source_sha256': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
             for name in ['nim_failure_audit.py', 'nim_service_probes.py', 'build_nim_audit_report.py']},
        'local_event_journal_sha256': hashlib.sha256((directory / 'events.jsonl').read_bytes()).hexdigest(),
        'raw_final_answers_published': False}
    (directory / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    return result


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
