"""Acquire versioned benchmark sources into a local library, never into Git.

Archives remain intact. Only evaluation subsets need to be expanded.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import threading
import time
import urllib.parse
import urllib.request

HEADERS = {"User-Agent": "Document-Intelligence-Evaluation/1.0 (local research evaluation)"}
LOCK = threading.Lock()

def read_url(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=90) as r:
        return r.read(), dict(r.headers)

def hf_files(repo):
    meta = json.loads(read_url("https://huggingface.co/api/datasets/" + repo)[0])
    revision = meta["sha"]
    url = f"https://huggingface.co/api/datasets/{repo}/tree/{revision}?recursive=true&limit=1000"
    files = []
    while url:
        body, headers = read_url(url)
        files += [f for f in json.loads(body) if f["type"] == "file"]
        link = headers.get("Link", headers.get("link", ""))
        match = re.search(r'<([^>]+)>; rel="next"', link)
        url = match[1] if match else None
    return revision, files

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def safe_target(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("Unsafe destination path")
    return target

def transfer(item, root):
    target = safe_target(root, item["dataset"] + "/raw/" + item["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = item.get("size")
    partial = target.with_name(target.name + ".part")
    record = dict(item)
    for attempt in range(4):
        try:
            if not target.exists():
                offset = partial.stat().st_size if partial.exists() else 0
                headers = dict(HEADERS)
                if offset:
                    headers["Range"] = f"bytes={offset}-"
                with urllib.request.urlopen(urllib.request.Request(item["url"], headers=headers), timeout=120) as response:
                    ranged = response.status == 206
                    if ranged and not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
                        raise ValueError("Invalid resumed Content-Range")
                    mode = "ab" if offset and ranged else "wb"
                    with partial.open(mode) as stream:
                        shutil.copyfileobj(response, stream, length=2 * 1024 * 1024)
                if expected is not None and partial.stat().st_size != expected:
                    raise ValueError(f"Size mismatch: {partial.stat().st_size} != {expected}")
                partial.replace(target)
            if expected is not None and target.stat().st_size != expected:
                raise ValueError("Existing file size mismatch; quarantined for manual inspection")
            digest = sha256(target)
            if item.get("expected_sha256") and digest != item["expected_sha256"]:
                raise ValueError("Publisher SHA-256 mismatch")
            record.update(status="complete", bytes=target.stat().st_size, sha256=digest, local_path=str(target.relative_to(root)))
            break
        except Exception as exc:
            record.update(status="failed", error=str(exc), attempts=attempt + 1)
            if attempt < 3:
                time.sleep(min(2 ** attempt, 8))
    record["checked_at"] = datetime.now(timezone.utc).isoformat()
    return record

def plan(root):
    items, catalog = [], []
    def add(dataset, url, path, **kw):
        items.append(dict(dataset=dataset, url=url, path=path, **kw))
    for key, repo, paths in [
        ("cuad", "The-Atticus-Project/cuad", ["data.zip", "readme.md", "category_descriptions.csv"]),
        ("acord", "The-Atticus-Project/acord", ["ACORD Dataset & ReadMe.zip", "README.md", "LICENSE"]),
    ]:
        meta = json.loads(read_url(f"https://api.github.com/repos/{repo}/commits/main")[0])
        revision = meta["sha"]
        for path in paths:
            add(key, f"https://raw.githubusercontent.com/{repo}/{revision}/" + urllib.parse.quote(path), path)
        catalog.append(dict(id=key, source=f"https://github.com/{repo}", revision=revision, coverage="publisher release archive", usage="See retained publisher README/terms; keep attribution"))
    for key, repo in [("chartqa", "ahmed-masry/ChartQA"), ("chartqapro", "ahmed-masry/ChartQAPro"), ("omnidocbench", "opendatalab/OmniDocBench"), ("pubtables1m", "bsmock/pubtables-1m"), ("fintabnet", "bsmock/FinTabNet.c")]:
        revision, files = hf_files(repo)
        if key == "chartqa":
            files = [f for f in files if f["path"] in ["ChartQA Dataset.zip", "README.md", ".gitattributes"]]
        for f in files:
            add(key, f"https://huggingface.co/datasets/{repo}/resolve/{revision}/" + urllib.parse.quote(f["path"]) + "?download=true", f["path"], size=f["size"], expected_sha256=f.get("lfs", {}).get("oid"))
        catalog.append(dict(id=key, source=f"https://huggingface.co/datasets/{repo}", revision=revision, coverage="full publisher distribution; ChartQA uses complete ZIP rather than duplicate parquet", usage="OmniDocBench: research only/non-commercial. Others: retain and review dataset card; code license is not automatically data license."))
    for name in ["core", "extra"]:
        add("doclaynet", f"https://codait-cos-dax.s3.us.cloud-object-storage.appdomain.cloud/dax-doclaynet/1.0.0/DocLayNet_{name}.zip", f"DocLayNet_{name}.zip")
    add("doclaynet", "https://raw.githubusercontent.com/DS4SD/DocLayNet/main/README.md", "README.md")
    catalog.append(dict(id="doclaynet", source="https://github.com/DS4SD/DocLayNet", revision="1.0.0", coverage="core and extra archives", usage="CDLA-Permissive-1.0 per publisher loader; retain source notices"))
    add("contractnli", "https://stanfordnlp.github.io/contract-nli/resources/contract-nli.zip", "contract-nli.zip")
    add("contractnli", "https://raw.githubusercontent.com/stanfordnlp/contract-nli/gh-pages/index.md", "TERMS-and-README.md")
    add("contractnli", "https://raw.githubusercontent.com/stanfordnlp/contract-nli/gh-pages/LICENSE", "LICENSE")
    catalog.append(dict(id="contractnli", source="https://stanfordnlp.github.io/contract-nli/", revision="publisher release; local hash recorded", coverage="complete release ZIP", usage="CC BY 4.0 and publisher terms retained; no redistribution in application repo"))
    nih_url = "https://beta.nih.gov/niaid/funding/sample-applications"
    body = read_url(nih_url)[0].decode()
    metadata = root / "niaid/metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    (metadata / "source-page.html").write_text(body, encoding="utf-8")
    links = sorted(set(urllib.parse.urljoin(nih_url, u.replace("&amp;", "&")) for u in re.findall(r'href="([^"]+\.pdf(?:\?[^"]*)?)"', body, re.I)))
    for url in links:
        add("niaid", url, Path(urllib.parse.urlparse(url).path).name)
    catalog.append(dict(id="niaid", source=nih_url, coverage="all directly linked PDFs on this sample page, not all NIH websites", usage="Copyrighted applications: unchanged materials for nonprofit educational use only; credit PI, institution and NIAID. Not a general commercial-use corpus. Kept in raw storage; not used for synthetic transformations."))
    return items, catalog

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--plan-only", action="store_true")
    args = p.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    plan_path = args.root / "download-plan.json"
    if plan_path.exists():
        saved = json.loads(plan_path.read_text(encoding="utf-8")); items, catalog = saved["files"], saved["datasets"]
    else:
        items, catalog = plan(args.root)
        plan_path.write_text(json.dumps(dict(datasets=catalog, files=items), indent=2), encoding="utf-8")
    print(json.dumps({"files": len(items), "known_bytes": sum(i.get("size", 0) for i in items), "datasets": [x["id"] for x in catalog]}), flush=True)
    if args.plan_only:
        return
    # Small files first so initial evaluation can start while archives transfer.
    items.sort(key=lambda i: i.get("size", 0))
    journal = args.root / "download-events.jsonl"
    latest = {}
    if journal.exists():
        for line in journal.read_text(encoding="utf-8").splitlines():
            r = json.loads(line); latest[(r["dataset"], r["path"])] = r
    jobs = [i for i in items if latest.get((i["dataset"], i["path"]), {}).get("status") != "complete"]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(transfer, i, args.root): i for i in jobs}
        for future in as_completed(futures):
            try:
                record = future.result()
            except Exception as exc:
                record = dict(futures[future], status="failed", error=str(exc))
            latest[(record["dataset"], record["path"])] = record
            with journal.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record) + "\n")
            if record["status"] == "failed" or len(latest) % 100 == 0 or record.get("bytes", 0) > 100_000_000:
                print(json.dumps({k: record.get(k) for k in ["dataset", "path", "status", "bytes", "error"]}), flush=True)
    (args.root / "download-status.json").write_text(json.dumps(list(latest.values()), indent=2), encoding="utf-8")
    failed = [r for r in latest.values() if r["status"] != "complete"]
    print(json.dumps({"complete": len(latest) - len(failed), "failed": len(failed)}), flush=True)
    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()
