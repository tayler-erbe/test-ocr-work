# Validated laptop export, completed 20 October 2026

Explicitly authorized public-benchmark row-level transfer for the desktop merge. This dedicated branch is the exception to the general aggregate-only exports rule; no private institutional inputs, labels or model outputs are included.

- `laptop.jsonl`: 18,244 rows, 20,090,340 bytes, including 3,816 derived vote rows.
- SHA-256: `ebc69a5340a896a61230570e013176fdf68e8a5e9eaf233c542c18982f5da753`.
- `laptop.conformance.txt`: fresh successful data + export + round-2 check, ending CONFORMANT.
- `laptop.run-manifest.json`: source commit, immutable case hashes, per-run settings, weights, runtime, counts, source checksums and public-only provenance audit.
- `laptop.sha256.txt`: machine-readable checksum. Local attributes preserve bytes across operating systems.

All rows were checked against the frozen public v1/confirm/v2 manifests by case ID, task and cases_sha256. The campaign used only the public case pack in its separate local database. The export is unchanged; failures and truncations were retained, not dropped or retried to replace scores. Only the rows explicitly authorized for this transfer are included.

On desktop, verify with plain code (no model needs to read predictions):

```powershell
Get-FileHash exports/laptop.jsonl -Algorithm SHA256
python -X utf8 -c "from pathlib import Path; print(sum(1 for _ in Path('exports/laptop.jsonl').open(encoding='utf8')))"
python -X utf8 tools/check_conformance.py --root C:/dev/ocr-lab --results exports/laptop.jsonl --round2
```

Then use the repository's `tools/merge_results.py --round2` with desktop and laptop exports. Read the original handoff and round-2 addendum; never run the desktop selection script to reselect variants.

Qwen2.5-VL 7B has the expected matching desktop digest. Qwen3-VL 8B instruct has digest `70e58e37beb15464e19aa903dedb2cba828b89c0fb186f75ff2738c7347b96eb`, which differs from the handoff's recorded desktop digest: method comparison, not a same-weights reproduction. 7B/8B results are not reproduction tests of the desktop's 32B model.

This branch starts at the pinned evaluated handoff commit `5bd04e42b9e6952f34a9a06e7aea3a3514adb945`. It is a transport branch; do not merge it wholesale over newer development without reviewing the branch history. Fetch only its export files if preferred.
