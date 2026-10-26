"""Recompute retrieval recall before generation, including failed model attempts.

Non-whitespace source characters count toward answer coverage; inter-line
whitespace gaps must not make otherwise-present reference text disappear.
"""
from bisect import bisect_right
import json
from pathlib import Path
from document_lab import DEFAULT_ROOT, connect, digest, now
from protocols.evaluation_v3 import select_context

def audit(root):
    db=connect(root);manifest=json.loads((root/'evaluation/frozen_public_holdout.json').read_text(encoding='utf-8'));cases={}
    for case_id in manifest['case_ids']:
        case=db.execute('SELECT * FROM cases WHERE id=?',(case_id,)).fetchone();spans=json.loads(db.execute('SELECT spans FROM document_spans WHERE doc_id=?',(case['doc_id'],)).fetchone()[0]);visible=select_context(spans,case['question']);gold=json.loads(case['gold'])
        if case['task']=='nli':
            expected=set(gold['ids']);recall=len(expected&{s['id'] for s in visible})/len(expected) if expected else None
        else:
            ranges=sorted((s['start'],s['end']) for s in visible);starts=[r[0] for r in ranges];coverage=[]
            for answer in gold['answers']:
                covered=True
                for offset,char in enumerate(answer['text']):
                    if char.isspace():continue
                    pos=answer['answer_start']+offset;index=bisect_right(starts,pos)-1
                    if index<0 or ranges[index][1]<=pos:covered=False;break
                coverage.append(covered)
            recall=sum(coverage)/len(coverage) if coverage else None
        cases[case_id]={'recall':recall,'visible_ids_sha256':digest(json.dumps([s['id'] for s in visible]))}
    db.close();dest=root/'reports/context-recall-audit.json';dest.write_text(json.dumps({'created_at':now(),'case_hash':digest(json.dumps(manifest['case_ids'])),'method':'pre_generation_nonwhitespace_reference_coverage_v1','cases':cases},indent=2),encoding='utf-8');print('Audited context recall for '+str(len(cases))+' fixed cases')

if __name__=='__main__':audit(DEFAULT_ROOT)
