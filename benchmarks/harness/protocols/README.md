# Frozen evaluation protocol

`evaluation_v3.py` is an immutable copy of the evaluator used for the initial 200-question public holdout. Its source SHA-256 is `43f78d7f122a6c1c0df5a484a49569ff20858ad72f0fac784b86615ca1e0d27f`.

The application CLI recognizes matching frozen manifests and dispatches evaluation to this snapshot. Keep this file unchanged. New protocol work belongs in a new version, with a new unexposed holdout or an explicitly labeled reanalysis. The archived code includes functions that were present at freeze time; the current UI/private extraction use the application modules instead.

The retained policy is an evaluation-context snapshot. Published summaries record their active quality-policy version separately; numeric score calculation and policy promotion are distinct.
