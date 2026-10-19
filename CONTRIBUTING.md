# Contributing

Make changes that improve accepted field accuracy, evidence quality, review burden, or dependable throughput. State the concrete problem, expected behavior, and how the change was checked.

## Read before changing the pipeline

- [Research conclusions](docs/research/conclusions.md) explain the current decisions.
- [Evidence contract](docs/evidence-and-fields.md) defines what a supported field must contain.
- [Evaluation plan](docs/evaluation.md) defines the comparisons needed for model changes.
- [Roadmap](docs/roadmap.md) separates implemented behavior from planned work.

## Changes and reviews

Use a branch and a pull request. Keep changes small enough to inspect. For a bug fix, include the triggering case and a focused regression check. For a model/parser change, record the exact checkpoint, runtime, quantization, prompt, schema, dataset revision, and the paired evaluation results. A new model should not be promoted only because its public benchmark increased.

Keep source data, API keys, logs containing document text, generated vector databases, and downloaded weights out of commits. Synthetic test data should be visibly synthetic. Approved real fixtures need a documented owner, access policy, and retention decision before use.

## Documentation requirements

Update the relevant guide when changing behavior. Label material as current, proposed, observed, estimated, or unverified. Link a primary source for model-specific facts. Do not replace a measured result with an estimate, and do not promote a vendor benchmark to institutional extraction accuracy.

The detailed research is a dated reference. Record new decisions and fresh measurements in the working guides rather than silently rewriting historical results. Link superseding evidence and explain changes. Keep tables and configuration examples aligned with actual code.

## Validation

For code changes, run checks appropriate to the changed behavior. Provider-free tests should not require credentials, network access, model downloads, or real contracts. End-to-end tests must identify the approved host/provider and data policy. Preserve failure examples and measure false negatives as well as hallucinated values.

Provider-free tests now cover source quoting, fabricated IDs, numeric alteration, absence consistency, scorer behavior, idempotent storage and download integrity. Run `python -m unittest discover -p "test_*.py" -v` and `python quality_check.py --policy-only`. The CI workflow exercises these on Windows and Linux. Pinned direct demo/workbench dependencies are provided; a full transitive lock and institutional deployment validation remain pending. A passing code check does not promote a model or fix the inherited Azure runner.

## Attribution and licensing

Preserve meaningful original attribution and Git history. Third-party model, toolkit, and dependency licenses are distinct from a repository license. Do not assume a permissive model license covers its serving container or every dependency. Do not claim institutional approval from a license alone.
