"""Produce local reports and a deliberately aggregate-only publishable summary."""
from collections import defaultdict
import csv
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import sqlite3
import subprocess
import urllib.request
import zipfile
from document_lab import DEFAULT_ROOT, connect, now, summary, digest

def reports(root, publish_path=None):
    directory=root/'reports';directory.mkdir(exist_ok=True)
    result=summary(root)
    db=connect(root)
    comparisons=[]
    fresh=[r for r in result['runs'] if r['config'].get('evaluation_role')=='fresh_public_holdout']
    # Keep scorer components visible: an empty-answer baseline can look strong
    # on an imbalanced extraction corpus, and quote-format failures are not a
    # direct measurement of semantic/legal understanding.
    for aggregate in fresh:
        rows=db.execute('SELECT r.*,c.gold,c.task FROM results r JOIN cases c ON c.id=r.case_id WHERE r.run_id=? AND c.dataset=?',(aggregate['run_id'],aggregate['dataset'])).fetchall()
        errors=defaultdict(int);strata=defaultdict(lambda:{'attempted':0,'correct':0});coverage=[]
        for row in rows:
            gold=json.loads(row['gold']);metric=json.loads(row['metrics']);prediction=json.loads(row['prediction'])
            label=gold.get('label','present' if gold.get('answers') else 'absent')
            strata[label]['attempted']+=1;strata[label]['correct']+=int(metric['correct'])
            if row['error']:errors[row['error']]+=1
            if gold.get('answers'):
                quote=' '.join(' '.join(e['text'].split()) for e in prediction.get('evidence',[]))
                coverage.append(all(' '.join(a['text'].split()) in quote for a in gold['answers']))
        majority=max((s['attempted'] for s in strata.values()),default=0)/max(1,len(rows))
        aggregate['scoring_components']={'by_reference_stratum':dict(strata),'majority_label_baseline':majority,'complete_reference_text_coverage_without_precision_gate':sum(coverage)/len(coverage) if coverage else None,'failure_reasons':dict(errors),'interpretation':'Strict evidence proxy and protocol adherence, not normalized private-field or legal accuracy'}
    for dataset in ['cuad','contractnli']:
        eligible=[r for r in fresh if r['dataset']==dataset]
        baseline=next((r for r in eligible if r['model']=='qwen2.5:3b'),None)
        if not baseline:continue
        for candidate in eligible:
            if candidate['model']==baseline['model']:continue
            a={r['case_id']:r for r in db.execute('SELECT r.*,c.doc_id FROM results r JOIN cases c ON c.id=r.case_id WHERE r.run_id=? AND c.dataset=?',(baseline['run_id'],dataset))}
            b={r['case_id']:r for r in db.execute('SELECT r.*,c.doc_id FROM results r JOIN cases c ON c.id=r.case_id WHERE r.run_id=? AND c.dataset=?',(candidate['run_id'],dataset))}
            common=sorted(set(a)&set(b));groups=defaultdict(list)
            for key in common:groups[a[key]['doc_id']].append(int(json.loads(b[key]['metrics'])['correct'])-int(json.loads(a[key]['metrics'])['correct']))
            values=list(groups.values());rng=random.Random(20261015);draws=[]
            for _ in range(1000):
                sampled=[rng.choice(values) for _ in values];draws.append(sum(sum(x) for x in sampled)/sum(len(x) for x in sampled))
            draws.sort()
            comparisons.append({'dataset':dataset,'baseline':baseline['model'],'candidate':candidate['model'],'paired_cases':len(common),'documents':len(values),'correctness_difference':sum(sum(x) for x in values)/sum(len(x) for x in values),'cluster_bootstrap_95ci':[draws[24],draws[974]],'interpretation':'descriptive public benchmark; no production winner without institutional holdout'})
    with (directory/'model-comparison.csv').open('w',newline='',encoding='utf-8') as stream:
        fields=['model','dataset','attempted','documents','accuracy','evidence_f1','failure_rate','p50_seconds','p95_seconds','retrieval_recall','abstention_precision','gate']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in fresh:writer.writerow({k:row[k]['status'] if k=='gate' else row[k] for k in fields})
    inventory={}
    for name in ['cuad','contractnli','acord','chartqa']:
        raw=root/'datasets'/name/'raw'
        path=next(raw.glob('*.zip'),None)
        if path:
            with zipfile.ZipFile(path) as z:
                inventory[name]={'archive_members':len(z.infolist()),'uncompressed_bytes':sum(f.file_size for f in z.infolist()),'stored_bytes':path.stat().st_size}
    try:
        import pyarrow.parquet as pq
        path=root/'datasets/chartqapro/raw/data/test-00000-of-00001.parquet'
        inventory['chartqapro']={'test_rows':pq.ParquetFile(path).metadata.num_rows,'stored_bytes':path.stat().st_size}
    except Exception as exc:inventory['chartqapro']={'inspection_error':str(exc)}
    plan=json.loads((root/'datasets/download-plan.json').read_text(encoding='utf-8'))
    records={}
    for line in (root/'datasets/download-events.jsonl').read_text(encoding='utf-8').splitlines():
        record=json.loads(line);records[(record['dataset'],record['path'])]=record
    acquisition=[]
    for item in plan['datasets']:
        files=[f for f in plan['files'] if f['dataset']==item['id']]
        rs=[records.get((f['dataset'],f['path']),{}) for f in files]
        acquisition.append({'dataset':item['id'],'planned_files':len(files),'verified_files':sum(r.get('status')=='complete' for r in rs),'unavailable_files':sum(r.get('status')=='failed' for r in rs),'verified_bytes':sum(r.get('bytes',0) for r in rs if r.get('status')=='complete'),'source':item['source'],'revision':item.get('revision'),'coverage':item['coverage'],'usage':item['usage']})
    with (directory/'dataset-catalog.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(acquisition[0]));writer.writeheader();writer.writerows(acquisition)
    try:
        with urllib.request.urlopen('http://127.0.0.1:11434/api/version',timeout=20) as response:ollama_version=json.load(response)
    except Exception:ollama_version={'version':'unavailable'}
    gpu=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],capture_output=True,text=True,timeout=20).stdout.strip()
    environment={'python':platform.python_version(),'os':platform.system(),'logical_cpus':os.cpu_count(),'gpu':gpu,'ollama':ollama_version,'packages':{name:importlib.metadata.version(name) for name in ['pdfplumber','pypdfium2','rank-bm25','rapidocr_onnxruntime','onnxruntime','numpy']},'performance_scope':'serial desktop requests; concurrent acquisition/OCR during parts of the run; not isolated L4/server throughput'}
    source_count=[dict(r) for r in db.execute('SELECT dataset,COUNT(*) AS documents,SUM(pages) AS represented_pages FROM documents GROUP BY dataset')]
    for item in source_count:
        if item['dataset']!='private':item['represented_pages']=None
    private_states=[dict(r) for r in db.execute("SELECT status,COUNT(*) AS documents FROM documents WHERE dataset='private' GROUP BY status")]
    findings=[dict(r) for r in db.execute("SELECT status,COUNT(*) AS fields FROM findings WHERE COALESCE(json_extract(metadata,'$.superseded'),0)=0 GROUP BY status")]
    stage_reports={}
    for name in ['ocr-baseline','retrieval-baseline','additional-task-summary','task-coverage']:
        path=directory/(name+'.json')
        if path.exists():stage_reports[name]={k:v for k,v in json.loads(path.read_text(encoding='utf-8')).items() if k!='cases'}
    publish={'generated_at':now(),'scope':'initial local research evaluation; no automatic promotion','environment':environment,'acquisition':acquisition,'archive_inventory':inventory,'source_counts':source_count,'private_source_status_counts':private_states,'private_field_status_counts':findings,'public_holdout_results':fresh,'paired_comparisons':comparisons,'stages':stage_reports,'limitations':['Public data may overlap model pretraining.','CUAD score is a local strict evidence proxy, not the official leaderboard score or normalized-field accuracy.','Public holdout is label-balanced; these rates do not estimate institutional prevalence.','OCR diagnostic uses crops, not full-page reconstruction.','Charts/table structure/classification of document types remain untested unless explicitly scored.','Private contracts have no human gold answers.','Code CI, model gates, source coverage and human acceptance are separate.']}
    publish['quality_policy']=json.loads(Path(__file__).with_name('quality_gates.json').read_text(encoding='utf-8'))
    (directory/'publishable-evaluation-summary.json').write_text(json.dumps(publish,indent=2),encoding='utf-8')
    (directory/'paired-model-comparison.json').write_text(json.dumps(comparisons,indent=2),encoding='utf-8')
    if publish_path:
        publish_path.parent.mkdir(parents=True,exist_ok=True);publish_path.write_text(json.dumps(publish,indent=2),encoding='utf-8')
    db.close()
    print(json.dumps({'holdout_rows':len(fresh),'paired_comparisons':len(comparisons),'datasets':len(acquisition),'verified_files':sum(r['verified_files'] for r in acquisition),'verified_gb':round(sum(r['verified_bytes'] for r in acquisition)/1e9,2),'private_field_status':findings}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT_ROOT);p.add_argument('--publish-path',type=Path);a=p.parse_args();reports(a.root,a.publish_path)
