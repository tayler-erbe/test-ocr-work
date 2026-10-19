"""Separate provider-free policy checks, library health, and model promotion."""
import argparse
import json
from pathlib import Path
from document_lab import DEFAULT_ROOT, connect, summary

def check_policy(path):
    policy = json.loads(path.read_text())
    model = policy["model_promotion"]
    assert model["min_documents"] >= 30 and model["min_cases"] >= 100
    assert 0 <= model["max_failure_rate"] < 1
    assert 0 < model["min_accuracy"] <= 1 and 0 < model["min_evidence_f1"] <= 1
    requirements = policy["release_requirements"]
    assert requirements["unknown_evidence_ids_allowed"] == 0
    assert requirements["silent_page_omissions_allowed"] == 0
    assert requirements["real_documents_in_git_allowed"] == 0
    assert requirements["unscored_tasks_may_pass"] is False
    assert requirements["human_holdout_review_required"] is True
    return policy

def library_health(root):
    db = connect(root)
    checks = {"sqlite_integrity": db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"}
    documents = db.execute("SELECT * FROM documents WHERE dataset='private'").fetchall()
    checks["private_source_hashes_present"] = all(len(d["sha256"]) == 64 for d in documents)
    for document in documents:
        rows = db.execute("SELECT page,status FROM pages WHERE doc_id=?", (document["id"],)).fetchall()
        checks["page_coverage:" + document["id"][:24]] = {r["page"] for r in rows} == set(range(1, document["pages"] + 1)) and all(r["status"] == "read" for r in rows)
    db.close()
    return {"status": "passed" if documents and all(checks.values()) else "failed", "checks": checks, "note": "Read coverage does not prove OCR fidelity or factual correctness"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--policy-only", action="store_true")
    parser.add_argument("--engineering-only", action="store_true")
    args = parser.parse_args()
    check_policy(Path(__file__).with_name("quality_gates.json"))
    if args.policy_only:
        print("Quality policy invariants passed")
    else:
        health = library_health(args.root)
        report = {"engineering": health, "model_promotion": "blocked_pending_human_holdout_and_task_specific_validation", "automatic_promotion": False}
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if args.engineering_only and health["status"] == "passed" else 2)
