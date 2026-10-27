# Pause and resume the four-candidate evaluation

Scope: GPT-OSS 20B legal; Nemotron 3.5 Parse, olmOCR 2 and PaddleOCR-VL-1.6 document parsing. No additional Qwen or local Nemotron campaign is scheduled. These controls add operational checkpoints; frozen prompts, manifests and scorers are unchanged.

## Operator commands (run on the desktop)

Choose one shared LOCAL control directory, e.g. `C:/dev/ocr-lab/round3-control`. Every worker and the desktop queue must use this same directory. Keep control state and model answers out of Git.

Request pause from a second terminal:

```powershell
python benchmarks/harness/tools/campaign_control.py --control-dir C:/dev/ocr-lab/round3-control pause
```

This prevents further case dispatch. The current case (including its token-count probe, if applicable) finishes and is checkpointed. Parser default concurrency is one, so normally one case drains; with a larger explicit worker count, up to that many already active cases drain. A pause is not instantaneous: a hung service can take its configured request timeout to return. Do not terminate the worker to obtain a clean pause.

Check the pause request:

```powershell
python benchmarks/harness/tools/campaign_control.py --control-dir C:/dev/ocr-lab/round3-control status
```

The command shows the flag, NOT proof that all requests have drained. Wait for the runner to print `status: paused` (or finish), then inspect its checkpoint. Parser run status is in the local SQLite `runs` table. Legal status is in `STATUS.LOCAL_ONLY.json` beside its journal. The desktop queue must stop launching new servers/jobs while the flag exists; these runners do not own a global desktop scheduler.

## Freeing the GPU is a separate action

Pausing client requests leaves a loaded server's weights in VRAM. After all requests drain, the desktop operator must gracefully stop ONLY the evaluation-owned server or unload ONLY its evaluation model, recording its exact restart configuration. No broad process-name kill is provided. The controls never kill processes, contact another session, stop its server or bypass a permission rejection. The existing port-8001 server has not been stopped by Codex; desktop GPU release remains external to these changes.

Do not begin other GPU work until actual VRAM availability is checked. Reload the same exact model/runtime settings before resuming. GPU residency alone is not sufficient to verify matching checkpoint revision or quantization.

## Resume without repeating completed attempts

Clear the flag after the other work ends:

```powershell
python benchmarks/harness/tools/campaign_control.py --control-dir C:/dev/ocr-lab/round3-control resume
```

This does not restart a process or launch a model. Restart the model service with the recorded configuration, then relaunch the original runner command:

- Parser: same backend, URL, tasks, root and settings, plus `--control-dir C:/dev/ocr-lab/round3-control`. It skips every case already recorded under that exact run ID, including failures. Limited smoke tests are labelled `partial`, never complete. Freeze the adapter after smoke tests and before the scored run.
- Legal: same original command, output directory, pack, model and settings, plus `--control-dir C:/dev/ocr-lab/round3-control --resume`. It checks the stored plan and deployment snapshot and refuses changes. All recorded attempts, including failures, are skipped. The raw journal is flushed and fsynced before a request is treated as checkpointed.

Use `--control-dir` on NEW runs too; legal output directories must be new unless `--resume` is explicit. Use local output directories outside the repository. Do not modify prompts, context or budgets mid-run and call it a resume.

## Interruptions and ambiguous requests

Each dispatched case has a local in-flight marker. A clean completion removes it only after the result is committed. A forced termination can leave a marker, partial journal or run lease; automatic resume then refuses. Audit the service and local files before resolving the uncertain attempt. Never silently delete an uncertain attempt and retry for a better score. A stale lease must only be removed after verifying the previous worker has exited. Concurrent workers against the same legal output or parser root are refused.

These controls must be installed BEFORE starting the new scored run. Existing runs from an older adapter hash do not automatically become the same resumable run; migration requires an explicit provenance review. Do not rerun already completed work to fit this controller.

## Validation

Provider-free tests cover pause before dispatch, a pause after the first request, preservation of failed attempts, changed-plan and duplicate refusal, and a parser pause/resume integration with no repeated case. They do not prove live desktop server shutdown, VRAM release or service restart. Claude must smoke-test those ownership-specific operations on the desktop.
