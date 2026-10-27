# Evaluation methods

Model configuration is the comparison unit: artifact, quantization, runtime, hardware, prompt, context, output budget, reasoning setting and decoding interface. A model name alone is insufficient.

The public vision case pack is fingerprinted and checked against original and round-2 contracts. Preserve frozen prompts, case manifests, scoring and statistical procedures. The harness remains together under benchmarks/harness/ so relocation does not change its relative imports or recorded behavior.

Metrics are task-specific: character error for crop OCR; TEDS for table structure; relaxed reference accuracy for chart questions; value recall for chart-to-table; word F1 for page text. Report numeric fidelity and failures alongside text/structure metrics. Do not average these metrics into a universal score.

Question-level rows can share a source chart or document. Confirmation uses the recorded split; the 1,322 chart questions cover 722 charts. Do not present row count as independent sample size. “Fresh” means unused in earlier recorded runs, not absent from model training.

Keep exploratory methods distinct from preselected confirmation. Vote3 was selected for round-2 chart confirmation. Self-check remains supporting evidence and behaves differently by model/task. Broad layout masking remains experimental because it loses numbers.

Evidence validation checks exact source slices, identifiers and offsets. It does not establish semantic relevance. For legal extraction, report strict acceptance, partial evidence, label accuracy, false positives, retrieval coverage and truncation separately. New Nemotron configurations are separate from the recorded vision evaluation.

## Completed round 3/3b/3c

Read [the final evaluation](EVALUATION.md) for the current interpretation. H1 passed, H2 did not pass numeric non-inferiority. Imported aggregate statistics were source-hash checked; fresh-set per-case outputs and the new manifest remain on the originating machine, so paired statistics were not independently recomputed here. No fine-tuning or L4/L40S benchmark is claimed. Older audit/session records describe the sequence of experiments; current routing and next steps supersede historical pending-task statements.
