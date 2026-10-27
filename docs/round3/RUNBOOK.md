# Round 3 runbook: pause, resume, status

All commands run from `C:/dev/test-ocr-work/benchmarks/harness`. In a the desktop operator Code prompt, prefix with `!`.

| Want | Command |
|---|---|
| Free the GPU now (stops after the request in flight, keeps everything done so far) | `python -X utf8 tools/round3_driver.py pause` |
| Continue where it stopped | `python -X utf8 tools/round3_driver.py resume` |
| See what is done, what is running, seconds per case | `python -X utf8 tools/round3_driver.py status` |

What a pause does: the runners stop dispatching (the shared control directory `C:/dev/ocr-lab/round3-control`, see PAUSE_RESUME.md), active requests drain and are checkpointed, then the driver stops the parser server it started or unloads the Ollama model it loaded. The GPU is free once `status` shows it below about 3 GB. Nothing is lost: parser rows are stored per case in the lab database, legal rows per request in the run's event file, and resume skips what is finished.

Stage order: Nemotron 3.5 Parse, PaddleOCR-VL-1.6, olmOCR-2 on the page tasks; gpt-oss-20b legal arms (24 cases x 8); gpt-oss-20b 60-document reasoning contrast; parser report to `results/vision/round3/parsers.json`; restore of the original port-8001 Qwen3-VL 32B server.

A smoke pass (`run --smoke`) does 3 cases per parser task so speed can be measured before the full run; the full run then reuses those rows.
