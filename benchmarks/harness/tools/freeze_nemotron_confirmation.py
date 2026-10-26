"""Freeze public cases from documents absent from locally recorded prior runs.

Never invokes a model. Label-stratified selection is scoring-side only.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from nim_evaluation import frozen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Refuse to replace an existing selection')
    db = sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    exposed = {r[0] for r in db.execute("SELECT DISTINCT c.doc_id FROM results r JOIN cases c ON c.id=r.case_id WHERE c.dataset IN ('cuad','contractnli')")}
    # Include the entire original 200-case manifest, even if a result was never saved.
    manifest = args.db.parent / 'evaluation/frozen_public_holdout.json'
    for case_id in json.loads(manifest.read_text())['case_ids']:
        row = db.execute('SELECT doc_id FROM cases WHERE id=?', (case_id,)).fetchone()
        if row:
            exposed.add(row[0])
    candidates = [dict(r) for r in db.execute("SELECT * FROM cases WHERE split='test' AND dataset IN ('cuad','contractnli')") if r['doc_id'] not in exposed]
    def stratum(case):
        gold = json.loads(case['gold'])
        return case['dataset'] + ':' + gold.get('label', 'present' if gold.get('answers') else 'absent')
    targets = {'cuad:present': 15, 'cuad:absent': 15, 'contractnli:Entailment': 10,
               'contractnli:Contradiction': 10, 'contractnli:NotMentioned': 10}
    groups = {key: sorted([c for c in candidates if stratum(c) == key], key=lambda c: hashlib.sha256(('20261026:' + c['id']).encode()).hexdigest()) for key in targets}
    counts, chosen, used = Counter(), [], set()
    while any(counts[key] < count for key, count in targets.items()):
        progressed = False
        for key, target in targets.items():
            if counts[key] >= target:
                continue
            candidate = next((c for c in groups[key] if c['doc_id'] not in used), None)
            if candidate:
                chosen.append(candidate)
                used.add(candidate['doc_id'])
                counts[key] += 1
                progressed = True
        if not progressed:
            raise ValueError('Insufficient unused documents for fixed target strata')
    scorer = frozen()
    requests, references = [], []
    for case in chosen:
        spans = json.loads(db.execute('SELECT spans FROM document_spans WHERE doc_id=?', (case['doc_id'],)).fetchone()[0])
        visible = scorer.select_context(spans, case['question'])
        captured = {}
        class StopCapture(Exception):
            pass
        class NoNetwork:
            def Request(self, url, data, headers):
                captured.update(json.loads(data))
                raise StopCapture()
        original = scorer.urllib
        scorer.urllib = type('Namespace', (), {'request': NoNetwork()})()
        try:
            scorer.ollama('not-a-live-model', case['question'], visible, case['task'])
        except StopCapture:
            pass
        finally:
            scorer.urllib = original
        if not captured:
            raise ValueError('Prompt capture failed; never substitute a modified prompt')
        digest = hashlib.sha256(json.dumps({'messages': captured['messages'], 'schema': captured['format']}, sort_keys=True).encode()).hexdigest()
        requests.append({'case_id': case['id'], 'task': case['task'], 'temperature': 0, 'max_tokens': 2000,
                         'enable_thinking': False, 'messages': captured['messages'], 'schema': captured['format'], 'request_sha256': digest})
        references.append({'case': case, 'visible': visible})
    db.close()
    args.out.mkdir(parents=True)
    for name, data in [('requests.json', requests), ('references.DO_NOT_SEND_TO_MODEL.json', references)]:
        (args.out / name).write_text(json.dumps(data, indent=2), encoding='utf8')
    receipt = {'cases': len(chosen), 'documents': len(used), 'strata': dict(counts),
               'selection': 'seeded hash order; round robin label strata; one case per document; exclusions from local results and original frozen manifest',
               'limitations': 'Unused in locally recorded runs; not proof of absence from other machines, unrecorded experiments, or model pretraining.',
               'source_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.out.iterdir()}}
    (args.out / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps({'cases': len(chosen), 'documents': len(used), 'strata': dict(counts)}))


if __name__ == '__main__':
    main()
