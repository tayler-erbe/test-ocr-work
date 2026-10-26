"""Resume large pinned archives with validated parallel HTTP byte ranges.

Run only when the ordinary downloader is stopped. Never run two writers against
the same library. Final bytes must match the publisher SHA-256 when available.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import shutil
import time
import urllib.request
from acquire_datasets import HEADERS, sha256, safe_target, transfer
from document_lab import DEFAULT_ROOT, now, digest

def request_range(item, start, end):
    return urllib.request.urlopen(urllib.request.Request(item["url"], headers=dict(HEADERS, Range=f"bytes={start}-{end}")), timeout=120)

def segment(item, start, end, path):
    expected = end-start+1
    if path.exists() and path.stat().st_size == expected:
        return path
    for attempt in range(5):
        try:
            offset = path.stat().st_size if path.exists() else 0
            if offset > expected:
                raise ValueError("Oversized partial segment")
            with request_range(item, start+offset, end) as response:
                cr = response.headers.get("Content-Range", "")
                if response.status != 206 or not cr.startswith(f"bytes {start+offset}-{end}/"):
                    raise ValueError("Server did not honor the exact segment range")
                with path.open("ab" if offset else "wb") as stream:
                    shutil.copyfileobj(response, stream, 1024*1024)
            if path.stat().st_size != expected:
                raise ValueError("Segment size mismatch")
            return path
        except Exception:
            if attempt == 4:
                raise
            time.sleep(min(2**attempt, 8))

def main(root, workers):
    plan = json.loads((root/'download-plan.json').read_text(encoding='utf-8'))
    latest = {}
    for line in (root/'download-events.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line); latest[(row['dataset'],row['path'])]=row
    pending=[i for i in plan['files'] if latest.get((i['dataset'],i['path']),{}).get('status')!='complete']
    large, other=[],[]
    for item in pending:
        if item.get('size',0)>500_000_000 or item['path']=='DocLayNet_core.zip':large.append(item)
        else:other.append(item)
    chunks, layouts={},[]
    for item in large:
        target=safe_target(root,item['dataset']+'/raw/'+item['path']); target.parent.mkdir(parents=True,exist_ok=True)
        partial=target.with_name(target.name+'.part')
        with request_range(item,0,0) as response:
            match=re.fullmatch(r'bytes 0-0/(\d+)',response.headers.get('Content-Range',''))
            if response.status!=206 or not match:raise ValueError('Cannot segment '+item['path'])
            size=int(match[1])
        prefix=partial.stat().st_size if partial.exists() else 0
        if prefix>size:raise ValueError('Oversized existing partial archive')
        directory=root/'segments'/digest(item['dataset']+'/'+item['path'])[:20];directory.mkdir(parents=True,exist_ok=True)
        jobs=[]
        for start in range(prefix,size,64*1024*1024):
            end=min(size-1,start+64*1024*1024-1);path=directory/f'{start}-{end}.part'
            jobs.append((item,start,end,path))
        layouts.append((item,target,partial,size,jobs))
        print(json.dumps({'file':item['path'],'prefix_gb':round(prefix/1e9,2),'remaining_gb':round((size-prefix)/1e9,2),'segments':len(jobs)}),flush=True)
    # Round robin files so a slow origin does not occupy the whole worker pool.
    job_list=[]
    for index in range(max((len(layout[4]) for layout in layouts),default=0)):
        for layout in layouts:
            if index<len(layout[4]):job_list.append(layout[4][index])
    failures=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(segment,*job):job for job in job_list}
        for index,future in enumerate(as_completed(futures),1):
            try:future.result()
            except Exception as exc:failures.append((futures[future],str(exc)));print('Segment failure: '+str(exc),flush=True)
            if index%20==0:print(json.dumps({'segments_finished':index,'total':len(job_list),'failed':len(failures)}),flush=True)
    for item,target,partial,size,jobs in layouts:
        related=[f for f in failures if f[0][0]['path']==item['path']]
        record=dict(item)
        if related:
            record.update(status='failed',error='Segment failures retained for resume')
        else:
            with partial.open('ab') as stream:
                for _,_,_,path in jobs:
                    with path.open('rb') as source:shutil.copyfileobj(source,stream,4*1024*1024)
            value=sha256(partial)
            if partial.stat().st_size!=size or (item.get('expected_sha256') and value!=item['expected_sha256']):
                record.update(status='failed',error='Final size/checksum mismatch')
            else:
                partial.replace(target)
                record.update(status='complete',bytes=size,sha256=value,local_path=str(target.relative_to(root)),checked_at=now(),transfer_method='validated_parallel_ranges')
                # Only remove our own completed regenerable chunk files.
                for _,_,_,path in jobs:path.unlink()
        with (root/'download-events.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(record)+'\n')
        print(json.dumps({k:record.get(k) for k in ['dataset','path','status','bytes','error']}),flush=True)
    for item in other:
        record=transfer(item,root)
        with (root/'download-events.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(record)+'\n')
        print(json.dumps({k:record.get(k) for k in ['dataset','path','status','error']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT_ROOT/'datasets');p.add_argument('--workers',type=int,default=16);a=p.parse_args();main(a.root,a.workers)
