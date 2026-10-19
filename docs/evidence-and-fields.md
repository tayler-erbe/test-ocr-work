# Evidence and field contracts

**Status: proposed.** The current script returns question-level quotation lists in a CSV. These contracts define the richer target records for implementation.

## The three checks

1. **Copy validity:** the evidence reference resolves, and the application materializes the exact referenced source text/cell. A fuzzy suggestion is not a valid copied quote.
2. **Source-read validity:** the parse faithfully represents the original native text, page image or cell. OCR agreement with itself does not establish fidelity to the image.
3. **Support validity:** the evidence supports this field's value, scope, conditions and effective version. Real but irrelevant text does not pass.

Keep all three outcomes in storage. Their success rates mean different things and must be evaluated separately. [Research rationale](research/conclusions.md), [verified source defects](research/repository-code-review.md).

## Evidence identity

Each reference resolves to a source version and parser artifact revision. PDF spans carry physical page, block ID, original character range and bounding box when available. DOCX spans carry section/paragraph identity, plus a rendered-page mapping if created. Spreadsheet evidence carries sheet/cell/range identity, original string, formula and cached value where applicable. Image evidence carries physical page/crop coordinates and OCR/vision revision.

Use half-open text ranges `[start, end)`, and validate `0 <= start < end <= source_length`. Store coordinates with an explicit coordinate system and page dimensions. No validator should guess whether coordinates are pixels, PDF points or normalized units.

Materialized quotations are copied by code and stored alongside their reference and digest. Preserve raw punctuation/spacing; normalized comparison is a separate utility with a reversible mapping to source positions. Generated figure descriptions are `interpretation`, not `quotation`.

## Candidate and accepted field

| Attribute | Required meaning |
|---|---|
| source_id / source_version | Immutable document identity and version |
| field_id / schema_version | Field definition and version, never just a question string |
| candidate_value | Model/rule output before acceptance |
| normalized_value | Typed representation, retaining original evidence |
| units / currency / period | Scope needed to interpret numeric/time values |
| evidence_refs | Source span/cell/region references; empty when genuinely absent |
| conditions / exceptions | Applicable qualifiers, exclusions and dependencies |
| extraction_method | Native rule, specialist/text LLM, image LLM, or reviewer |
| parser / model / prompt / runtime / quantization | Exact known revisions; unknowns explicit |
| completeness | Whether required pages/sections were read and searched |
| copy/read/support validation | Separate outcomes with reason and checker revision |
| confidence | Calibrated score if available, or explicitly uncalibrated |
| review_state / reviewer decision | Pending/accepted/rejected/corrected and audit metadata |
| run_id / timestamps | Reproducible processing lineage |

The first implementation can use JSON records with these semantics before Oracle integration. Do not equate a new storage file with the complete schema contract.

## Field outcome semantics

| Outcome | Interpretation | Evidence/review requirement |
|---|---|---|
| present | A supported candidate value was extracted | Valid source references and required validators |
| absent | Source was sufficiently read/searched and the field is not present | Completeness recorded; no invented quote |
| ambiguous | Multiple valid interpretations or conflicting values | Retain competing evidence; review/clarify |
| unread | Relevant source could not be read | Never reclassify as absent |
| not_retrieved | Current context omitted potentially relevant material | Coverage fallback, then re-evaluate |
| failed | Parsing/model/schema/persistence operation failed | Structured error, retry eligibility, no certified value |

Review states are separate: `pending`, `accepted`, `rejected`, `corrected`. A model's `present` candidate is not automatically accepted. A rejected or corrected candidate remains in the audit trail.

## Acceptance rules

- Reject invalid source IDs, out-of-bounds spans, invalid page/cell references and model-created evidence text that differs from the resolved source.
- Require field-specific type/normalization checks. Normalize money with Decimal, preserving currency and scope. Convert dates only when source format and locale are supported; retain ambiguity instead of guessing.
- Do not select a scalar from multiple inconsistent amounts or periods without retaining scope and a resolution reason.
- Check negations, exceptions, notice/cure conditions, incorporated exhibits and supersession. A sentence that mentions termination does not establish termination for convenience.
- Source/image quality checks are stricter for consequential amounts, dates, restrictions and legal conditions; define them with stakeholders and evaluate their review burden.
- Validate found/value/evidence consistency. Truncated or malformed model output is failed extraction, not absence.
- Verify completeness before absence and before any claim of “all” clauses/rows. No top-K retriever can certify document coverage on its own.

## Project A field catalog

These 12 families preserve the relevant purpose of the current queries. Proposed subfields are typed; broad verbatim answers remain available for analyst inspection.

| Family | Proposed subfields | Required qualifiers |
|---|---|---|
| billing | Payment mechanism, fee/price, currency, invoice cadence, due dates | Amount scope, milestone/year, taxes, exceptions |
| termination | Convenience/cause/other grounds, notice, cure, penalties, survival | Who may terminate, triggering conditions, exceptions |
| effective_date | Explicit date or event-triggered commencement | Signature conditions, precedence, ambiguity |
| renewal | Automatic/manual renewal, term, notice window, renegotiation | Opt-out rules and responsible party |
| contract_type | Source title/type | Explicit source wording versus classifier inference |
| deliverables | Scope, deliverables, service/product items | Acceptance criteria and responsible party |
| equipment | Item rows, quantity, model/serial, description | Full table coordinates/headers, totals/units |
| parties | Legal names, roles, addresses and contacts | Parties versus contact persons/pass-through entities |
| delivery_performance | Delivery/milestone dates, SLA metrics, remedies | Relative deadlines, dependencies and units |
| liability_insurance | Indemnity, liability cap, coverage/limits, exclusions | Currency, beneficiary, cap base, carve-outs |
| intellectual_property | Ownership, licenses, data/use rights | Preexisting/background IP, permissions/restrictions |
| confidentiality | Protected scope, term, disclosure rules, exceptions | Survival and required/permitted disclosures |

A document may have several values per family. Do not reduce an entire termination or budget table to one string merely to satisfy a compact schema.

## Project B award catalog

First implementation scope: award and award-modification facts. Fields are drawn from the project brief; final typed schema IDs and controlled vocabularies require domain-owner review.

| Group | Fields to cover | Evidence/normalization rules |
|---|---|---|
| Sponsor and program | Sponsor, pass-through sponsor, agency division, program, opportunity number, program officer | Separate legal entities and people; retain exact identifiers |
| Funding | Total obligated, ceiling, increments, requested/awarded amounts where stated | Currency, increment versus cumulative total, source version, fiscal/budget year |
| Indirect cost | F&A rate, base, exclusions | Rate/base pairing; do not infer base from rate alone |
| Cost sharing | Required amount/percentage, source, conditions | Distinguish mandatory/voluntary and cash/in-kind |
| Performance periods | Period of performance, budget periods, option periods | Start/end, option exercise conditions, amendment precedence |
| Closeout | Deadline and relative rule | Anchor event, required documents, extension rules |
| Payment and billing | Mechanism, cadence, invoice deadlines, payment terms | Responsible entity, triggers, exceptions |
| Reporting | Report types, due dates, cadence, recipients | Relative dates, final versus periodic, mandatory/conditional |
| Deliverables | Deliverables and milestones | Acceptance, responsible party, deadline and dependencies |
| Prior approvals | Activities requiring permission, approver, process | Threshold, timing, exclusions |
| Carryforward | Allowed/prohibited/approval-required, amount/period restrictions | Explicit authority and exceptions |
| Spending restrictions | Restricted costs, caps, conditions | Applicable funding period and affected category |
| Program income | Treatment and reporting requirements | Additive/deductive/matching treatment only when supported |
| IP and data | IP ownership/license, data rights, management requirements | Background versus generated material and release restrictions |
| Publication | Review, acknowledgment, permission, embargo | Timing and exceptions |
| Export/CUI | Export-control/CUI clauses and handling obligations | Clause identity and stated scope; no inferred legal determination |
| Foreign entities | Restrictions, disclosure and participation rules | Applicable entities/activity and exceptions |
| Termination | Grounds, notice, settlement, survival | Conditions and responsible authority |
| Renewal/continuation | Continuation language, optional funding, renewal conditions | Distinguish commitment from possibility |
| Modification difference | Changed values/clauses, effective date, superseded terms | Explicit version pair, original/new evidence, change category |

All arithmetic and aggregate comparisons use approved SQL/Python operations. Differences must identify whether a number is a new total or an increment. Never sum cumulative totals across amendments.

## Project B proposal catalog

Second implementation scope: proposal narratives and requested budgets. Separate descriptive interpretation from original quotations and identifying facts.

| Group | Fields to cover | Constraints |
|---|---|---|
| Research content | Aims, themes, methods, technologies, populations, maturity | Mark summaries/classifications as interpretation; link supporting spans |
| Resources | Facilities and equipment | Distinguish available, requested and planned resources |
| People and collaboration | Investigators/roles, collaborators and institutions | Disambiguation and source-role evidence |
| Sponsorship | Sponsor, program and opportunity identifiers | Requested target versus award sponsor |
| Budget | Requested amount by year/category | Read sheets/cells, units and formulas; compute in code |

Proposal-to-award linkage should prefer authoritative Kuali IDs. An inferred link records method, confidence, competing matches and review state; it must not silently become authoritative identity.

## Assistant contract

The intent result contains approved intent ID, validated parameters, requested scope and confidence/reason for clarification. Application code maps the ID to a predefined query. Result rows receive stable result IDs and underlying field-version IDs.

An answer contains individual claims with source/result references. Original quotations and computed results are rendered differently. Every numeric assertion must correspond to an accepted field or approved query calculation; the model cannot invent arithmetic. Invalid references, unsupported claims or missing parameters prevent unqualified publication.

## Versioning

Version field definitions, source artifacts, parser outputs, normalizers, prompts, models and validation rules independently. A parser change can alter offsets; old references continue resolving to the old artifact. Moving to a new schema must include migration/comparison rules and must not silently alter past accepted records.

See [architecture](architecture.md) for storage and job boundaries and [evaluation](evaluation.md) for measuring these contracts.
