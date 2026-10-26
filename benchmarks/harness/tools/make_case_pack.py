"""Copy exactly the data the frozen vision-v1 cases need into a portable folder, with a SHA-256 receipt.

The laptop must never rebuild the case manifests: vision_eval.build() only keeps OmniDocBench pages whose image
file exists locally, so a machine with a different subset of files would freeze a different case set. Instead,
copy this pack and use it as the lab root (--root) on the other machine.

Contents (same relative paths as the desktop lab, so every case path resolves unchanged):
  evaluation/vision_cases_v1.json, vision_confirm_v1.json (+ vision_cases_v2.json if present)
  datasets/omnidocbench/raw/images/<only the pages the cases use>
  datasets/omnidocbench/raw/OmniDocBench.json      (needed only to rebuild; kept for audit)
  datasets/chartqa/raw/ChartQA Dataset.zip         (charts are read straight from the zip)
  RECEIPT.json                                      sha256 of every file; tools/check_conformance.py --data verifies it

  python tools/make_case_pack.py --root C:/dev/ocr-lab --out D:/ocr-vision-pack
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_contract  # noqa: E402

CHARTQA_ZIP = "datasets/chartqa/raw/ChartQA Dataset.zip"
OMNI_JSON = "datasets/omnidocbench/raw/OmniDocBench.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    files = []
    for which, spec in eval_contract.FROZEN.items():
        src = a.root / spec["file"]
        if not src.exists():
            if spec["required"]:
                raise SystemExit(f"{src} missing")
            continue
        m = json.loads(src.read_text(encoding="utf-8"))
        if eval_contract.cases_sha256(m) != spec["cases_sha256"]:
            raise SystemExit(f"{src}: cases_sha256 is not the frozen value; refusing to pack it")
        files.append(spec["file"])
        files += sorted({c["image"] for c in m["cases"] if c["image"].startswith("datasets/")})
    files += [CHARTQA_ZIP, OMNI_JSON]
    files = list(dict.fromkeys(files))
    receipt = {}
    for rel in files:
        src, dst = a.root / rel, a.out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dst)
        receipt[rel] = sha256(dst)
        if receipt[rel] != sha256(src):
            raise SystemExit(f"copy of {rel} does not match its source")
    total = sum((a.out / r).stat().st_size for r in receipt)
    (a.out / "RECEIPT.json").write_text(json.dumps({"protocol": eval_contract.PROTOCOL, "made_from": str(a.root),
                                                    "frozen_case_sets": {k: v["cases_sha256"] for k, v in eval_contract.FROZEN.items()},
                                                    "bytes": total, "files": receipt}, indent=1), encoding="utf-8")
    print(json.dumps({"out": str(a.out), "files": len(receipt), "gigabytes": round(total / 1e9, 2)}))


if __name__ == "__main__":
    main()
