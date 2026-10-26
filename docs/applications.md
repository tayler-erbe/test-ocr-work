# Intended applications

## The problem

Structured systems often retain unstructured attachments. Reporting and search can remain dependent on manually opening packets containing mixed PDF pages, scans, tables, charts and spreadsheet exports. This is the problem addressed by the prototype; this evaluation did not measure its industry prevalence or financial impact.

## Candidate workflows

| Document family | Candidate information | Useful interface |
|---|---|---|
| Research proposals and awards | Sponsor, project identifier, investigator, dates, award amounts, budget categories, milestones and reporting duties | Search/filter by project; compare proposed fields against source pages |
| Procurement proposals | Supplier, solicitation identifier, line items, amounts, delivery dates and supporting documents | Proposal comparison with traceable evidence and reviewer corrections |
| Contracts and amendments | Parties, term, payment, renewal, governing law and exceptions | Clause search and reviewed structured exports |
| Invoices and purchase orders | Identifiers, line items, totals, dates and matching references | Reconciliation with numeric checks |
| Financial and technical reports | Tables, charts, narrative findings and source references | Searchable records and evidence-linked summaries |
| Administrative forms and archival scans | Defined fields, page text and document types | Triage, indexing and assisted review |

These are applications to validate, not individually proven deployments. Public OCR/chart/table scores do not establish award-field accuracy or procurement automation readiness.

## Proposed user journey

Connect an approved folder/export/API; classify and segment each packet; parse native text/spreadsheets where available; OCR remaining images; propose defined fields; show exact page evidence; flag uncertainty and unread pages; retain reviewer corrections; export approved records. Keep any action affecting business records behind the appropriate review gate.

## Local processing and cost

Organization-controlled processing can avoid sending document content to an external inference service. Secure operation still requires verified access controls, encryption, network egress restrictions, audit logs and retention policies. See [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf).

The measured small-model campaign ran on a workstation laptop with about 12 GB GPU memory and 64 GB RAM. This supports feasibility for the tested review-assisted workloads, not a production capacity guarantee. A hardware purchase-price claim needs a dated comparable listing or acquisition record. Include engineering, human review, operations and energy when estimating total cost.
