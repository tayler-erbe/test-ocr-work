# Local Document Intelligence Evaluation

**Which local model should read your PDFs, and what can you trust it to extract?**

An advisory engineering evaluation by **Tayler Erbe**, using public OCR, table, chart and legal benchmarks. Completed 27 October 2026. Guidance for a reviewed workflow under hardware constraints, not a universal ranking or production certification.

## Start here

- [Final advisory: methods, results and recommendations](docs/EVALUATION.md).
- [Hardware and budget guide](docs/hardware-and-budget.md): workstation estimates and single-L4/L40S planning.
- [Interactive findings dashboard](site/index.html): serve with `python -m http.server 8931 --directory site`.
- [Next phase: scalable intake pipeline](docs/roadmap.md).
- [Machine-readable evidence](results/FINAL_EVALUATION.json), with source hashes and original aggregates.

## Practical findings

| Need | Start with | What was established |
|---|---|---|
| Financial-report table crops | PaddleOCR-VL-1.6 single pass | H1 passed: 0.852 TEDS, 97.4% numeric recall, 100 project-unused tables. Amounts still need validation. |
| Whole-page text | Nemotron 3.5 Parse single pass | Word F1 0.899; numeric recall 88.2%. H2 did not pass numeric non-inferiority. |
| Archival prose | olmOCR-2 7B FP8, bare adapter | Strong prose overlap with substantial numeric loss; not the preferred financial route. |
| Charts / layout | Qwen3-VL task routes / DocLayout-YOLO | Preserve model-specific methods; no universal self-check benefit. |
| Clause proposals | Qwen3 32B thinking off; GPT-OSS 20B low as a smaller candidate | Modest strict scores; neither qualifies for unattended legal extraction. |

## Why this matters

ERP migrations and repositories contain mixed packets: narrative, scans, pricing tables, graphs and spreadsheets flattened into PDFs. Applications include research proposals and awards, procurement proposals, contracts, amendments, invoices, purchase orders, financial statements, scientific papers and archives. These are opportunities, not evaluated deployments across every document type.

Local inference can keep inputs within organization-controlled infrastructure. Secure storage, permissions, network controls and operational review are still required. Native spreadsheets should be parsed as data when available.

Results vary with documents, scan quality, language, fields and labels. Fine-tuning may help after representative labelled data exists; no gain was measured or guaranteed here. Fix lost OCR text and retrieval misses before trying to train them away.

## Measured versus planned

Round 3 used an **RTX 5090 32 GB**. Earlier vision work includes a **12 GB laptop**; its 40,975 combined result rows repeat configurations and are not unique documents. Targets are **one L4 24 GB or one L40S 48 GB**. Neither target was benchmarked, and no new sweep is scheduled. Prices are dated planning allowances, not proof of savings or stock.

## Repository map

| Directory | Purpose |
|---|---|
| `src/`, `tests/` | Evidence/retrieval components and software checks |
| `benchmarks/harness/` | Recorded runners, frozen prompts, scorers and contracts |
| `data/public/` | Public benchmark pack, Git LFS assets and receipt |
| `results/` | Final evidence index, original exports and aggregates |
| `docs/` | Advisory, methods, hardware, privacy and roadmap |
| `site/` | Static portfolio case study and result explorer |
| `tools/`, `requirements/` | Checks and dependencies |

Run Python 3.12 checks with `python tools/check_project.py --data` after dependencies and `git lfs pull`. They establish software/contract behavior, not semantic accuracy. [Data boundaries](docs/data-and-privacy.md) and [history resync](docs/RESYNC.md) remain applicable.

Only public benchmark material and fabricated examples belong here. Preserve attribution and model/code/data licenses. Open weights do not make every component open source. AI coding tools supported implementation; local models performed inference and deterministic reference-based code produced task scores.

Website source is prepared for the existing [personal portfolio](https://taylererbe.com/). A repository push does not establish that the live domain has been updated.
