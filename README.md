# Document Intelligence Evaluation

**Choosing local models for OCR, tables, charts and evidence-linked extraction under hardware constraints.**

A public-data engineering case study by Tayler Erbe. The project evaluates how model choice, prompting, evidence handling and available GPU memory affect document-processing quality. It provides a reproducible benchmark record and a review-assisted extraction prototype.

## Why this matters

An ERP migration can move records without unlocking the information in their attachments. A single packet may combine narrative text, scans, budget tables, charts and spreadsheets rendered as PDF. Teams need searchable, structured records with evidence they can inspect—not simply plausible generated text.

Potential applications include **research proposals and award documents, procurement proposals, contracts and amendments, invoices, purchase orders, financial reports and technical reports**. These are intended applications, not claims that every document type has been validated. Native spreadsheets should be parsed directly when available.

Local inference is an option where sensitive content must stay within an organization-controlled environment. It does not by itself establish secure operation: permissions, network egress, encryption, retention and operational controls still need verification.

## Measured findings

| Task | Configuration | Recorded result | Interpretation |
|---|---|---|---|
| Prose crop OCR | Qwen3-VL 8B Instruct, laptop baseline | About 1.2% completed character error; 96.5% numeric recall; 50 crops | Useful prototype candidate; below the numeric-recall acceptance target |
| Table transcription | Same configuration | 0.818 TEDS; 60 tables | Structure similarity is not proof of correct amounts |
| Chart questions | Same configuration | 79.5% baseline vs 36.0% self-check; 200 development questions | Methods must be selected per model and task |
| Chart-to-table | Same model, self-check | Value recall 0.418 to 0.930; 60 cases | Exploratory improvement; separate from chart-question accuracy |
| Whole-page text | Desktop 32B, broad masking | Word F1 0.814 to 0.881; numeric recall 87.2% to 69.4%; 80 confirmation pages | Masking remains experimental where numbers matter |

The vision campaign contains **40,975 public result rows across two machines**. Rows repeat cases across configurations; they are not independent documents. Round-2 chart confirmation covers **1,322 questions across 722 charts**. Self-check is a supporting comparison; vote3 was the selected confirmatory method.

The measured laptop used approximately **12 GB GPU memory and 64 GB system RAM**. Desktop results used a 32 GB GPU. No sustained L4/L40S throughput, purchase-cost advantage or production SLA has been established.

**Nemotron is being reassessed.** Earlier results describe tested configurations, not an irredeemable model limitation. The follow-up separates reasoning, output budget, sampling, context coverage and evidence representation. See [the experiment plan](docs/nemotron-reassessment.md).

## Start here

- [Interactive case study](site/index.html): serve it locally with `python -m http.server 8931 --directory site`, then open `http://127.0.0.1:8931/`.
- [Corrected routing report](results/vision/ROUTING_REPORT.md): decisions and limitations.
- [Generated merged results](results/vision/merged/MERGED_REPORT.md): measured configuration tables.
- [Methods](docs/methods.md), [applications](docs/applications.md), [next steps](docs/roadmap.md).

The site source is intended for integration into [taylererbe.com](https://taylererbe.com/). This repository does not claim that deployment has completed.

## Repository map

| Folder | Purpose |
|---|---|
| `src/` | Evidence validation and retrieval components |
| `tests/` | Provider-free tests using fabricated examples |
| `benchmarks/harness/` | Recorded benchmark runners, frozen legal scorer and vision contracts |
| `data/public/` | Public vision case pack and receipt; large assets use Git LFS |
| `results/vision/` | Public exports, merged measurements and routing report |
| `site/` | Static case study and interactive aggregate dashboard |
| `docs/` | Methods, applications, privacy boundaries and roadmap |
| `tools/` | Project checks and documented entry points |
| `requirements/` | Dependencies separated by evaluation use |

The benchmark harness retains its internal layout to preserve recorded behavior. Active evidence components and tests are separated from that experimental snapshot. There are no application scripts loose in the repository root.

## Reproduce the checks

Python 3.12 is the recorded runtime. Install the frozen conformance dependencies, then run:

```powershell
python -m pip install -r requirements/conformance_requirements.txt
python tools/check_project.py
python tools/check_project.py --data
```

The first command checks privacy boundaries, software tests, quality policy and both frozen contracts. `--data` also verifies the public image pack against its receipt; run `git lfs pull` first. These checks do not call a model. They establish software/contract behavior, not extraction accuracy.

## Scope and attribution

Only public benchmark inputs/results and fabricated software-test examples belong in this repository. No private sample documents, their responses, labels, field-level outcomes or derived pilot reports are included in the current tree. Do not commit credentials or infrastructure endpoints. See [data and privacy boundaries](docs/data-and-privacy.md).

AI coding assistants supported implementation and orchestration; local models performed benchmark reading and extraction. Reference labels and deterministic scorers—not another model's opinion—produced the reported task metrics. Preserve publisher attribution and dataset-specific terms; public availability does not imply unrestricted redistribution.
