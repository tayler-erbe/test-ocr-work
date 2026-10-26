"""Create and validate human reference labels without treating blanks as absence."""
import argparse
import csv
import json
from pathlib import Path
from document_lab import DEFAULT_ROOT, connect
from local_demo import FIELDS

COLUMNS=['doc_id','source_sha256','field','presence','expected_value','gold_quote','pdf_pages','reviewed_all_pages','reviewer','adjudicator','review_status','notes']

def initialize(root, path):
    if path.exists():raise ValueError('Annotation file already exists; never overwrite human labels')
    db=connect(root);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=COLUMNS);writer.writeheader()
        for doc in db.execute("SELECT id,sha256 FROM documents WHERE dataset='private' ORDER BY id"):
            for field in FIELDS:writer.writerow(dict(doc_id=doc['id'],source_sha256=doc['sha256'],field=field,presence='unlabeled',review_status='draft'))
    db.close();print('Created blank reference template: '+str(path))

def validate(root,path):
    db=connect(root);docs={d['id']:d for d in db.execute("SELECT * FROM documents WHERE dataset='private'")};db.close()
    with path.open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream))
    errors=[];seen=set();ready=0
    for index,row in enumerate(rows,2):
        reasons=[];doc=docs.get(row.get('doc_id'));key=(row.get('doc_id'),row.get('field'))
        if key in seen:reasons.append('Duplicate document/field label')
        seen.add(key)
        if not doc:reasons.append('Unknown document')
        elif row.get('source_sha256')!=doc['sha256']:reasons.append('Source hash changed')
        if row.get('field') not in FIELDS:reasons.append('Unknown field')
        presence=row.get('presence')
        if presence not in ['present','absent','ambiguous']:reasons.append('Unlabeled reference; blank is not absence')
        if not row.get('reviewer','').strip():reasons.append('Reviewer required')
        if row.get('review_status')!='adjudicated' or not row.get('adjudicator','').strip():reasons.append('Adjudication required before scoring')
        if presence=='present':
            if not row.get('gold_quote','').strip() or not row.get('expected_value','').strip():reasons.append('Present term needs reference value and image-checked quotation')
            try:
                pages=[int(x.strip()) for x in row.get('pdf_pages','').split(';')]
                if not doc or any(p<1 or p>doc['pages'] for p in pages):reasons.append('Page outside source PDF')
            except ValueError:reasons.append('Use semicolon-separated physical PDF page numbers')
        if presence=='absent':
            if row.get('reviewed_all_pages')!='yes':reasons.append('Absence requires explicit complete-document review')
            if row.get('expected_value','').strip() or row.get('gold_quote','').strip():reasons.append('Absent term cannot contain a positive value/quote')
        if presence=='ambiguous' and not row.get('notes','').strip():reasons.append('Ambiguity needs an explanation')
        if reasons:errors.append({'row':index,'reasons':reasons})
        else:ready+=1
    expected={(doc_id,field) for doc_id in docs for field in FIELDS}
    missing=len(expected-seen)
    result={'rows':len(rows),'scoring_ready_rows':ready,'missing_document_fields':missing,'validation_errors':errors,'ready_for_private_scoring':not errors and missing==0,'note':'This validates annotation structure/provenance, not semantic truth. Quotes must be checked against page images, not merely OCR.'}
    print(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT_ROOT);p.add_argument('operation',choices=['init','validate']);p.add_argument('--file',type=Path);a=p.parse_args();path=a.file or a.root/'evaluation/private-gold-template.csv'
    if a.operation=='init':initialize(a.root,path)
    else:raise SystemExit(0 if validate(a.root,path)['ready_for_private_scoring'] else 2)
