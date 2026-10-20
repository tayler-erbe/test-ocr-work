# Legal comparison, desktop side (20 Oct 2026)

Local models only (qwen3:32b on Ollama 0.34.4, digest 030ee887880f; Qwen3-VL-32B-Instruct-AWQ on vLLM, max_model_len 10240). Pack checksums verified; the scorer's prompt template rebuilds all 24 pack requests byte for byte. Reference answers went to the unchanged scorer only, never to a model.

## Results

12 questions per task, all previously seen during diagnostics. One question moves a score by about 8 points: exploratory, not a ranking.

| Model and arm | CUAD strict | CUAD failed | CUAD evidence F1 | CUAD present/absent right | CUAD answers recovered | NLI strict | NLI failed | NLI evidence F1 |
|---|---|---|---|---|---|---|---|---|
| Qwen3-32B baseline | 5/12 | 2 | 0.443 | 7/12 | 0.333 | 9/12 | 1 | 0.601 |
| Qwen3-32B reasoning, 16k | 4/12 | 4 | 0.387 | 8/12 | 0.458 | 9/12 | 0 | 0.603 |
| Qwen3-32B full document | 4/11 (1 too long) | 4 | 0.467 | 10/11 | 0.667 | 9/12 | 1 | 0.601 |
| Qwen3-VL-32B baseline | 5/12 | 3 | 0.478 | 9/12 | 0.458 | 8/12 | 1 | 0.551 |

Pack comparators: Nemotron revised 1/12 CUAD, 5/12 NLI; Qwen2.5 7B 7/12 and 6/12 (600-token budget, not fully matched).

## Findings

- **No truncations or call errors.** Every failure is a validation failure: a CUAD quote not found, or ambiguous, in its cited span (2 to 4 per arm), or one NLI label inconsistent with its evidence.
- **Reasoning on** (Qwen3-32B, 16k budget): reasoning present on all 24; about 4x output tokens; no strict gain; CUAD quote failures doubled (2 to 4).
- **Full document:** 11 of 12 CUAD contracts fit in 32,768 tokens (largest run 24,366; one at 52,712 not run). Answers recovered rose 0.333 to 0.667 and present/absent judgments 7/12 to 10/11, but quote-to-span validity fell 0.78 to 0.52, so strict scores did not rise. The model finds the right clauses and fails at binding quotes to spans, which supports selecting evidence by ID and copying text in code. For ContractNLI the pack excerpts already covered the whole document in 11 of 12 cases, so this arm adds nothing there.
- **NLI labels (Qwen3-32B baseline):** entailment 4/4, contradiction 3/4, not mentioned 2/4. No sign of the affirmative bias seen in the Nemotron configuration (0/4 contradictions), though 4 per label is only suggestive.
- **Interpretation:** on identical inputs, prompts, schemas and scorer, both 32B Qwen models clearly outperform the revised Nemotron configuration. This is consistent with a Nemotron configuration or deployment problem but does not prove one: architecture, quantization and serving differ, and the sample is small.

## Files

`run_desktop.py`, `run_qwen3_32b_window.py`, `summary.json`. Raw model responses stay local in `desktop_results/local/` (git-ignored per the pack rules).
