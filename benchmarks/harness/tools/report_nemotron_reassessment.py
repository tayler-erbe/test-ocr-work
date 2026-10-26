"""Aggregate public reassessment logs locally; never publishes source/answer text."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import statistics
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from nim_evaluation import frozen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--pack', type=Path, default=REPO / 'handoff/legal-comparison-24')
    args = parser.parse_args()
    refs = json.loads((args.pack / 'references.DO_NOT_SEND_TO_MODEL.json').read_text())
    plan = json.loads((args.run / 'PLAN.json').read_text())
    expected_rows = len(refs) * len(plan['arms'])
    lookup = {r['case']['id']: r for r in refs}
    rows = [json.loads(line) for line in (args.run / 'events.LOCAL_ONLY.jsonl').read_text().splitlines()]
    import sqlite3
    db = sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True)
    scorer = frozen()
    detailed = []
    for row in rows:
        ref = lookup[row['case_id']]
        case = ref['case']
        gold = json.loads(case['gold'])
        visible = ref['visible']
        if row['arm'] == 'full_document':
            visible = json.loads(db.execute('SELECT spans FROM document_spans WHERE doc_id=?', (case['doc_id'],)).fetchone()[0])
        item = dict(row, doc_id=case['doc_id'])
        try:
            prediction = json.loads(row.get('final_answer') or '')
            if case['task'] == 'nli':
                item['label_correct_ignoring_evidence'] = prediction.get('label') == gold['label']
                item['gold_label'] = gold['label']
                item['predicted_label'] = prediction.get('label', 'invalid')
                kind = 'nli'
            else:
                key = 'ids' if row['arm'] == 'ids' else 'matches'
                if isinstance(prediction, dict) and isinstance(prediction.get(key), list):
                    item['raw_presence_correct'] = bool(prediction[key]) == bool(gold['answers'])
                    item['gold_present'] = bool(gold['answers'])
                    item['raw_predicted_present'] = bool(prediction[key])
                kind = 'ids' if row['arm'] == 'ids' else 'extraction'
            try:
                scorer.validate_response(prediction, visible, kind)
                item['evidence_validation'] = 'valid'
            except ValueError as exc:
                # Frozen validator messages are fixed strings without source content.
                item['evidence_validation'] = str(exc)
            if case['task'] == 'extraction' and isinstance(prediction, dict) and isinstance(prediction.get('matches'), list):
                valid, total, texts = 0, 0, []
                for match in prediction['matches']:
                    total += 1
                    try:
                        evidence = scorer.validate_response({'matches': [match]}, visible, 'extraction')
                        valid += 1
                        texts.extend(x['text'] for x in evidence)
                    except ValueError:
                        pass
                item.update(literal_matches_valid=valid, literal_matches_total=total)
                expected = gold['answers']
                if expected:
                    import re
                    normalize = lambda text: re.sub(r'\s+', ' ', text).strip()
                    joined = normalize('\n'.join(texts))
                    item['reference_answer_recovery'] = sum(normalize(a['text']) in joined for a in expected) / len(expected)
        except (ValueError, TypeError, AttributeError):
            item['evidence_validation'] = 'invalid_or_missing_json'
        detailed.append(item)
    db.close()
    groups = defaultdict(list)
    for row in detailed:
        groups[(row['arm'], row['dataset'])].append(row)
    summary = []
    for (arm, dataset), group in sorted(groups.items()):
        result = {'arm': arm, 'dataset': dataset, 'n': len(group), 'documents': len({r['doc_id'] for r in group}),
                  'correct': sum(r['metrics']['correct'] for r in group),
                  'accepted': sum(r['status'] == 'complete' for r in group),
                  'truncated': sum(r.get('finish_reason') == 'length' for r in group),
                  'validation_outcomes': dict(Counter(r['evidence_validation'] for r in group)),
                  'evidence_f1': statistics.mean(r['metrics'].get('evidence_f1', 0) for r in group),
                  'median_seconds': statistics.median(r['seconds'] for r in group),
                  'reasoning_observed': sum(r.get('reasoning_present', False) for r in group)}
        for metric in ('raw_presence_correct', 'label_correct_ignoring_evidence', 'reference_answer_recovery'):
            observed = [r[metric] for r in group if metric in r]
            result[metric] = {'n': len(observed), 'mean': statistics.mean(observed) if observed else None}
        result['false_present'] = sum(r.get('gold_present') is False and r.get('raw_predicted_present') is True for r in group)
        result['absent_cases_with_parseable_presence'] = sum(r.get('gold_present') is False for r in group)
        result['nli_confusion'] = dict(Counter(str(r['gold_label']) + ' -> ' + str(r['predicted_label']) for r in group if 'gold_label' in r))
        summary.append(result)
    pairs = []
    # Pre-specified exploratory contrasts. No p-values or confirmatory claims.
    for arm, comparator in [('budget', 'baseline'), ('reasoning', 'budget'), ('sampling', 'reasoning'),
                            ('definitions', 'sampling'), ('full_document', 'sampling'),
                            ('ids', 'sampling'), ('schema_in_prompt', 'sampling'),
                            ('on_16000', 'off_16000')]:
        for dataset in ('cuad', 'contractnli'):
            left = {r['case_id']: r for r in groups.get((arm, dataset), [])}
            right = {r['case_id']: r for r in groups.get((comparator, dataset), [])}
            expected_cases = sum(r['case']['dataset'] == dataset for r in refs)
            if len(left) != expected_cases or left.keys() != right.keys():
                continue
            clusters = defaultdict(list)
            for case_id, row in left.items():
                clusters[row['doc_id']].append(int(row['metrics']['correct']) - int(right[case_id]['metrics']['correct']))
            documents = list(clusters)
            rng = random.Random(20261026)
            draws = []
            for _ in range(3000):
                values = [v for doc in rng.choices(documents, k=len(documents)) for v in clusters[doc]]
                draws.append(statistics.mean(values))
            draws.sort()
            pairs.append({'arm': arm, 'comparator': comparator, 'dataset': dataset,
                          'paired_cases': len(left), 'documents': len(documents),
                          'accuracy_difference': statistics.mean(v for values in clusters.values() for v in values),
                          'exploratory_document_bootstrap_95_percentile_interval': [draws[75], draws[2924]]})
    report = {'status': 'complete' if len(rows) == expected_rows else 'partial', 'attempts': len(rows),
              'expected_attempts': expected_rows, 'cases': len(refs),
              'limitations': 'See frozen run plan for case exposure and configuration-selection status. Repeated stochastic draws absent; no model rejection or production approval. Raw-presence and label-only metrics ignore evidence validity and are diagnostics only.',
              'groups': summary, 'paired_contrasts': pairs}
    (args.run / 'AGGREGATE_REPORT.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'status': report['status'], 'attempts': len(rows), 'groups': [{k:r[k] for k in ('arm','dataset','n','correct','accepted','truncated')} for r in summary]}, indent=2))


if __name__ == '__main__':
    main()
