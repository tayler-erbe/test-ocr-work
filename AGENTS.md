# Working rules

Work in tayler-erbe/test-ocr-work. Keep the project general-purpose and public-data-only. Do not introduce client identities, stakeholder names, infrastructure endpoints, private inputs, private responses or private-derived results.

Keep application components in src/, tests in tests/, recorded benchmark machinery in benchmarks/harness/, public results in results/, and the portfolio in site/. Avoid dated status documents, duplicate reports and loose root scripts.

Preserve the frozen legal evaluator bytes and vision contract behavior. New experiment settings require new labels and output directories. Never overwrite a frozen selection or run the selection script run_round2.py. Never send reference labels to inference. Do not use a model as the accuracy grader.

Run python tools/check_project.py before pushing. Use --data before inference/merging. Model outputs stay local unless explicitly approved public-benchmark exports. Never publish private-derived aggregates. Production readiness, security and savings require evidence beyond benchmark scores.

The portfolio belongs on the existing personal website. Do not create a separate public hosting destination or change repository visibility without a new explicit request. Read docs/roadmap.md for outstanding work.
