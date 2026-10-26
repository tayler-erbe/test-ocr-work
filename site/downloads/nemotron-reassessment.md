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
