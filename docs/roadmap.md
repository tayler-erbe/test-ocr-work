# Implementation roadmap

**Status: proposed work.** Documentation and source review are complete on this branch; the application remains the inherited prototype. Each phase has explicit acceptance criteria so progress is reviewable.

## Phase 0 — Reproducible project foundation

**Deliver:** correct entry point/runbook, minimal compatible dependency manifest and lock strategy, config validation, provider-free tests, documented source/data retention and artifact exclusions. This documentation change supplies the corrected runbook and exclusions; packaging/tests are code work.

**Acceptance:** a clean isolated environment can import/run synthetic checks without credentials, downloads or real data; required provider options are validated at startup; generated indexes and local secrets do not appear in Git; supported interpreter/runtime is recorded. Retain inherited attribution/history.

## Phase 1 — Fix correctness and failure handling

**Deliver:** exact evidence selection/copying; strict separation of fuzzy suggestions; mixed-page OCR/read completeness; exact-first page attribution during migration; explicit write errors and failed exit status; consistent found/value/evidence semantics; distinct unsupported-feature versus transient errors.

**Acceptance:** the four [review reproductions](research/repository-code-review.md) become passing regression checks. Changed money/negation cannot receive source-copy acceptance. Unread pages cannot become document absence. Persistence failure prevents a successful complete job. An exact citation outranks a fuzzy page. Every output records mode and failure/validation state.

**Dependency:** Phase 0. Avoid changing the production model while fixing acceptance rules so comparisons remain interpretable.

## Phase 2 — Canonical source and field records

**Deliver:** immutable source hashes/versions, parser artifacts, source spans/cells, typed Project A fields, normalization with units/currency/conditions, versioned run lineage, review candidates and decisions. Refactor provider/parsing/validation/storage interfaces out of the monolithic script.

**Acceptance:** every accepted field can be inspected against its original source; raw and normalized values remain distinct; old parser offsets remain resolvable; amount/date normalization and condition semantics pass focused tests. Legacy CSV export can be produced from records, but is not authoritative storage.

**Dependency:** Phase 1. Follow the [evidence contract](evidence-and-fields.md).

## Phase 3 — Institutional evaluation and model bake-offs

**Deliver:** adjudicated train/dev/test sets, stage-isolated evaluation harness, paired quantization/context/grammar tests, retrieval question set, performance pilot and candidate promotion records.

**Acceptance:** per-field/null/evidence metrics and review burden are published with exact revisions; held-out families/templates prevent leakage; finalists pass agreed critical-field gates; a 48-hour soak provides committed outcomes/hour and resource usage. Unsupported guesses remain labeled.

**Dependency:** stable source/evidence interfaces from Phase 2. Use the [evaluation plan](evaluation.md); promote a model only after the comparison.

## Phase 4 — Dependable bulk processing and retrieval

**Deliver:** incremental/idempotent stages, job checkpoints/leases, bounded retries/concurrency, atomic index promotion, lexical+dense retrieval with source associations, configurable resource scheduling and structured observability.

**Acceptance:** interrupted jobs resume without duplicate accepted records or lost prior indexes; concurrent runs do not collide; a failed storage commit cannot advance a stage; resource settings respect measured tenant headroom; exact identifiers and clause recall improve against the baseline.

**Dependency:** Phases 2–3. Confirm actual index storage formats before using capacity estimates.

## Phase 5 — Project B ingestion and award extraction

**Deliver:** approved Kuali/Oracle source adapter; signature-based format routing; DOCX/spreadsheet/image/archive handlers with bounds; audited classification cascade; award schema; Oracle field/run/review persistence; modification relationships and evidence-backed differences.

**Acceptance:** provider policy blocks every B path to external inference, including embeddings and judges; corrupt/unread files quarantine visibly; archive members retain parent identity; budget formulas/caches and sheet coordinates persist; increments versus cumulative totals are distinguished; effective/superseded values are explicitly versioned.

**Dependency:** preceding correctness and job foundations plus infrastructure/retention approval. Do not start all 125K attachments as an uncheckpointed model loop.

## Phase 6 — Analytics and fixed-query assistant

**Deliver:** approved parameterized query registry, authorization/filtering, typed arithmetic, result IDs, intent classifier/parameter validation, claim-level citations, abstention/clarification and analyst review interface.

**Acceptance:** generated arbitrary SQL is never executed; denied records never reach retrieval/model context; incorrect/ambiguous parameters require resolution; numbers match approved calculations; source/result citations support the claims; regression and permission tests pass.

**Dependency:** accepted/versioned award records and a validated retrieval layer. Conversation features do not bypass record acceptance.

## Phase 7 — Proposal intelligence and linkage

**Deliver:** proposed aims/themes/methods/facilities/people/budget schema, descriptive-versus-verbatim status, authoritative proposal-award linkage, reviewed inferred-link candidates, public-data enrichment where allowed.

**Acceptance:** confidential proposal content stays within approved services; interpretations are visibly distinguished from source quotations; budget-year units and relationships are preserved; inferred linkage cannot silently replace authoritative identifiers.

**Dependency:** award/platform foundations and proposal-specific annotated evaluation.

## Decisions required before deployment

| Decision | Responsible role | Needed evidence |
|---|---|---|
| Field accuracy/review tolerances | Contract/research administration domain owner | Adjudicated metrics and failure examples |
| Allowed data/providers/retention | Institutional data owner/security | Explicit policy covering all stages |
| NIM model/profile | Infrastructure owner | GPU inventory, profile minima, service test |
| GPU schedule/concurrency | Shared-server operators | Tenant peaks and sustained pilot |
| Backfill scope/deadline | Project and operations owners | File mix, filtering and complete-path throughput |
| Repository licensing/fixtures | Project/data owner | Original rights, dependencies, source suitability |

## First implementation batch

Start with Phase 0 packaging and the Phase 1 reproduced defects. Keep that change small enough to review independently of parser/model replacement. Then introduce canonical evidence/typed records and run the bake-offs. This sequencing turns the research into measurable improvements instead of an untested full-system swap.
