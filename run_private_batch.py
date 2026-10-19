"""Extract complete private sources and retain explicit blocks for incomplete ones."""
import argparse
import json
from document_lab import DEFAULT_ROOT, connect, digest
from private_extraction import extract as extract_private
from local_demo import FIELDS

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=__import__('pathlib').Path, default=DEFAULT_ROOT)
    parser.add_argument("--model", default="qwen2.5:7b")
    args = parser.parse_args()
    extract_private(args.root, args.model)
    db = connect(args.root)
    for doc in db.execute("SELECT * FROM documents WHERE dataset='private' AND status!='needs_review'").fetchall():
        missing = [r[0] for r in db.execute("SELECT page FROM pages WHERE doc_id=? AND status!='read' ORDER BY page", (doc["id"],))]
        run_id = digest(doc["sha256"] + "blocked-incomplete-v1")[:24]
        metadata = json.dumps({"source_sha256": doc["sha256"], "gold_status": "unlabeled", "context": "No model call: source page coverage unresolved", "blocked_pages": missing})
        for field in FIELDS:
            db.execute("INSERT OR REPLACE INTO findings VALUES (?,?,?,?,?,?,?)", (run_id, doc["id"], "not_called", field, "[]", "blocked_incomplete_source", metadata))
    db.commit(); db.close()
