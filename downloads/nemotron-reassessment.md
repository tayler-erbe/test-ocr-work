# Nemotron controlled reassessment

Completed 26 October 2026: **192 requests, eight configurations, the same 24 public diagnostic cases** (12 CUAD, 12 ContractNLI). All cases were previously exposed. This is exploratory, not a production model ranking.

| Configuration | CUAD strict correct | CUAD accepted | NLI strict correct | NLI accepted |
|---|---:|---:|---:|---:|
| baseline | 1/12 | 2/12 | 5/12 | 12/12 |
| budget | 1/12 | 2/12 | 5/12 | 12/12 |
| reasoning | 4/12 | 7/12 | 6/12 | 11/12 |
| sampling | 5/12 | 8/12 | 7/12 | 9/12 |
| definitions | 4/12 | 7/12 | 5/12 | 7/12 |
| full_document | 3/12 | 7/12 | 7/12 | 11/12 |
| ids | 4/12 | 12/12 | 7/12 | 9/12 |
| schema_in_prompt | 4/12 | 7/12 | 9/12 | 12/12 |

## Completed follow-up: 26 October 2026

The Nemotron evaluation round is complete: **312 requests across 84 public cases**. The exploratory campaign ran eight configurations on the same 24 previously exposed cases (192 requests); the separate reasoning comparison ran two configurations on 60 cases from 60 documents (120 requests). Requests are repeated observations, not unique documents.

| Public task | Reasoning off | Reasoning on | Mechanically accepted, off / on |
|---|---:|---:|---:|
| CUAD extraction, 30 documents | 3/30 (10.0%) | 13/30 (43.3%) | 7/30 / 20/30 |
| ContractNLI, 30 documents | 5/30 (16.7%) | 12/30 (40.0%) | 28/30 / 22/30 |

Both comparison arms used identical prompts, retrieved context, JSON schema, temperature zero and a 16,000-token output budget. Only reasoning was switched. Cases were frozen before inference; reference labels never entered model requests. The frozen scorer was unchanged; failures stayed in every denominator. Reasoning-on truncated once per task; reasoning-off did not truncate. Mechanical acceptance is not semantic correctness.

**Configuration contributed to the earlier poor result.** Reasoning improved strict correctness on this separate public set; increasing the budget alone did not improve the exploratory baseline. Evidence-by-ID removed CUAD validation failures in the exploratory arm, but did not establish correct answers. JSON-object/schema-in-prompt and full-document arms were exploratory protocol comparisons, not isolated proof of a decoding or deployment defect.

**This is not production approval or a cross-model winner.** Absolute strict scores remain low. The 60-case set has no matched second-model results. Documents were absent from locally recorded earlier runs, not proven absent from pretraining or unrecorded experiments. Small samples and single stochastic exploratory passes limit conclusions. No evidence establishes a faulty deployment or an irredeemable model.

Next: compare the exact second API model on identical inputs; repeat promising stochastic configurations; improve evidence selection and validation; and validate on representative human-labelled documents before promotion. The completed benchmark round does not mean all optimization is exhausted. Institutional/private validation must stay in an approved environment.

## What this changes

- The original baseline reproduced at 1/12 CUAD and 5/12 NLI. Raising the budget alone to 16,000 left both strict scores unchanged.
- At the same 16,000-token budget and temperature zero, enabling reasoning increased CUAD strict correctness to 4/12 and NLI to 6/12. These small paired results nominate a configuration; they do not establish a population-level gain.
- The vendor-recommended reasoning sampling configuration reached 5/12 CUAD and 7/12 NLI in one stochastic pass. It needs repeated runs before selection.
- JSON-object mode with the schema also written into the prompt reached 9/12 NLI with all 12 responses accepted. In the strict-schema sampling arm, label-only correctness was also 9/12, but three label/evidence inconsistencies reduced strict correctness to 7/12. This is evidence-interface sensitivity, not proof that constrained decoding is generally harmful.
- ID-only extraction removed CUAD evidence-validation failures (12/12 accepted), but strict correctness was still 4/12. Literal provenance and semantic correctness are different checks; whole-span copying also changes answer granularity.
- Full-document context was not a universal remedy: 3/12 CUAD and 7/12 NLI in this run. More context can add distractors; no causal claim that longer context hurts follows from one stochastic pass.
- Baseline CUAD had one truncation; no other configuration truncated. Many remaining failures involve quotes absent or ambiguous within their cited span.

## Interpretation

**Do not reject Nemotron as irredeemable.** The tested configuration mattered. The software and evidence interface also matter. Neither a bad deployment nor a model-family limitation has been established. More budget alone was insufficient; reasoning and output protocol deserve further testing.

The separate fixed reasoning-on/off comparison completed: 120 requests over 60 public cases from 60 documents absent from locally recorded earlier runs. Both arms used temperature zero, 16,000 output tokens, identical retrieved context, prompts, schemas and scoring. CUAD strict correctness improved from 3/30 to 13/30; NLI from 5/30 to 12/30. Reasoning-on had one truncation per task; reasoning-off had none. All failures remained in denominators. These results support enabling reasoning for further work, but neither configuration establishes production adequacy. “Unused” does not establish absence from model pretraining or unrecorded experiments.

## Reproduction and limits

See [the frozen experiment plan](https://github.com/tayler-erbe/test-ocr-work/blob/main/docs/nemotron-reassessment.md) and the adjacent aggregate JSON. The unchanged legal scorer and public input pack live under benchmarks/harness/. Raw final answers and deployment metadata remain local. No reasoning traces or private documents were retained in this repository.

Serving metadata and service version matched the prior local audit. That is not a model-weight checksum or proof of correct backend configuration. Latencies are observed request times, not isolated sustained throughput. Small exposed samples, multiple comparisons and single stochastic draws prohibit production approval or a universal ranking.

## Separate public confirmation

| Task | Reasoning off, 16k | Reasoning on, 16k | Accepted off / on |
|---|---:|---:|---:|
| CUAD, 30 documents | 3/30 | 13/30 | 7/30 / 20/30 |
| ContractNLI, 30 documents | 5/30 | 12/30 | 28/30 / 22/30 |

The cases were fixed before inference. This was a pre-specified reasoning contrast after exploratory work, not a fully independent external replication or evidence of absence from model training. No comparison model was run on these 60 cases; these results cannot establish a cross-model winner. The adjacent aggregate report includes document-level paired uncertainty and label/evidence diagnostics.

## External evidence and the next optimization round

Research checked 26 October 2026. The completed round is not a demonstrated model ceiling.

### What the released model is intended for

NVIDIA positions the text Nano checkpoint for general reasoning, coding, agents, chat and retrieval-augmented generation. Its headline suite covers math, coding, tool use, instruction following and long context; these are not interchangeable with legal extraction plus exact evidence. The model card recommends temperature 1.0/top_p 1.0 for reasoning, versus 0.6/0.95 for tool calling. Our temperature-zero confirmation isolated the reasoning switch; it was not an optimization of every generation setting. A sampling arm was screened on 24 cases, but not independently confirmed or repeated. [NVIDIA model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16).

NVIDIA's reproduction recipe uses task-specific prompts and settings, repeated samples on several benchmarks, and much larger generation caps for some tasks. It therefore does not support equating our single-pass strict scores with the published benchmark scores. Its large default output cap is not evidence that increasing our cap will fix errors: our 2k-to-16k budget-only arm did not improve strict scores. [Reproduction recipe](https://github.com/NVIDIA-NeMo/Evaluator/blob/main/packages/nemo-evaluator-launcher/examples/nemotron/nano-v3-reproducibility.md).

### What other practitioners actually reported

- Firsthand reports include good results on coding, long instructions and RAG/MCP applications. These are uncontrolled anecdotes, not legal benchmark replication. [Community experience](https://www.reddit.com/r/LocalLLaMA/comments/1pocsdy/nemotron_3_nano_30b_is_amazing_tldr/).
- A tester reported hallucinations and missed details in targeted extraction at about 200k context, including after changing quantization. Their runtime, quantization and context differ from ours, so this supports investigating a failure mode, not diagnosing our endpoint. [Firsthand extraction report](https://www.reddit.com/r/LocalLLaMA/comments/1pn8upp/nvidia_releases_nemotron_3_nano_a_new_30b_hybrid/).
- A practitioner evaluated section-based fact extraction with word-for-word evidence validation and reported a benefit from thinking. This used **Nemotron 3.5 Lightning**, not our Nano checkpoint, only 48 sections from two documents, and an uncalibrated model judge. It is a useful architecture hypothesis, not a comparable accuracy result. [Practitioner's methods and caveats](https://threadunsafe.dev/screaming-in-space/continuum/platform/benchmarks/models/nemotron-3.5-lightning-30b-a3b).
- NVIDIA reports a legal-pretraining ablation improving a proxy LegalBench average from 64.6 to 74.7. That is a separately trained ablation, not an accuracy claim for our deployed artifact or our strict scorer. It suggests domain adaptation may help, without proving the existing endpoint should score 74.7 here. The dataset also names Contract-NLI-derived training material; training/test overlap must be examined before any future adaptation. [Legal dataset card](https://huggingface.co/datasets/nvidia/Nemotron-Pretraining-Legal-v1/blob/c02b324e8b94a3f06800e46273bc0d59be295c6b/README.md).

The targeted search did not identify a reproducible, independent evaluation of this exact deployed checkpoint on our CUAD/ContractNLI protocol. Search results titled as model comparisons were not treated as evidence without matched underlying results. Different Nano, VL, Omni and Lightning variants must not share scores by name association. The tested text model does not directly read PDF images; OCR/vision is a separate pipeline component.

### Why 13/30 and 12/30 are not the whole diagnosis

On the 60-case reasoning-on comparison, CUAD presence/absence was correct in 25/29 parseable responses (25/30 counting the invalid response as failure), but this is not answer extraction accuracy. Nine responses failed quote-to-span validation and one was invalid/truncated. ContractNLI label-only correctness was 17/29 parseable responses (17/30 counting failure), versus 12/30 strict; seven responses had label/evidence inconsistencies and one was invalid/truncated. These checks overlap and must not be summed as exclusive failure categories. See the confirmation aggregate JSON.

These diagnostics justify work on evidence representation, retrieval and semantic decisions. They do not justify relaxing the existing strict scorer or presenting presence detection as successful extraction. The balanced CUAD set contains 15 absent cases: an always-empty answer baseline would score 15/30 under the strict absent-answer rule, above the observed 13/30. That calculated trivial baseline is not a useful extractor, but it prevents overstating relative improvement. For balanced three-label NLI, a constant label has 10/30 label accuracy before evidence requirements.

### Proposed next experiment, not yet run

1. Audit exact model build, chat template, reasoning parser and effective request settings. Run a small mechanically scored capability check using the provider's published protocol; passing would not prove legal quality, but failing would justify serving investigation.
2. On development cases, separate decisions: select clause/evidence IDs first, then label or extract; code copies exact evidence. Compare the existing context with larger uncut clause-level context. Use gold context only as a separately labelled diagnostic upper bound, never as deployable retrieval or an input containing reference answers.
3. Compare temperature-zero and task-appropriate sampling with repeated runs. Use disjoint worked examples from development documents; keep all original scorers and failures. Measure accuracy, abstention, quote validity, latency and tokens separately.
4. Freeze the resulting configuration before another document-disjoint confirmation. Compare a second model on identical inputs. Keep the current 60 cases as exposed diagnostics after any tuning on their failures.

No new inference was performed for this literature review. These are proposed experiments, not promised improvements or production approval.
