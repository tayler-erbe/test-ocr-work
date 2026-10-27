# Scalable intake pipeline: implementation handoff

Model selection on public proxies is closed as of 27 October 2026. The next phase rebuilds the prototype using the routes in [the final evaluation](EVALUATION.md). No new model bake-off or laptop feasibility sweep is scheduled.

Read-only connector → MIME detection and packet/page inventory → immutable source store → native text or selected OCR/table/chart route → canonical page/region spans → retrieval → evidence-ID proposals → deterministic validation → reviewer decisions → approved export/search.

This is the implementation target, not a claim that the prototype already provides it. Keep sources, machine proposals and human decisions separate.

| Milestone | Deliverable | Completion gate |
|---|---|---|
| 1. Define intake/output | Source API/export/folder, permissions, types, volume, fields and consumer | Owners approve exact connection and data contract |
| 2. Restartable ingestion | Source IDs/versions/hashes, MIME checks, deduplication, quarantine, page accounting, queues/checkpoints | Idempotent ingestion; no unread page disappears; pause/restart/recovery demonstrated |
| 3. Task routing | Paddle table route; Parse page candidate; existing layout/charts; Qwen3 or GPT-OSS legal candidate | Artifacts/configurations recorded; regression suite retained; critical numbers not silently accepted |
| 4. Review workflow | Search/filter, source regions, accept/correct/reject, absent/unreadable/uncertain states, audit/export | Analyst can trace each value and export approved records under source permissions |
| 5. Domain validation | Representative labels, document-disjoint holdout, independent double-labelled subset and adjudication | Per-field accuracy, false positives, numeric binding, page failures and review time measured |
| 6. Adaptation | Error-specific prompts/retrieval; fine-tune only if labels justify it | Locked holdout improves without unacceptable regressions; benefit not assumed |
| 7. Review-assisted release | Access, retention, encryption, backups, bounded retries and restore procedures | Domain and IT owners approve acceptance criteria and operating ownership |

Each job records source ID, version/content hash, stage, configuration, attempt, state, timestamps and error. States include queued, running, paused, complete, failed and quarantined. Leases prevent duplicate processing; commits are atomic. Retry limits and reasons are fixed; no silent replacement of failed observations. Preserve model proposals and reviewer corrections separately.

Financial validation must bind numbers to fields, rows/headers, signs, decimals, currencies, scales and units. Token presence alone is insufficient. Measure false positives and omissions. Provenance proves text was copied, not that it answers the question.

Dates follow source access, schema agreement and reviewer availability. A ten-document integration check is not an acceptance set. Sample size follows field prevalence, critical error tolerance and document clustering. Public guidance excludes private labels, examples and pilot-derived statistics.
