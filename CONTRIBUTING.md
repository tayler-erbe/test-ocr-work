# Contributing

Keep changes focused on one concern: extraction components, benchmark implementation, evaluation evidence or presentation. Include the affected test/contract check and explain any changed behavior.

Do not change prompts, case selection, scoring or thresholds under an existing experiment identity. Add a versioned configuration instead. Retain failures in denominators, distinguish diagnostic and confirmatory work, and report evidence validity separately from semantic correctness.

Run `python tools/check_project.py`. Run `python tools/check_project.py --data` before inference or export merges. Keep all runtime databases, credentials, raw new responses and private material outside the repository.
