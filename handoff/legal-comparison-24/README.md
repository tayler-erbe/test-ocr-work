# Input-only legal extraction comparison (24 cases)

Authorized public-input handoff in `tayler-erbe/test-ocr-work`. This pack intentionally contains public CUAD/ContractNLI inputs and published reference labels. It contains **no Nemotron responses, reasoning traces, per-case model scores, private documents, database, credentials or endpoint URLs**. It is separate from the vision-v1 handoff and must not enter its export/merge.

## Verify before running

From this directory, using Python 3.12:

```powershell
python -X utf8 verify_pack.py
```

Require `INPUT PACK VERIFIED`. This checks byte hashes, 24 aligned cases, task counts, request hashes, allowed empty responses, and the unchanged frozen scorer checksum. It is a legal-pack integrity check, not the vision conformance gate or a model-quality pass.

## Model-facing inputs

`requests.json` is the **only model-input file**. Each row contains the exact original messages and schema, case ID, task, temperature, budget and requested thinking setting. Both source context and original citation IDs are already inside the messages. Never rebuild retrieval, shorten context, rewrite prompts, reorder source spans, or add reference labels to a request.

`references.DO_NOT_SEND_TO_MODEL.json` contains scoring-only gold and source-span offsets. Keep it out of model calls, RAG indexes, tool attachments and prompt construction. `frozen_evaluation_v3.py` and `document_lab.py` are unchanged scorer code/import support, not model input.

## Matched baseline on desktop

Run local Qwen3-32B and the available Qwen3-VL model through the existing local client. Record exact tag/repository, weight digest/revision, quantization, runtime/version, GPU and observed generation settings. Use one model on the GPU at a time.

For every one of the 24 requests: use the provided messages/schema, temperature 0, output budget 2,000 and requested thinking disabled. For Ollama use native `format` and `think:false`, with the original legal context allocation `num_ctx:32768` where supported; for a local OpenAI-compatible service use strict `response_format.json_schema` and the model's supported thinking control. Record server context limits and any unsupported setting; do not silently substitute a different protocol. An instruct model and a thinking model are different deployments; record the build. Observed reasoning or truncation must be reported even when thinking was requested off.

Keep final answers, finish reasons, token usage, latency and errors locally. Do not retry failures to replace them. Every case remains in the denominator. Use a new labelled configuration for reasoning on, 16,000 output tokens, full-document context or ID-only extraction. This pack includes the exact retrieved excerpts, not complete documents; obtain full documents from the public dataset separately for that experiment.

## Code scoring

Import `frozen_evaluation_v3.py` without calling its CLI or `evaluate()` function. Those functions have historical model/default selection behavior that is not this 24-case comparison.

```python
evidence = scorer.validate_response(prediction, reference['visible'], reference['case']['task'])
metrics = scorer.score(reference['case'], prediction, evidence, reference['visible'])
```

On a truncation, invalid JSON or validation failure: strict correctness false, evidence F1 zero. Preserve the final response locally for diagnostics. Report 12 CUAD and 12 NLI questions separately, failures/truncations, and evidence F1 alongside strict correctness. Supplement with separately labelled presence/absence, per-reference-answer recovery and partial literal-validity diagnostics; never alter the frozen acceptance score.

The revised Nemotron result on this exact subset was 1/12 CUAD and 5/12 NLI, with thinking disabled and 2,000 output tokens. These are aggregate comparators; their saved responses are deliberately excluded. Earlier Qwen2.5 7B scored 7/12 and 6/12, but at 600 output tokens, so that is not a fully matched generation comparison.

All 24 cases were already exposed during diagnostics. This is a paired exploratory comparison, not a new untouched holdout or a model-family verdict. Keep outputs local and publish only aggregates. Fresh institutional validation and document-level uncertainty follow after the setup is chosen.
