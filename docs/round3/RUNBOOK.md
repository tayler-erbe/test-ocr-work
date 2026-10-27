# Round 3 runbook: pause, resume, status

All commands run from `C:/dev/test-ocr-work/benchmarks/harness`. In a Claude Code prompt, prefix with `!`.

| Want | Command |
|---|---|
| Free the GPU now (stops after the request in flight, keeps everything done so far) | `python -X utf8 tools/round3_driver.py pause` |
| Continue where it stopped | `python -X utf8 tools/round3_driver.py resume` |
| See what is done, what is running, seconds per case | `python -X utf8 tools/round3_driver.py status` |

What a pause does: the parser server on port 8001 is stopped, or the Ollama model is unloaded, within one request. Nothing is lost: parser rows are stored per case in the lab database, legal rows per request in the run's event file, and resume skips what is finished.

Stage order: Nemotron 3.5 Parse, PaddleOCR-VL-1.6, olmOCR-2 on the page tasks; gpt-oss-20b legal arms (24 cases x 8); gpt-oss-20b 60-document reasoning contrast; parser report to `results/vision/round3/parsers.json`; restore of the original port-8001 Qwen3-VL 32B server.

A smoke pass (`run --smoke`) does 3 cases per parser task so speed can be measured before the full run; the full run then reuses those rows.
