# Vision evaluation, round 2: improvement plan (pre-registered 20 Oct 2026, before any v2 data was frozen or run)

Production model: Qwen3-VL-32B-Instruct AWQ on vLLM (`openai:qwen3vl32b`). Every reading, extraction and judgement is
done by local models and plain-code scorers; no the desktop operator model sees any image or document.

## Where round 1 lost points (from stored scores, not from looking at images)

| task | round-1 result (32B) | where the loss is |
|---|---|---|
| chart_qa (held out, 2,022 Q) | 86.4% baseline, 88.3% with self-check | human-written questions 77.9% vs augmented 94.5%: the loss is reasoning/arithmetic over read values, not reading |
| page_text (40 pages) | word F1 0.809 | precision 0.765 vs recall 0.919: the model transcribes text the answer key excludes (tables, figures, display equations, page furniture); worst on academic papers (0.75) and books (0.71) |
| table (held out, 159) | TEDS 0.851; expert prompt did not hold up on held-out | structure 0.907, cell F1 0.766; no untouched OmniDocBench tables remain for a fresh test |
| layout | VLM F1 0.61/0.71 vs DocLayout-YOLO 0.85/0.81 | already solved by routing layout to YOLO (production default) |
| ocr_crop | CER 1.2% | at the answer-key ceiling: numeric recall is identical (0.965) for all five models, so the remaining misses are key artefacts |

## Candidate improvements, ranked (expected gain / cost)

1. **Layout-guided page text ("layoutmask")**: DocLayout-YOLO finds tables, figures, display equations and page furniture;
   those areas are painted white before the same model reads the page with the same prompt. One factor changes (the input
   image). Expected: large precision gain on papers and books, recall unchanged. Cost: +0.3 s per page on CPU.
2. **Variant vote ("vote3")** for chart questions: majority of the baseline, self-check and upscale answers (answers that
   agree within the 5% relaxed rule count as one); a tie goes to the self-check answer. Expected: +1 to +2 points.
   Cost: 3 calls per question (about 3 s).
3. **Read-then-answer ("readfirst")** for chart questions: the model first extracts the chart's data table, then answers
   from the image plus its own table, writing notes before the answer. Targets the human-question arithmetic gap.
   Expected: +1 to +3 points on human questions. Cost: about 5 s per question.
4. LoRA fine-tune of Qwen3-VL-8B on ChartQA train (disjoint from every evaluation chart). Most valuable for the 12 GB work
   laptop, where only an 8B model fits; needs the GPU exclusively for several hours (8001 down). Not run this round.
5. Table improvements: no untouched table data is left in OmniDocBench, so any table change could only be tested on data
   already used. Needs a new table benchmark (e.g. PubTabNet val) first. Not run this round.

## Data (frozen before any run; `vision_cases_v2.json`, sha256 recorded in the manifest)

- **chart_qa_dev2**: ChartQA **val** split (never used in round 1), charts whose hash puts them in the development third.
  All questions on those charts.
- **chart_qa_confirm2**: the other two thirds of ChartQA val charts. Disjoint charts from dev2, from v1 and from confirm v1
  (which were ChartQA test).
- **page_text dev**: the 40 v1 pages (round 1 never tuned page_text, so they are still a fair development set).
- **page_text_confirm2**: 80 English OmniDocBench pages that appear in no earlier case of any task.

## Decision rules (fixed now)

- Chart questions: the variant (selfcheck, vote3 or readfirst) with the highest accuracy on chart_qa_dev2 is the one
  confirmed, against baseline, on chart_qa_confirm2. Exact McNemar test.
- Page text: layoutmask is confirmed against baseline on page_text_confirm2 if it does not lower word F1 on the dev pages.
  Paired bootstrap on word F1.
- Confirmatory family = these two tests only; Holm correction over the two. Significance level 0.05. No threshold, metric
  or case is changed after results are seen. Negative results are reported.
- Concurrency: requests are sent four at a time to vLLM (continuous batching). Baseline and variant runs use the same
  setting, so the comparison is fair; tiny batching-order differences at temperature 0 are noted, not hidden.
