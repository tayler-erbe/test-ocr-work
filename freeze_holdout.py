"""Freeze unexposed public test documents after exploratory protocol work.

Does not create human annotations or establish independence from model training.
"""
import json
from pathlib import Path
from document_lab import DEFAULT_ROOT, connect, digest, now

def freeze(root):
    db = connect(root)
    seen = {r[0] for r in db.execute("SELECT DISTINCT c.doc_id FROM cases c JOIN results r ON c.id=r.case_id")}
    selected, counts = [], {}
    for dataset in ["cuad", "contractnli"]:
        docs = [r[0] for r in db.execute("SELECT DISTINCT doc_id FROM cases WHERE dataset=? AND split='test'", (dataset,)) if r[0] not in seen]
        docs.sort(key=lambda value: digest("public-holdout-v1:" + value))
        docs = docs[:40]
        if len(docs) < 30:
            raise ValueError(f"Only {len(docs)} unexposed test documents remain for {dataset}")
        groups = []
        for doc_id in docs:
            rows = list(db.execute("SELECT id,gold FROM cases WHERE doc_id=? AND split='test'", (doc_id,)))
            rows.sort(key=lambda row: digest("question-v1:" + row["id"])); groups.append(rows)
        cases, strata = [], {}
        for group in groups:
            for row in group:
                gold = json.loads(row["gold"])
                label = gold.get("label", "present" if gold.get("answers") else "absent")
                strata.setdefault(label, []).append(row["id"])
        # Guarantee representation of each source document, then fill balanced
        # label strata. Labels stratify selection; they never enter model prompts.
        for i, group in enumerate(groups):
            labels = sorted(strata)
            preferred = labels[i % len(labels)]
            row = next((r for r in group if r["id"] in strata[preferred]), group[0])
            cases.append(row["id"])
        while len(cases) < 100:
            available = {label: [i for i in ids if i not in cases] for label, ids in strata.items()}
            available = {k:v for k,v in available.items() if v}
            if not available:
                break
            label = min(available, key=lambda k: (sum(i in strata[k] for i in cases), k))
            cases.append(available[label][0])
        selected += cases
        counts[dataset] = {"cases": len(cases), "documents": len(docs), "strata": {label: sum(i in ids for i in cases) for label,ids in strata.items()}}
    dest = root / "evaluation/frozen_public_holdout.json"
    dest.parent.mkdir(exist_ok=True)
    if dest.exists():
        raise ValueError("Holdout already frozen; do not silently replace it")
    protocol = Path(__file__).with_name("document_lab.py")
    result = {"created_at": now(), "source_code_sha256": digest(protocol.read_bytes()), "counts": counts, "case_ids": selected, "excluded_exposed_documents": len(seen), "role": "fresh public holdout after protocol freeze; private human holdout still required"}
    dest.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"path": str(dest), "counts": counts, "excluded_exposed_documents": len(seen)}))
    db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    freeze(parser.parse_args().root)
