"""Add source replacements and a numerical-reasoning corpus without hiding failures."""
import argparse
import json
from pathlib import Path
import urllib.parse
from acquire_datasets import read_url, transfer
from document_lab import DEFAULT_ROOT

def main(root):
    data = root / "datasets"
    plan_path = data / "download-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    items = []
    repo = "czyssrs/FinQA"
    revision = json.loads(read_url(f"https://api.github.com/repos/{repo}/commits/main")[0])["sha"]
    tree = json.loads(read_url(f"https://api.github.com/repos/{repo}/git/trees/{revision}?recursive=1")[0])["tree"]
    for entry in tree:
        path = entry["path"]
        if entry["type"] == "blob" and ((path.startswith("dataset/") and path.endswith(".json")) or path in ["README.md", "LICENSE"]):
            items.append(dict(dataset="finqa", path=path, size=entry["size"], url=f"https://raw.githubusercontent.com/{repo}/{revision}/" + urllib.parse.quote(path)))
    known = {(f["dataset"], f["path"]) for f in plan["files"]}
    plan["files"] += [i for i in items if (i["dataset"], i["path"]) not in known]
    if "finqa" not in [d["id"] for d in plan["datasets"]]:
        plan["datasets"].append(dict(id="finqa", source="https://github.com/czyssrs/FinQA", revision=revision, coverage="all dataset JSON files plus publisher notices", usage="Keep dataset/code license distinctions; retained README. Numerical-reasoning tasks require a separate adapter; no fabricated model score."))
    temporary = plan_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(plan, indent=2), encoding="utf-8"); temporary.replace(plan_path)
    for item in items:
        record = transfer(item, data)
        with (data / "download-events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
        print(json.dumps({k:record.get(k) for k in ["dataset", "path", "status", "bytes", "error"]}), flush=True)

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    main(p.parse_args().root)
