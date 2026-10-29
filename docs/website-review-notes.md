# Website review notes

These notes consolidate the owner's walkthrough of the current website. They are requirements for a later revision, not a record of changes already implemented. Continue collecting feedback before rebuilding the website.

## Handoff summary

The owner has completed this walkthrough and wants a second opinion before the first implementation pass. The reviewed surface is primarily the detailed case study and its explorer, not just the separate leadership landing page. No website changes or new inference have been made during this note-taking phase.

**Preserve:** The professional visual design, interactive result exploration, useful hardware section, working hardware anchor navigation, and access to the original technical evidence.

**Main revision:** Make the site a decision aid for leadership: clear task-specific recommendations, hardware/budget context, understandable measures and examples, available-only controls, visible legal findings, readable report pages and actual PDF downloads. Lead with implications, then supporting evidence and optional technical detail.

**Proposed page order from the owner:** Findings → Hardware → Results → Methods → Next steps. Resources follow, grouped for leadership first, downloadable data second, repository/code last.

**Evidence checks before rewriting:** Reconcile the latest final results with every dashboard import; audit missing values; resolve the apparent Qwen/parser ranking contradictions using matched tasks/sets; distinguish models from configurations and pipelines; verify costs and hardware fit rather than making purchase or value claims from the available rigs.

The numbered sections below retain the detailed comments, concrete examples, verified local checks and acceptance criteria. Later suggestions refine earlier layout alternatives; they should be reconciled into one coherent design rather than implemented as competing controls.

## Purpose and audience

The website should help a reader decide which document models and hardware to consider for their own use case and budget. Leadership needs clear recommendations and practical costs before technical detail. Preserve the detailed case study as a separate reference.

The central question is: **For my documents and budget, what setup should I consider, why would I choose it, and what can I reasonably expect it to do?**

Explain potential applications such as research proposals, awards, procurement packets and other mixed PDFs. Distinguish possible applications from workflows actually validated in the evaluation.

## 1. Prevent empty results in the explorer

**Concern:** The explorer allows filter combinations with no recorded configurations. A blank chart and empty table make the work look incomplete, even when the combination was never evaluated.

**Requested change:** Offer only combinations backed by recorded results. When a task changes, update the available hardware, evaluation split and method choices so the visitor retains a populated view. Do not imply that a missing experiment is a failed model.

**Additional example supplied during the walkthrough:** Whole-page text → Desktop · 32 GB → Confirmation v1 → All recorded methods displays “No recorded configurations match these filters” and an empty chart/table. Record this exact path as an acceptance-check case, alongside the earlier Prose crop OCR → Desktop · 32 GB → Confirmation v3 example. The owner reiterated that selectable combinations leading to nothing feel sloppy; preventing these paths is a required usability fix, not just a change to the empty-state wording.

Check availability across all dependent filters, not just the task dropdown. Make unavailable choices unselectable or omit them. If an earlier selection becomes invalid after another choice changes, move to a valid combination with a clear explanation. Treat “Desktop · 32 GB” as GPU memory, distinct from a model's parameter count (for example, 32B).

**Review criterion:** A visitor following the offered filter choices should not reach an empty results page. The behavior for old links with unavailable combinations must also be handled clearly.

## 2. Make PDF the primary report download

**Concern:** Markdown is inconvenient for many leadership readers. A document that requires an explanation of how to open it is a barrier to sharing the findings.

**Requested change:** “Download the final advisory” should deliver a formatted PDF. Preserve Markdown in the repository for technical readers.

**Review criterion:** The downloadable PDF opens normally, has readable tables, page numbers and clickable sources, and retains the report's findings and qualifications. Verify its rendered pages before delivery.

## 3. Replace activity counters with useful decision information

**Location confirmed by the walkthrough screenshot:** The four-item summary strip near the top of the detailed case study (`site/technical.html`, `.stat-strip`), with its explanatory sentence immediately below. This is the specific section behind the feedback in sections 3–6, rather than a request to add more headline statistics.

| Current item | Requested treatment |
| --- | --- |
| “40,975 — earlier vision rows; round 3 separate” | Remove from the headline or move to methods with a plain explanation of repeated result rows. It does not communicate independent document coverage or business value. |
| “2 — machines in the vision campaign” | Replace the bare count with named tested hardware, memory capacity and its practical role. Link to model fit and complete-system cost estimates, separating measured rigs from proposed deployment targets. |
| “1,322 / 722 — confirmation questions / charts” | Retain the useful sample information, with dataset provenance, selection/split explanation, purpose, relevance and generalization limits. See section 5. |
| “3 / 3b / 3c — completed evaluation rounds” | Replace unexplained labels with a short account of the questions these stages answered and the decisions they supported. These are evaluation-stage labels, not three website versions; verify their relationship to earlier rounds against the protocols. See section 6. |

The sentence below the strip correctly distinguishes repeated rows from unique documents and software checks from accuracy. Preserve those distinctions in the revised explanation, but do not rely on a footnote to make otherwise unexplained headline numbers meaningful.

**Concern:** Headline counts such as “40,975 earlier vision rows; round 3 separate” do not explain value to the reader. A result-row count is not a count of independent documents and should not be used as an unexplained sign of scale.

**Requested change:** Prioritize the task, recommended model, expected strengths and limitations, hardware needed, and approximate cost. Move technical campaign bookkeeping into the methods reference where appropriate.

**Review criterion:** The opening helps a reader understand what the system could do for them and what it would take to run it, rather than merely how much evaluation activity occurred.

## 4. Identify the hardware and cost explicitly

**Concern:** “Two machines in the vision campaign” does not tell a reader what equipment they would need to replicate the work or use a selected model.

**Requested change:**

- Name the actual tested machines, GPUs and GPU memory; include verified CPU and system-memory specifications where available.
- Separate measured configurations from proposed deployment targets, including the single L4 and L40S options. State what remains untested.
- Map recommended models and workloads to practical hardware requirements, with context, image size and concurrency qualifications.
- Give dated estimates for a complete usable system, not just a GPU. Separate purchase cost from engineering, human review, maintenance and other operating costs.
- Explain the decision between local control and cloud convenience. Keep estimated comparisons distinct from measured costs; do not imply that local hosting alone establishes security.

**Review criterion:** A reader can identify a plausible starting setup and budget for their task without inferring requirements from unexplained campaign labels. Do not invent missing specifications, target-server throughput or cloud savings.

## 5. Give the chart confirmation sample context

**Concern:** “1,322 confirmation questions / 722 charts” is useful, but needs an explanation. The counts alone do not tell readers where the material came from, how the evaluation set was constructed, why it was selected, or how it relates to their documents.

**Requested change:** Retain the counts and explain:

- **Source:** Name the public dataset and link to its original source and the recorded evaluation protocol.
- **Construction:** Explain how existing charts, questions and reference answers were selected and split for this evaluation. Distinguish source-dataset creation from project-specific preparation. Describe any generated material explicitly; verify the details before writing them.
- **Meaning:** There were 1,322 questions about 722 charts, so some charts had multiple questions. These are not 1,322 independent documents.
- **Purpose:** Explain which skills the questions probe, such as locating values, comparing quantities and performing calculations, as supported by the recorded task definitions.
- **Why confirmation matters:** Explain that methods were chosen using development data and then checked on a separate confirmation set. Preserve the recorded limits on prior use and selection.
- **Relevance:** Connect these skills to chart-bearing reports and proposal or award attachments as potential applications. Explain why this is a useful component test rather than proof of end-to-end performance on those workflows.
- **Limits:** Public chart benchmarks do not establish accuracy on private documents, poor scans, whole mixed packets or every field a business needs. Questions sharing a chart are correlated. Project-unused data is not necessarily absent from model pretraining.

**Review criterion:** A nontechnical reader can answer “Where did these examples come from, what was tested, why should I care, and how far can I generalize the findings?” after reading the explanation.

## 6. Explain why the evaluation continued across rounds

**Concern:** Showing three rounds or versions without their purpose looks like repeated activity. Readers need to understand what was learned, what remained unresolved, and why another round was warranted.

**Requested change:** Present a short, evidence-linked progression. For each round, state the question, what changed, the finding, and the decision it enabled. Verify the sequence against the recorded protocols rather than treating round numbers as interchangeable versions of the same experiment.

Explain why additional work was justified when it addressed an unanswered question, investigated a failure, tested a new candidate or checked a proposed improvement on separate data. Distinguish these purposes from simply rerunning until a favorable score appeared. Include unsuccessful approaches and inconclusive findings, and explain why the candidate evaluation eventually stopped.

Explain the methodology in terms of the decisions it protects:

- **Defined tasks and reference answers:** judge the capability the workflow actually needs, using reference-based scoring rather than another model's opinion.
- **Frozen prompts, cases and scorers:** make comparisons inspectable and prevent moving the scoring rules after seeing results. Disclose configuration differences that limit comparability.
- **Development versus confirmation:** use development examples to choose an approach, then check that choice on separate examples. Identify exploratory findings and reused cases instead of calling everything an independent confirmation.
- **Paired comparisons and uncertainty:** compare methods on the same cases where the protocol supports it, and show how much confidence the sample allows. Account for related questions sharing the same source chart or document.
- **Predefined success criteria:** distinguish a measured improvement from a result that passed the planned acceptance rule. A better text score does not compensate automatically for losing numbers.
- **Failures and truncations:** retain and report them so the result reflects the tested setup, including its practical limits.
- **Domain validation next:** public benchmark results help select pilot candidates; representative business documents and human labels determine fitness for the actual workflow.

**Presentation direction:** Use a simple “Question → Test → Finding → Next decision” timeline. Keep statistical details in the technical reference while explaining their purpose in plain language. Do not collapse different tasks, confirmation sets or hypotheses into a single rising score.

**Review criterion:** A leadership reader can explain why the project needed multiple rounds, what each added, and why the final recommendation is more defensible than a single model demo. The explanation should also make clear what the methodology has not established.

## 7. Lead with clear, supported recommendations

**Location:** The detailed case study's “01 / What the evidence says” cards: PaddleOCR-VL-1.6, Nemotron 3.5 Parse, and the chart-method card.

**Concern:** The opening does not clearly communicate what each model did best or why it was recommended. “No universal winner” and “prototype choices within the tested configurations” are qualifications, not useful recommendations by themselves. The owner remembers strong Qwen results and sees Qwen at the top of the page-text chart, creating an apparent contradiction.

**Requested change:** Lead with the strongest supported choice for each defined use case. Give the model, the job, the reason to choose it, the important limitation, and the evidence behind the recommendation. Keep the distinction between the highest displayed score and the recommended operational trade-off explicit. Do not turn the owner's question into a verified finding before auditing the underlying results.

**Reconciliation required before rewriting recommendations:** The supplied explorer screenshot is Whole-page text / Both machines / Confirmation v2 / All recorded methods. It shows Qwen3-VL 32B AWQ with layout masking at word F1 0.881, alongside numeric recall 69.4%. The summary cards describe later parser results. Explain the different evaluation sets, methods and objectives; do not compare scores from different sets as though they came from one matched experiment. Verify whether the final recommendation is supported by the latest appropriate paired comparison and clearly show where Qwen remains a strong choice. Audit the actual source aggregates before resolving the ranking.

**Review criterion:** A reader can understand why the top row in a particular explorer view may differ from the model recommended for a numeric-sensitive workflow. Neither the card nor the chart should appear to contradict the other without explanation.

## 8. Translate technical metrics and hypothesis labels

**Concern:** “TEDS,” “0.852,” “H1 passed,” “H2,” “Word F1,” and “numeric non-inferiority” are not self-explanatory to leadership. The current headings make the reader decode the experiment before understanding the result.

**Requested change:**

- Explain TEDS in plain language before using the abbreviation: Tree-Edit-Distance-based Similarity, a reference-based table similarity measure. Explain what it compares in this evaluator, its 0–1 scale, and that higher is better. Verify the exact scorer behavior against the implementation.
- Explain that 0.852 is a similarity score, not proof that 85.2% of tables or financial fields were completely correct. A percent-style display must not imply accuracy.
- Replace “H1 passed” in the main recommendation with the plain-language result: the planned table-improvement test passed while satisfying the specified numeric-preservation criterion. Explain the threshold in the methods reference; keep H1 as a technical cross-reference if useful.
- Replace “numeric question open” with a clear statement of what remains uncertain. Here it concerns preservation of numbers during page transcription, not necessarily questions posed to a model.
- Explain word F1 as overlap with reference words, not overall document accuracy, semantic correctness or fidelity of every number.
- Explain numeric recall as recovery of reference numbers, not proof that each recovered amount is correct and attached to the correct field.

**Review criterion:** Every prominent result can be understood without prior knowledge of the abbreviations. Preserve the technical definitions without making them the headline.

## 9. Define tasks and show what the models actually received

**Concern:** Terms such as table extraction, whole-page text and numeric questions do not show a visitor what an input or output looks like. The owner specifically asks for concrete examples and an explanation of embedded images and scanned material.

**Requested change:** Add a short definition and a representative input/output example for each explorer task, updating with the selected task:

- **Whole-page text:** Explain whether the evaluated input was a page image, parsed text or another representation. Show a page and a short transcription excerpt. Do not call a vision-based page-reading experiment a text-only input experiment.
- **Tables:** Show a table crop or scanned table image and the corresponding recovered rows, columns and values. Explain what structure and number preservation mean in practice.
- **Charts:** Show a chart and a representative question and answer; distinguish answering a chart question from reconstructing chart data as a table.
- **Prose crop OCR:** Show that this concerns a cropped text region rather than a complete mixed page.
- **Numbers:** Illustrate a missed or misplaced amount or date, showing why a cleaner-looking transcription can still be unsuitable for financial use.

Use appropriately licensed public benchmark examples or clearly labelled fabricated illustrations. Keep reference answers separate from inference inputs. State whether an example is illustrative or an actual recorded model output; do not fabricate a successful model response.

**Vision coverage:** Explicitly identify which evaluated systems read images, including the Qwen vision-language models and applicable document parsers. Explain where those capabilities help with scans, embedded tables, charts and images. Image input capability is not proof of reliable interpretation of every figure or arbitrary mixed packet. Explain any untested document types and preserve native spreadsheet parsing as a distinct route.

**Review criterion:** A leadership reader can describe what the model was shown, what it returned, and what was checked for the selected task.

## 10. Make links land on the promised evidence

**Concern:** “Inspect final table results,” “Inspect page results,” “Compare chart answers,” and the masking warning's “See the evidence” all scroll to the same explorer without necessarily showing the relevant comparison. The owner likes the explorer, but the repeated generic destination feels redundant and does not fulfill the different link promises.

**Requested change:** Keep the explorer and improve the connection between claims and evidence. Either use one clearly labelled general explorer link or make each task-specific link open a populated, appropriate task/split/hardware/method view, with visible context. Validate navigation and browser back/forward behavior alongside the empty-filter fix.

**Masking warning:** The owner expected “See the evidence” to reach the evidence/methods discussion (“Evidence first / From the page to the decision”), rather than an unchanged explorer. Choose a destination that actually explains and supports this specific masking trade-off: an explicit comparison with numeric recall and source links, with the methods discussion linked where helpful. A generic evidence-by-ID explanation alone would not substantiate the masking score claim. Make the link wording match the destination and confirm the intended experience during review.

**Review criterion:** Each link reveals the result or explanation its wording promises. Task links must not silently inherit an unrelated filter selection or land on a blank view.

## 11. Preserve the explorer and prepare a complete revision handoff

**Positive feedback to preserve:** The owner repeatedly emphasized that the interactive explorer is useful and should remain. The requested work is clearer recommendations, definitions, evidence navigation and valid filter choices, not removal of the comparison tool.

**Process:** Capture every walkthrough comment in this single document. Keep owner observations separate from verified findings and implementation decisions. Continue collecting feedback before implementation. Once authorized, implement an initial revision against these notes, then use this document for a subsequent review and refinement pass. Do not represent proposed changes as completed or a ranking concern as resolved without verification.

**Completion review should cover:** recommendation consistency; metric definitions; task examples; vision-model coverage; claim-specific links; populated filters; meaningful hardware/cost context; dataset and round explanations; a usable PDF download; preservation of the detailed version; and consistency between the leadership and technical views.

## 12. Make evaluation stages meaningful to the reader

**Location:** Explorer → Whole-page text → Desktop · 32 GB → Development → All recorded methods, as shown in the owner's screenshot. The evaluation-split dropdown lists Development and several confirmation versions, including final parsers.

**Concern:** Readers cannot tell what “evaluation split” means, how the choices differ, why they would select one, or which should guide a decision. A dense explanation mentioning final-parser pages and H2 also appears while a development comparison is selected, mixing the current view with unrelated stage information.

**Requested change:** Explain development as the examples used to explore and choose methods, and confirmation as separate examples used to check specified choices, subject to the actual protocol and reuse history. Give each available stage a short, descriptive label and purpose, dataset/task coverage, and an explanation of how its result should be used. Do not imply that higher version numbers alone mean better results or that every stage evaluated the same candidates on the same data.

Consider presenting the decision-relevant final comparison first and placing historical/development exploration behind an optional control. Preserve access to the history. Tie the explanatory text to the selected task and stage; do not show final-parser caveats as if they describe the development rows currently displayed.

**Review criterion:** Before changing stages, a reader can understand what they will see and why it matters. The current view explains its own sample, methods and limits without forcing readers to interpret internal protocol labels.

## 13. Explain method comparisons, table columns and the recommendation together

**Concern:** The development screenshot looks like two versions of Qwen3-VL 32B AWQ competing for a winner. It actually labels the same model with two processing methods: layout masking and baseline. The word-score bars favor one method while the numeric column favors the other, without a clear explanation of what that means for a business task.

**Observed values in the supplied screenshot (verify against source before implementation):**

| Same model; different method | Word F1 | Pages / failures | Numeric recall | Median time |
| --- | --- | --- | --- | --- |
| Qwen3-VL 32B AWQ · layout masking | 0.895 | 40 / 0 | 72.0% | 11.87 seconds |
| Qwen3-VL 32B AWQ · baseline | 0.809 | 40 / 0 | 90.9% | 16.50 seconds |

**Requested change:**

- Explicitly say when rows represent the same model with different preprocessing, rather than different model versions. Explain baseline and layout masking in plain language and show what masking changes in the input.
- Explain that 0.895 and 0.809 are word-F1 scores, not overall accuracy percentages. The chart ranks this one metric, not overall suitability.
- Show numeric preservation alongside text recovery so the most prominent bar does not imply an overall winner. In this view, masking has a higher word score but lower numeric recall.
- Use meaningful column labels: “Pages tested,” “Processing failures,” “Reference numbers recovered,” and “Typical processing time,” with concise definitions and task-appropriate units. Separate counts or write “40 pages tested · 0 processing failures” instead of “40 / 0.”
- Explain that no processing failure does not mean an error-free extraction. Report missing values as “not reported,” distinct from zero.
- Explain median as the middle observed processing time and state its measurement scope, including whether preprocessing and model loading are included. Verify the runner's timing definition before claiming end-to-end latency.
- Correct the direction of speed comparisons in the presentation: the screenshot's masking time is lower (11.87 versus 16.50 seconds), not longer. Record this neutrally so the revised page removes the ambiguity that led to the confusion.
- Add a short interpretation tied to a stated objective: for number-sensitive documents, retaining numbers can matter more than maximizing word overlap. If no candidate meets the acceptance criteria, state that instead of inventing a winner. Development results are exploratory and require the appropriate confirmation evidence.

**Presentation direction:** Clearly distinguish “highest text-overlap score,” “best numeric preservation,” “fastest in this measured comparison,” and “recommended starting configuration for this use case.” These may be different rows. Do not collapse them into an unvalidated combined score or claim statistical superiority from these displayed averages alone.

**Review criterion:** A nontechnical visitor can explain the difference between the two rows, what every displayed number means, and which trade-off matters for their task. Recommendations should remain understandable without hiding conflicting metrics or the uncertainty behind them.

## 14. Turn the page-text comparisons into actionable advice

**Locations supplied:** Whole-page text / Desktop · 32 GB / Confirmation v2, followed by Confirmation v3 · final parsers. The owner is still collecting feedback and intends to continue to other sections.

**Concern:** Values change across development and confirmation views without enough explanation of what changed in the experiment. Sorting bars by word F1 appears to identify a winner, while numbers, time and failures suggest different trade-offs. The reader is left asking which result to use and what advice the evaluation provides.

**Requested change:** Provide a short comparison-specific conclusion: what was tested, what changed from the earlier stage, the important result, which use case it supports, and what remains unresolved. Explain whether a stage changes the data, method, candidate model, integration or some combination. Verify these details against the protocols; do not infer them from the version label or apparent score increase. Do not select the highest score across different evaluation sets as the “best version.”

### Confirmation v2: explain the gaps and the trade-off

The screenshot shows the same Qwen3-VL 32B AWQ model with masking and baseline, 80 pages each: word F1 0.881 versus 0.814; numeric recall 69.4% versus 87.2%; failure counts and median latency displayed as dashes.

- Explain why this is a different sample from the 40-page development comparison, and what confirmation was intended to check.
- Missing timing and failure values look incomplete. Investigate whether the original records contain them and whether they can be imported reliably. If unavailable, say “not reported in the available source” and explain the resulting comparison limit. Do not invent timings, treat missing failures as zero, or rerun frozen work simply to fill a visual gap without separate authorization and labelling.
- State the decision implication of higher word overlap but substantially lower number recovery. Avoid calling masking the overall winner solely because its bar is longer.

### Confirmation v3: explain what a parser and a pipeline are

Define a document parser by its actual role in these tests: converting a document/page representation into extracted text or structured content. Show representative input/output so the reader does not assume “parser” means only simple text extraction. Explain which systems use page images and which outputs were scored. The label “final parsers” means the final recorded parser comparison, not production-approved tools.

Distinguish a model called directly through the recorded adapter from its official processing pipeline. Explain what extra processing the pipeline actually performs, based on inspected configuration, rather than treating all rows as five independent model families. In particular, distinguish `paddle-pipeline` from `paddleocrvl [budget8192]`. Translate internal labels such as `[budget8192]` into an optional explanation of the output limit; do not lead with the internal run name.

**Observed screenshot values (verify against source before revision):**

| Displayed configuration | Word F1 | Pages tested | Processing failures | Reference-number recall | Median time |
| --- | --- | --- | --- | --- | --- |
| Paddle official pipeline | 0.922 | 80 | 0 | 77.1% | 4.01 s |
| Nemotron Parse single pass | 0.899 | 80 | 1 | 88.2% | 3.06 s |
| olmOCR-2 single pass | 0.898 | 80 | 0 | 70.6% | 11.40 s |
| Qwen3-VL 32B AWQ baseline | 0.820 | 80 | 3 | 88.3% | 21.59 s |
| PaddleOCR-VL direct single pass | 0.737 | 80 | 9 | 78.2% | 3.17 s |

### Explain the metric and the choice at the point of use

- Spell out word F1 in accessible terms: a balance between recovering reference words and avoiding extra/unmatched words. Explain precision and recall only as needed. It is not “word function 1” and is not overall extraction accuracy. Verify the actual tokenization, matching, aggregation and treatment of failed cases before illustrating the formula or interpreting close scores.
- Explain the 0–1 scale and why 0.922, 0.899 and 0.898 do not by themselves establish a statistically meaningful ranking or a universally best tool.
- Show a plain-language decision summary alongside the chart. For example, the displayed Paddle pipeline has the highest word overlap, while Nemotron Parse has higher numeric recall and lower median latency than that pipeline, with one recorded failure. These are observed trade-offs, not proof that either meets the business requirements.
- Preserve the caveat that the planned numeric-preservation test for Nemotron Parse was inconclusive. Do not turn its near-matching observed numeric recall versus Qwen into a confirmed equivalence claim.
- Explain why the preferred candidate changes with the objective: searchable prose, financial numbers, structure, speed, hardware constraints or reviewer effort. Where the evidence cannot support a clear choice, say what additional validation would decide it.
- Explain that processing failures can affect high- and low-scoring rows; do not imply that only the lowest bar has failures. Clearly state whether headline quality scores include failed cases or only completed ones.

**Review criterion:** After viewing the chart and summary, the reader can state a reasonable candidate for their task, its trade-off and the next check required. They should not have to reconstruct a recommendation from five bars and several unexplained columns.

## 15. Reconsider the crop-OCR label, ordering and available evidence

**Location supplied:** Prose crop OCR → Both machines → Confirmation v3 · final parsers → All recorded methods. The view is empty. Changing hardware did not resolve it. “Prose crop OCR” is the first task option and unfamiliar to the owner, making the initial exploration feel incomplete.

**Requested change:** Explain and rename the task in plain language, for example “Text-region OCR,” with “Read a cropped image of a paragraph rather than a whole page” and a representative example. Reorder the choices around the audience's main decisions and ensure every offered path has results. The owner asks for a recommendation before removing the task or commissioning new evaluation; neither is automatically authorized by this observation.

**Read-only check during note-taking:** The local `site/data/benchmark.json` already contains seven crop-OCR configuration summaries, all labelled development: five desktop and two laptop. The absence in the screenshot is therefore an unavailable task/split combination in the dashboard data, not evidence that the task was never evaluated. These counts are configurations, not seven independent datasets or seven unique models. This check did not rerun inference or audit the original crop-level outputs.

**Recommended treatment for the later revision:** Retain the existing crop-OCR evidence, clearly labelled exploratory/development. Selecting this task should show its available development results instead of carrying over Confirmation v3. Prefer a populated, decision-relevant table or page comparison as the first/main choice. Do not run more evaluation solely to fill an invalid filter view; consider additional confirmation only if this task is important to the intended workflow and the evidence gap warrants a separately approved experiment.

**Review criterion:** The first offered task is understandable and usable. Selecting text-region OCR reveals its existing evidence with clear limits; the interface cannot imply either that it has final-parser confirmation results or that no evaluation exists.

## 16. Explain table transcription and replace the hardware filter

**Location supplied:** Table transcription → Desktop · 32 GB → Confirmation v3 · final parsers → All recorded methods. The owner also tried Laptop · 12 GB across all tasks and saw empty views.

### Explain the actual task and its practical meaning

**Concern:** “Table transcription” and the caveat-heavy table-structure explanation do not tell a leadership reader what was done or what the output looks like.

**Requested change:** Describe the task plainly: reading a table image and recovering its contents into rows and columns that software can use. Show an appropriate public or clearly illustrative table input and structured output. Verify the recorded format before describing a spreadsheet/export capability as implemented. Explain that table similarity measures resemblance to a reference table, while accurate financial use also needs correct amounts, labels and row/column associations. Introduce what was tested before listing statistical limitations.

The supplied chart orders PaddleOCR-VL direct single pass, Nemotron Parse, Paddle's official pipeline, Qwen3-VL 32B AWQ and olmOCR-2 by the displayed table metric. Explain what that ordering establishes, the numeric/speed/failure trade-offs and which planned comparison was confirmed. Do not imply every pair in the sorted list has a proven significant difference.

### Owner's preferred interaction: remove the hardware filter

**Requested change:** Remove the hardware dropdown from the main results experience. State the actual measured hardware plainly on each applicable result/comparison. When more than one machine has recorded results, show both with clear hardware labels rather than requiring the visitor to discover them through a filter. Preserve differences in models, weights, runtime and datasets; displaying both does not establish a controlled hardware comparison.

The current hardware filter repeatedly produces empty views and gives the impression that the laptop evaluation is absent. Hardware requirements and costs remain essential advisory content; removing the dropdown must not remove that information.

### Check whether data is missing before deciding the rebuild scope

**Owner's question:** Are completed evaluations missing from the website, and should the website be reorganized around the latest final evidence? The owner intends to share this document with another collaborator for a joint recommendation. Keep the document complete and distinguish observations from verified coverage; this does not authorize messaging another service or task.

**Read-only check during this feedback session:** The local `site/data/benchmark.json` contains 30 laptop configuration summaries:

| Task | Available split | Configuration summaries |
| --- | --- | --- |
| Chart questions | Development | 8 |
| Chart to table | Development | 8 |
| Text-region / prose-crop OCR | Development | 2 |
| Whole-page text | Confirmation v2 | 4 |
| Table transcription | Development | 8 |

There are no laptop rows labelled Confirmation v3 in this local dashboard dataset. Retaining that split while switching machines explains an empty view, although the user's full interaction sequence has not been independently replayed. The screenshot alone does not prove that all laptop results are absent. Counts above are configuration summaries, not unique documents or independent model counts.

**Verification required before implementation:** Compare the latest repository branches/results and final source reports against the dashboard's source hashes and imported rows. Identify any missing completed public evaluation, transformation issue, stale deployment or invalid filter state. Do not assert that the local JSON is a complete inventory of every evaluation. Present final decision-relevant comparisons first, with earlier exploratory evidence available separately; retain provenance and avoid combining incomparable sets into one ranking.

**Review criterion:** Readers see the available results and their measured hardware without encountering a hardware-based dead end. The revision recommendation explicitly states whether results were missing or merely hidden by the interface, and which evidence belongs in the primary advisory versus the historical detail.

## 17. Make laptop results discoverable and controls specific to the current view

**New observation:** The owner found the laptop whole-page results under Confirmation v2 after considerable searching. They could easily have missed this completed work. This refines the earlier observation that laptop views appeared empty; it does not mean the laptop was evaluated only on whole-page text or only in Confirmation v2 across every task. See the coverage check in section 16.

**Owner's suggested layout alternative:** Separate desktop and laptop evaluations into clearly identifiable sections or views. This is an alternative/refinement to removing the hardware dropdown, not an instruction to hide either machine's results. Choose a coherent arrangement during the later revision review that makes both sets of evidence visible without creating empty filter paths. Preserve measured hardware labels and do not imply differences are caused by hardware alone.

**Specific required behavior for Laptop / Whole-page text:**

- Only Confirmation v2 has recorded rows in the checked dashboard data for this combination. Use it automatically; do not offer Development, Confirmation v1 or Confirmation v3 as selectable choices.
- If only one split is available, omit the redundant split dropdown. Explain the evaluation set in normal language, with its original identifier available in the technical provenance, rather than requiring a user to choose an internal version name.
- The method dropdown should contain exactly **All recorded methods**, **Baseline**, and **Layout masking**, subject to verification of the latest source data.
- Do not offer Parser single pass, Official pipeline, Self-check, Expert prompt or Upscale for this combination, because the currently displayed dataset has no matching rows for them.
- Derive available choices from the current task and available records. Apply the same rule across the explorer, rather than hard-coding a universal method list or assuming all laptop tasks share this whole-page method set.

**Screenshot context:** The found view contains four configurations: Qwen2.5-VL 7B and Qwen3-VL 8B Instruct, each with baseline and layout masking, 80 pages per row. Failure counts, numeric recall and median latency are shown as unreported. These missing fields remain part of the coverage/provenance audit; a high word score alone cannot establish suitability for number-sensitive work.

**Review criterion:** A first-time visitor can find the laptop evidence without trial and error. Controls only offer choices with meaningful results, and a single available evaluation set does not require an unnecessary selection. The redesigned navigation must demonstrate this exact laptop whole-page path as well as the previously recorded empty paths.

## 18. Resolve the perceived absence of laptop work before judging evaluation coverage

**Owner's concern:** After navigating the site, the owner believes only whole-page text was evaluated on the laptop, questions whether other results were omitted or tasks never run, and asks whether this reflects model capability or an incomplete campaign. This is an important credibility problem in the presentation, not a conclusion to accept without checking records.

**Additional source check during note-taking:** The local generated `site/downloads/MERGED_REPORT.md` explicitly records laptop runs for chart questions, table transcription, chart-to-table recovery and prose crops. The dashboard maps those summaries to Development. Whole-page Confirmation v2 rows come from the corrected routing report. Thus the records checked so far contradict “only whole-page text was evaluated.” They do not yet prove the public dashboard imports every completed evaluation or that every result is exposed correctly in the live UI.

The four laptop whole-page rows are **two models with two methods**, not four models: Qwen2.5-VL 7B and Qwen3-VL 8B Instruct, each baseline and layout masking. Other laptop tasks use additional methods where recorded. Confirm counts, results and coverage from original exports during the full audit before publishing a completeness claim.

**Do not confuse three questions:** whether a task was run, whether its results were imported and discoverable, and whether the model performed well enough for a particular workflow. Missing or hidden rows cannot establish model incapability. These records also do not prove these two models were the only models that could fit the laptop or that untested models would perform better. Explain the campaign's actual selection/scope and hardware constraints without making an exhaustive model-fit claim.

**Latest preferred navigation:** Start by choosing a clearly identified hardware view (desktop or laptop), potentially as two separate interactive explorers. Every subsequent task, evaluation-set and method option must derive only from runs recorded for that hardware. If a task has a single available set, use it directly. Reconcile this with the earlier suggestion to remove the hardware dropdown: the underlying requirement is hardware-first clarity with no empty paths, not preserving a specific dropdown design.

**Review criterion:** Present a verified hardware-by-task coverage inventory before deciding whether new evaluation is necessary. In the revised experience, selecting laptop must make its existing five task categories discoverable without trial and error. Separately identify any missing imports, unrun comparisons and insufficient validation. Do not authorize or start new inference merely because the current website hides results.

## 19. Keep the hardware section, but lead with capability and budget

**Location:** “Fit the workload to the machine,” including the deployment-tier selector and L40S card.

**Positive feedback:** The owner considers this section mostly good. Its hardware and cost guidance is useful; preserve the purpose and practical tier exploration rather than treating the section as a wholesale failure.

**Requested emphasis:**

- Begin with what a setup enables: the tasks, models, practical limits and workflows a reader could pilot. Then explain the hardware and price needed to support that use.
- Put an estimated complete-server/system price range prominently beside each deployment tier, rather than burying it in a bullet. Identify estimate date, source, exclusions and uncertainty. GPU-only pricing is not a full system budget.
- Frame the opening of the website around cost-constrained local document intelligence: “Given this budget and these document needs, what is a reasonable starting setup?” A budget headline must name the setup/scope it covers; do not claim that every evaluated workflow is available under one low price.
- State clearly: this is the equipment available for this evaluation, what was actually tested on it, and the recommendations the evidence supports. Separate measured hardware, proposed deployment hardware, and hypothetical purchasing options.
- Do not imply the tested machines are the best-value equipment currently on the market. Other hardware may offer better price/performance or more usable memory, but that requires a separate, current comparison. The project is not an exhaustive hardware shopping study.
- Date and qualify procurement advice. Do not convert predicted fit into tested concurrent capacity, throughput, ranking stability, security, total operating cost or return on investment. Audit existing statements such as “roughly half the desktop decode speed” and “the model ranking should hold” before carrying them into the revision.

**Review criterion:** A reader sees the budget, what it could enable, what was measured and what remains an estimate. They can use the evaluation as a starting point without mistaking the available test equipment for a current best-buy recommendation.

## 20. Make the GPT-OSS evaluation discoverable

**Owner's question:** GPT-OSS was evaluated, but the owner does not recall seeing those results on the website and suspects an omission. This is another completeness/discoverability concern to investigate in the coverage audit.

**Read-only source check:** The local detailed case study `site/technical.html` already includes GPT-OSS 20B in the “Final legal comparison: useful candidates, no unattended extraction” table under evidence-linked extraction. It reports low/high reasoning configurations on the 60-document public legal comparison, alongside Qwen3 32B and hosted Nemotron. It is not a row in the vision/OCR task explorer. This establishes presence in local website source, not a complete live-deployment audit.

**Requested treatment:** Make the legal/extraction track visible from the model inventory, overview and appropriate navigation, with a direct link to its results and a plain explanation of its distinct task. Explain why GPT-OSS is relevant for text-based clause/field proposals but was not part of these image-reading comparisons. Preserve actual evaluated capabilities and settings; do not invent vision or OCR results for it. Clearly distinguish the final legal comparison from earlier screening results or unrelated sample sizes.

**Review criterion:** Readers can find every evaluated candidate's relevant track, including GPT-OSS, and understand what was and was not tested. An OCR-focused explorer must not create the impression that it represents the entire evaluation campaign if legal results live elsewhere.

## 21. Publish reports as readable web pages with matching PDF downloads

**Location:** “What makes the comparison inspectable?” → “Read the corrected routing report.” This currently opens/downloads Markdown rather than an ordinary report page.

**Expanded requirement:** Apply the PDF requirement to all visitor-facing report/document links currently pointing to Markdown, not only the final advisory. The owner also wants the report content readable directly on the website, without requiring a file download or knowledge of Markdown.

**Requested experience:**

1. A link labelled “Read [report]” opens a dedicated, clearly titled HTML report page within the website.
2. That page presents substantially the same report information as the shareable document: readable headings, explanations, tables, figures, source links and qualifications, with a clear route back to the main site.
3. A prominent **Download PDF** link provides an actual, formatted PDF file that leadership can save, email or hand off. A print-dialog button alone does not satisfy this requirement.
4. Links explicitly labelled “Download [report]” should deliver the PDF directly, rather than silently serving Markdown.

Cover the corrected routing report, final advisory, hardware/budget guide and other public-facing Markdown reports or guides linked from the site. Inventory all such links before revising them; keep source Markdown available in the repository for technical use. Do not interpret this as a request to replace repository documentation, code files, machine-readable JSON or CSV exports with PDFs.

**Consistency and maintenance:** Generate the HTML and PDF from a common approved content source where practical. Preserve report date/version, historical versus current status, source provenance and substantive caveats. A historical report must remain visibly historical rather than silently being represented as the final recommendation. Ensure the PDF and web page agree and link to the relevant current advisory when appropriate.

**Review criterion:** Visitors can read each linked report on an ordinary website page, then download a matching PDF that opens independently. PDFs have readable layouts and tables, page numbers and clickable sources; render and inspect them before delivery. Validate the landing-page links, report navigation, PDF files and mobile reading experience. No leadership-facing “Read report” link should unexpectedly require opening a Markdown file.

## 22. Write every section for a leadership decision first

**Location supplied:** The source-preservation / parsing / evidence-selection / validation steps, followed by “What makes the comparison inspectable?” and the metric, uncertainty, reproduction and limitations panels. This is also an editorial requirement across the entire website and its report pages/PDFs.

**Concern:** The prose reads as technical documentation. Readers must decode terms and implementation details before discovering why the information matters. Leadership needs to digest the findings quickly, understand that the work was rigorous, and leave with the key concepts needed for a decision—not learn every model or experimental detail first.

**Required order for each paragraph, card and expanded explanation:**

1. **What the reader needs to know:** the finding, recommendation or important unresolved question in plain language.
2. **Why it matters to the decision:** the practical implication for reliability, numbers, cost, hardware, review effort, data handling or the next investment.
3. **What supports it:** concise, specific evidence and the material limitation, without turning exploratory evidence into proof.
4. **Optional technical detail:** definitions, settings, statistics and implementation detail after the takeaway, through an appropriate expansion or technical reference.

**Tone:** Simple to understand without being simplistic or patronizing. Treat leadership as capable decision-makers who need context, not as technical specialists or children. Prefer concrete examples and ordinary language. Explain necessary terms when first encountered; remove jargon that contributes nothing to the decision.

**Application to the pictured section:**

- Explain source preservation through its value: reviewers can check a proposed answer against the original page and identify unread material. Technical identifiers and hashing can follow.
- Explain parsing/vision through the input problem and outcome: recover usable information from readable text, scans, tables or charts. Describe the proposed versus implemented workflow accurately.
- Explain evidence selection through auditability: the tool proposes supporting passages that a reviewer can inspect. Retrieval or evidence IDs are implementation detail, not the opening message.
- Explain validation through its practical boundary: mechanically verified source text still requires a check of meaning and relevance. Do not present traceability as proof of semantic correctness.
- Lead methods with the safeguards that make a recommendation defensible, then explain frozen protocols, reference-based scoring, uncertainty and confirmation where useful.
- Lead reproduction with what can reasonably transfer to another setup and what must be retested, rather than unexplained weight digests and group counts.
- Lead limitations with their consequence: what decision can be made now, what cannot yet be approved, and what evidence is needed next. Avoid a dense list of technical negatives with no action attached.

**Review criterion:** Someone scanning only the opening sentence of each section/card should understand the important conclusions and next decisions. The supporting material must still let a technical reviewer inspect the rigor. Clearer language must not imply stronger evidence, hide failures, or remove a caveat necessary to understand the recommendation.

## 23. Explain Vote3, percentage points and task-specific winners

**Location:** “Confirmed chart method / Round 2 — Vote3: gains on 7B and 32B, no reliable gain on 8B,” showing +4.5 pp, +2.6 pp and −0.2 pp.

**Concern:** The owner does not know what “pp” means or whether the larger gain for 7B means the smaller model outperformed 32B. The practical takeaway and model choice remain unclear.

**Requested change:**

- Write **percentage points** instead of an unexplained “pp.” Give a short illustration: moving from 70% to 74.5% is an increase of 4.5 percentage points. Label any illustrative numbers as examples, not measured scores.
- Explain Vote3 plainly using the actual frozen method: obtain three answers using the recorded variants and choose the majority answer under the specified rule. Clarify compute/call cost and ties/no-majority handling from the protocol rather than assuming all three responses always agree or are independent.
- State that the displayed changes compare each model's Vote3 result with its own baseline. A +4.5-point gain versus +2.6 points does not by itself establish that the 7B model has higher final accuracy than the 32B model.
- Show the absolute baseline and final scores, sample and uncertainty needed to answer the owner's cross-model question. Verify paired comparability and avoid treating a within-model improvement test as proof of a cross-model ranking.
- Explain “no reliable gain” as inconclusive evidence of benefit for the tested 8B configuration, rather than proof of identical performance or a universal rule for every 8B model.
- Give a task-specific candidate recommendation with absolute quality, numbers, speed, cost and hardware needs where measured. Acknowledge when there is insufficient evidence to declare a winner.

**Review criterion:** A reader understands both whether the extra method helped a particular model and which tested configuration is a reasonable choice for their task. Smaller models may be useful, but improvement magnitude alone is not evidence that they beat larger models.

## 24. Explain the proposed multi-model pipeline and staged processing strategy

**Owner's proposal:** Use the strongest suitable model or tool for each component of a mixed PDF, instead of expecting one model to do every job. Separate text, chart, table and image tasks, then organize processing in batches so models can be loaded one at a time on constrained hardware. Accumulate the recovered information into a coherent document record across stages.

**Requested presentation:** Add a plain-language architecture proposal showing: receive and identify the document → identify pages/regions and required tasks → route each task to an appropriate tool/model → preserve and combine source-linked outputs → validate and review → export approved information. Explain chart question answering, chart-to-table reconstruction, text reading, table recovery and general image interpretation as distinct capabilities, without assuming every image has a validated route.

**Important clarification:** “No universal model” means no single tested configuration is best across every task, metric and constraint. It does not mean a task-specific best measured candidate can never be identified. Route by evidence and workflow requirements, not by an unsupported claim that every component needs a different model.

**Batching proposal:** Where GPU memory or serving constraints require sequential loading, group pending work by model/task to amortize loading cost. Run and checkpoint a bounded batch, release that model, and continue with another stage. This is a proposed operating strategy, not proof that the hardware can only ever host one model or that every document must wait for an entire corpus stage to finish. Consider bounded batches, scheduling priorities and model-switch costs when implementing it.

**Design requirements to explain in practical terms:**

- Preserve original files; add versioned derived outputs rather than rewriting the source documents.
- Keep document/page/region identities and source coordinates so results can be recombined and inspected without losing context or double-counting overlapping text/tables.
- Preserve cross-page tables and surrounding context where required; segmentation and routing can introduce errors and need evaluation.
- Reuse trustworthy native text and spreadsheet data where available rather than sending every component through a vision model.
- Record model/configuration versions, processing states, unread regions, failures and review decisions. Use checkpoints, deduplication, bounded retries and resumable/idempotent stages so interruptions do not require restarting everything.
- Measure the assembled pipeline end to end. Strong component scores do not establish that segmentation, routing, reconstruction, field extraction or human review work reliably together.

### Initial backfill versus ongoing intake

The owner suggests an initial backlog of potentially hundreds of thousands of files, followed by lighter processing of new or changed documents. Include this distinction as an operating model. Corpus size is a scenario, not a verified project volume.

The suggested one-to-two-week initial pass is a planning hypothesis, not a measured estimate or commitment. Estimate only after measuring representative pages/regions per file, routing frequency, target-server throughput, model loading, failures/retries, usable GPU hours, storage/I/O and review workload. Do not extrapolate whole-corpus time directly from short desktop latency measurements. Ongoing intake is manageable only if sustainable capacity exceeds arrival and change volume at acceptable latency; it is not automatically a light workload.

**Review criterion:** Leadership can understand how task-specific choices could form one useful service, why sequential batching can suit limited hardware, what separates backfill from steady-state operation, and what still needs to be built and measured. Keep this future architecture distinct from the completed model evaluation.

## 25. Explain the legal/extraction track before presenting its scores

**Location:** “Exact source text is a check. Correct meaning is another,” its final legal comparison table, and the “Final methods, results and limitations” link that opens raw `EVALUATION.md`.

**Owner's observation:** GPT-OSS results are now visible, so this particular concern is discoverability and explanation, not established absence. The catchy heading does not clearly say what the experiments were for. The owner wants the purpose described directly: extracting relevant information and evaluating document understanding and reasoning, with supporting evidence.

**Requested explanation:**

- State the actual tasks before presenting the scores: finding contract provisions/answers and deciding whether a document supports, contradicts or does not establish a claim, as defined by the evaluated protocols. Do not imply broad human-like understanding or validated legal advice.
- Expand CUAD (Contract Understanding Atticus Dataset) and ContractNLI (contract natural-language inference); verify official names, provenance, annotation definitions, licences and source links before publication. Explain the public legal document types and why they were useful tests, while noting the limits of transfer to proposals, awards and other business workflows.
- Show a legally reusable public sample or labelled fabricated illustration: document passage and question/claim → recorded model answer/decision and supporting text → reference/validation outcome. Distinguish actual outputs from illustrative ones, original quoting-schema runs from the separate evidence-by-ID design, and text-based understanding from OCR image reading.
- Explain each denominator in full: the relevant score is the number of cases meeting the specified strict correctness/evidence rule out of 30 on that task; truncated responses are counted across the 60 requests. Verify the sampling units against the manifest before describing all requests as independent documents.
- Explain truncation as the response reaching its allowed output-token limit before completion, according to the logged finish reason. It is a generation-limit issue, not necessarily a document being cut off or a separate set of cases. Explain that some model budget can be used by reasoning and that truncation and wrong-answer counts can overlap.
- Make clear that GPT-OSS low/high are reasoning configurations of the same 20B model, not two different models. Likewise distinguish Qwen thinking settings and the hosted Nemotron configuration.

**Report access:** Replace the raw Markdown destination with the dedicated readable web report and actual formatted PDF required in section 21. This is a repeated, explicit owner priority, not an optional enhancement.

**Review criterion:** A reader understands why these legal tests were run, what each model received and produced, what the counts mean, and how the findings relate to a proposed reviewed extraction workflow.

## 26. Visualize legal findings and make the conclusion unmistakable

**Concern:** The legal results are a small table of unexplained counts rather than an accessible visual comparison. The owner cannot readily tell whether Qwen3 32B is the best option, what GPT-OSS contributes, or what should be tried next.

**Requested change:** Give this track clear visual comparisons comparable in readability to the OCR explorer. Show separate task results on shared, labelled scales and show truncations clearly without stacking them as if they were mutually exclusive wrong answers. Use readable contrast, plain model/configuration names, denominators and accessible labels. Do not combine different task metrics into an unexplained overall accuracy or imply significance from bar order.

End the section/page with a visually prominent conclusion covering:

- **Recommended candidate for a stated purpose, and why:** tie it to actual quality, evidence checks, truncations, resource needs and limitations.
- **Other useful candidates:** where a smaller model or another configuration is worth considering, without inventing superiority.
- **What did not meet the need:** explain failure modes and fixed-budget effects, not an irreversible verdict on the model.
- **Next steps that could improve the workflow:** label untested prompt, retrieval, evidence-selection, budget or adaptation changes as hypotheses. Confirm they belong in the next phase; this walkthrough does not reopen the closed model campaign.

The owner wants “who was best and why” visible at a glance. Meet that need with the strongest defensible conclusion, not a forced universal winner. In the recorded final table, Qwen thinking-off has the highest observed ContractNLI count, while CUAD has ties among other configurations and a strong absent-answer baseline. The existing report notes modest scores and no paired cross-model significance conclusion. Verify these before presenting a recommendation. Do not call Qwen an established universal winner or any candidate approved for unattended extraction.

## 27. Include the full evaluation story in Findings and organize resources by audience

**Concern:** The Findings cards omit the legal/evidence-linked work and do not convey the most important concepts or decisions. The page initially looks polished, but closer use exposes confusing navigation, incomplete context and a fragmented account of the results.

**Requested change:** Include OCR, tables, charts and legal/text extraction in a concise top-level findings overview. Explain separate evaluation tracks rather than burying legal work below an OCR-only explorer. The owner is open to a reason for separate detailed presentations: the defensible distinction is different inputs, tasks and scoring. Preserve that distinction while giving all important findings visibility. Do not merge incompatible measures into one numeric ranking merely to fit one table.

For each overview item, show the job, candidate/recommendation, key evidence, limitation and next decision, with a link that opens the relevant detailed evidence. Reformat the results for usable interpretation while retaining the successful visual design and interaction.

**Resource order:**

1. Leadership-readable report pages and their matching PDF downloads: final advisory, hardware/budget guidance, corrected routing report, other appropriate reports.
2. Clearly labelled machine-readable data and provenance downloads, including JSON and CSV where available. These do not need conversion into PDFs.
3. Repository link for code, frozen protocols and tests.

All resource links must resolve to the promised destination. GitHub can remain an external repository link. Audit existing anchors including the implementation-milestones link; ensure they reveal actual relevant information rather than merely repeating the same location.

## 28. Complete budget-tier advice without claiming an unmeasured best buy

**Additional positive feedback:** The hardware section and the top Hardware navigation link work well and should be retained. Move hardware earlier in the story, following Findings.

**Additional requirements:**

- Add sourced, dated complete-system estimates for a comparable GPU laptop and the measured desktop class, not necessarily the owner's exact purchased units. State GPU memory, relevant system memory and assumptions. Do not substitute the small-parser starter-workstation estimate for the RTX 5090 test rig's cost.
- Retain ranges for the proposed L4 and L40S systems; the owner's references to roughly $10,000 and $21,000 are approximate upper ends of existing planning ranges, not verified quotes or market ceilings. Other systems may cost more or less.
- For each tier, make capabilities and best-supported model choices visually easy to scan. Clearly separate measured results on that tier from estimated fit of models on untested targets. Show “not benchmarked on this hardware” where needed instead of inventing target-hardware winners.
- Explain which exact model variants/precisions might fit an L40S and what runtime memory/headroom assumptions remain. Weight fit alone does not establish simultaneous model residency or usable context/concurrency.
- Describe the available hardware as the constraints of this evaluation. The public site should remain general-purpose and must not introduce the owner's employer/team, private client, infrastructure endpoints or stakeholder identity while describing those constraints.

**Owner's value question, not a requested factual conclusion:** The owner questions whether a roughly $21,000 L40S system is worthwhile given the successful smaller candidates. Record this as a cost/value question to investigate, not advice that an L40S is inherently poor value. A defensible answer needs workload, target throughput, memory needs, support/operating requirements and current alternatives. Do not claim cost-effectiveness from quality rankings or unmeasured target-server performance alone.

**Preferred navigation and content order:** Findings → Hardware → Results → Methods → Next steps. Hardware-tier selection should make the useful model/task choices clear; use visual recommendation summaries rather than only long bullet lists. Resolve all filters against available measurements, with the hardware-first exploration preference from sections 17–18.

## Final handoff and first-pass acceptance checklist

The walkthrough is complete for now. Prepare this single document for the owner's second-opinion review; do not start the website rebuild, additional evaluations, external coordination or publishing from this note-taking request.

- Preserve the original technical reference and keep both views internally consistent.
- Audit result coverage, provenance, missing values and live/source consistency before declaring omissions or winners.
- Expose laptop and desktop evidence without dead-end filters; offer only recorded choices and remove redundant single-option selectors.
- Explain task inputs/outputs, metrics, datasets, evaluation stages and practical trade-offs in leadership language.
- Make task-specific recommendations prominent, including the legal/GPT-OSS track, without overstating significance, readiness or model capability.
- Add appropriate public examples and distinguish demonstrations from real recorded outputs.
- Lead hardware advice with capability and dated complete-system budgets; separate test rigs from unbenchmarked targets and current shopping alternatives.
- Explain the proposed task-routing pipeline and separate backfill from ongoing intake, with timing and capacity left as estimates to validate.
- Replace public-facing Markdown report destinations with readable HTML pages and matching actual PDF downloads; visually inspect PDF rendering.
- Make evidence links specific, resource order audience-aware and navigation follow the owner's preferred sequence.
- Check responsive layouts, accessible labels/contrast, direct links, browser navigation and downloads after implementation.
- Retain public-data boundaries, frozen scoring behavior and honest uncertainty. Do not infer security, savings or production approval from benchmark/software checks.

## Editorial rule for the revision

Every prominent number should explain a decision or answer a reader's question. Give its source, unit, meaning and practical limitation in plain language. Use visuals to clarify comparisons, not to decorate the page with unexplained metrics. Keep the underlying evidence and technical methods available without making them the first thing a leadership audience has to navigate.

## Current boundary

This document records feedback only. No website edits, PDF conversion or deployment are part of this note-taking step. Additional walkthrough feedback should be incorporated here before implementation begins.
