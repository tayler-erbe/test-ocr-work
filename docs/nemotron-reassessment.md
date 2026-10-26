# Nemotron reassessment: experiment plan

Status: completed 26 October 2026. This preserved plan records the protocol fixed before requests. The eight-arm campaign (192 requests) and separate reasoning comparison (120 requests) are complete. See [completed findings](../results/legal/README.md). This supersedes no frozen result and makes no model-rejection claim.

## Question

Can an improved, documented inference configuration and extraction interface materially improve the existing Nemotron endpoint on public legal tasks? Distinguish a weak tested configuration from a model limitation. Do not assume the desired conclusion is either success or failure.

## Design

Use the same 24 previously exposed CUAD/ContractNLI cases (12 each). Preserve exact baseline messages and schema. Run requests sequentially, interleaving configurations by case. Keep every failure and truncated answer in the denominator. Retain final answers locally, but never reasoning text. Record reasoning presence, usage, finish reason, latency, request hash, code hash, source hash and deployment snapshot hash. A snapshot is not a weight checksum.

| Arm | Context | Reasoning | Output budget | Sampling | Comparison |
|---|---|---|---|---|---|
| baseline | Frozen retrieval | Off | 2,000 | temperature 0 / top_p 1 | Repeat earlier configuration |
| budget | Frozen retrieval | Off | 16,000 | 0 / 1 | Output budget only |
| reasoning | Frozen retrieval | On | 16,000 | 0 / 1 | Reasoning only versus budget |
| sampling | Frozen retrieval | On | 16,000 | 1 / 1 | Vendor reasoning sampling versus reasoning |
| definitions | Frozen retrieval | On | 16,000 | 1 / 1 | Add explicit legal label/absence definitions |
| full_document | Complete publisher spans | On | 16,000 | 1 / 1 | Remove retrieval omission; no gold-selected context |
| ids | Frozen retrieval | On | 16,000 | 1 / 1 | Evidence selection; code copies whole spans |
| schema_in_prompt | Frozen retrieval | On | 16,000 | 1 / 1 | JSON-object channel with schema also in prompt |

The last five arms compare against sampling, not each other. ID-only changes evidence granularity, so a strict extraction-score difference is not a pure model-quality effect. JSON-object mode changes both decoding and schema delivery; this is a complete protocol comparison, not an isolated decoder claim. Stochastic single draws are a screening experiment, not a stable estimate. Repeat promising sampling configurations before selecting one.

NVIDIA's model card recommends temperature 1.0/top_p 1.0 for reasoning and 0.6/0.95 for tool calling. This experiment tests the reasoning recommendation; the benchmark is not a tool-calling task. [Model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16).

## Scoring and safeguards

Keep frozen strict correctness and evidence F1. Also report acceptance, truncation, extraction presence/absence accuracy among valid responses, and denominators. Mechanical evidence validity is not semantic accuracy. Never send gold labels or answer annotations to the endpoint. Full context comes from publisher spans in a read-only local database restricted to the two public datasets. Never shorten a document silently: log a context-budget failure instead. Conservative byte accounting reserves output and template space; it is not exact tokenizer accounting.

No private documents or their derivative aggregates enter this experiment. Do not add local event logs to Git or the website. No retries replace a failed observation. New executions require a new directory.

## Decision standard

This small, exposed diagnostic can identify mechanisms and nominate configurations. It cannot establish a production winner or prove a serving defect. Freeze a selected configuration after screening, then confirm on document-disjoint, untouched public examples with document-cluster uncertainty, absent-field errors and operational latency. Compare another model on identical inputs. Where available, test the same checkpoint in an independently configured deployment to isolate serving or precision effects. A poor result without that control does not prove a bad deployment.

The immediate outcome should be a configuration recommendation with its measured limitations, not a claim that Nemotron is irredeemable.
