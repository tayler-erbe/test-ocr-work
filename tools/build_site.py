"""Build the public website's generated parts from committed sources. No inference.

  python -X utf8 tools/build_site.py          # build data/comparisons.json, report pages and PDFs, then validate
  python -X utf8 tools/build_site.py --check  # validate only

Generates:
  site/data/comparisons.json   named comparisons for the results explorer (every one populated by construction)
  site/reports/*.html          readable report pages, built from the Markdown sources in docs/ and site/downloads/
  site/downloads/*.pdf         matching PDFs (headless Edge or Chrome), with page numbers and clickable links
Validates: every comparison has rows; every local link and anchor in the public pages resolves; no reader-facing
"Read" or "Download" link points at a Markdown file.
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
REPO = "https://github.com/tayler-erbe/test-ocr-work"

DESKTOP = "Desktop · RTX 5090, 32 GB GPU memory"
LAPTOP = "Laptop · RTX 4000 Ada Laptop GPU, 12 GB GPU memory"

MODEL_NAMES = {
    "nemotron-parse [budget8192]": "Nemotron 3.5 Parse (0.63B parser)",
    "paddleocrvl [budget8192]": "PaddleOCR-VL-1.6 (0.9B parser)",
    "paddle-pipeline": "PaddleOCR-VL-1.6 official pipeline",
    "olmocr2 [budget8192]": "olmOCR-2 7B (parser)",
    "27B local artifact*": "27B local build (identity unverified)",
}
METHOD_NAMES = {
    "baseline": "baseline prompt", "expert": "expert prompt", "selfcheck": "self-check", "upscale": "upscaled image",
    "hires": "higher-resolution image", "layoutmask": "layout masking", "table only": "read the table first",
    "tuned": "round-1 tuned prompt", "single-pass": "called directly, one pass", "official-pipeline": "layout plus element pipeline",
    "vote3": "vote3 (majority of three answers)",
}

STAGES = {
    "development": ("Development", "Examples used to explore methods and choose what to test next. Exploratory: a good result here is a lead, not a confirmed finding."),
    "confirmation v1": ("Held-out check, round 1", "Examples kept aside during round 1 and scored once, to check the round-1 choices."),
    "confirmation v2": ("Pre-registered check, round 2", "Examples no earlier run had used. The method to confirm and the decision rule were written down before scoring."),
    "confirmation v3": ("Pre-registered confirmation, round 3", "Fresh examples, the same 8,192-token output limit for every model, and a pass rule written down before scoring."),
}

METRICS = {
    "table": ("Table similarity (TEDS, 0 to 1)", "How closely the recovered table's rows, columns and cell text match the reference table. 1 means identical. It is a similarity score, not the share of tables that were fully correct.", False),
    "page_text": ("Word overlap (word F1, 0 to 1)", "A balance between recovering the reference words and not adding extra ones. It is not overall accuracy, and it does not check that every number is right.", False),
    "chart_qa": ("Questions answered correctly", "Share of chart questions answered to match the reference, allowing 5% tolerance on numbers.", False),
    "chart_table": ("Chart values recovered (value recall, 0 to 1)", "Share of the chart's reference values recovered within 5% when the model rebuilds the chart's data table.", False),
    "ocr_crop": ("Character error rate", "Share of characters that would need to change to match the reference text. Lower is better.", True),
}

TASK_ITEMS = {"table": "tables", "page_text": "pages", "chart_qa": "questions", "chart_table": "charts", "ocr_crop": "text regions"}

# Round-2 chart confirmation (1,322 ChartQA validation questions on 722 charts). Not in benchmark.json; values are the
# baseline and method accuracies in site/downloads/MERGED_REPORT.md (chart_qa_confirm2 rows). Failures and timings for
# vote3 do not exist: vote3 is computed from stored answers without new calls.
ROUND2_CHARTS = [
    ("Qwen2.5-VL 7B", "laptop", "baseline", 0.5575), ("Qwen2.5-VL 7B", "laptop", "vote3", 0.6029),
    ("Qwen2.5-VL 7B", "laptop", "selfcheck", 0.7352), ("Qwen2.5-VL 7B", "laptop", "upscale", 0.5197),
    ("Qwen3-VL 8B Instruct", "laptop", "baseline", 0.7496), ("Qwen3-VL 8B Instruct", "laptop", "vote3", 0.7481),
    ("Qwen3-VL 8B Instruct", "laptop", "selfcheck", 0.3230), ("Qwen3-VL 8B Instruct", "laptop", "upscale", 0.7648),
    ("Qwen3-VL 32B AWQ", "desktop", "baseline", 0.8200), ("Qwen3-VL 32B AWQ", "desktop", "vote3", 0.8457),
    ("Qwen3-VL 32B AWQ", "desktop", "selfcheck", 0.8449), ("Qwen3-VL 32B AWQ", "desktop", "upscale", 0.8351),
]

LEGAL_FINAL = [  # results/legal/round3/*/summary.json and the hosted reassessment, same 60 public documents
    ("Qwen3 32B, thinking off", 14, 18, 0), ("Qwen3 32B, thinking on", 15, 16, 0),
    ("gpt-oss-20b, low reasoning", 15, 14, 0), ("gpt-oss-20b, high reasoning", 11, 4, 19),
    ("Nemotron 3 Nano 30B (hosted API), reasoning on", 13, 12, 2),
]

LAYOUT = [("DocLayout-YOLO (layout detector)", 0.8761), ("Nemotron 3.5 Parse (0.63B parser)", 0.6115)]  # stats.json layout row


def row_name(r):
    return MODEL_NAMES.get(r["model"], r["model"])


def from_benchmark(rows, task, split, side, keep=None):
    out = []
    for r in rows:
        if r["task"] == task and r["split"] == split and r["side"] == side and (keep is None or r["variant"] in keep):
            out.append({"model": row_name(r), "method": METHOD_NAMES.get(r["variant"], r["variant"]), "key": f'{r["model"]}|{r["variant"]}',
                        "score": r["score"], "cases": r["cases"], "failed": r.get("failed"), "seconds": r.get("median_seconds"),
                        "numbers": r.get("numeric_recall"), "source": r.get("source")})
    return out


def comparisons():
    bench = json.loads((SITE / "data" / "benchmark.json").read_text(encoding="utf-8"))
    rows = bench["rows"]
    C = []

    def add(cid, track, title, task, split, side, question, meaning, limits, recommend=None, rows_=None, confirmatory=False, sources=None, metric=None, items=None):
        rws = rows_ if rows_ is not None else from_benchmark(rows, task, split, side)
        stage = STAGES.get(split, (split, ""))
        m = metric or METRICS[task]
        C.append({"id": cid, "track": track, "title": title, "hardware": {"desktop": DESKTOP, "laptop": LAPTOP}.get(side, side),
                  "side": side, "task": task, "stage": stage[0], "stage_note": stage[1], "confirmatory": confirmatory,
                  "question": question, "metric": m[0], "metric_note": m[1], "lower_is_better": m[2],
                  "items": items or TASK_ITEMS.get(task, "cases"), "meaning": meaning, "limits": limits, "recommend": recommend,
                  "sources": sources or [], "rows": rws})

    src_r3 = [{"label": "Paired statistics", "url": "downloads/stats.json"}, {"label": "Final advisory", "url": "reports/final-advisory.html"}]
    src_r2 = [{"label": "Routing report", "url": "reports/routing-report.html"}, {"label": "Round-2 export audit", "url": "data/round2-audit.json"}]
    src_r1 = [{"label": "Merged results", "url": "reports/merged-results.html"}]

    # Tables
    add("tables-final", "Tables", "Final table test: 100 financial-report tables", "table", "confirmation v3", "desktop",
        "Does a small specialised table reader beat the strongest earlier model on tables it has never seen?",
        "PaddleOCR-VL-1.6 passed the planned test: higher table similarity than Qwen3-VL 32B (0.852 against 0.762) and it kept the numbers (97.4% against 93.2%). It is the table model to pilot first.",
        "Public financial-report tables (FinTabNet.c), not your documents. 97.4% numeric recall is below a 99% bar, so amounts still need review. The table score measures structure similarity, not correct field assignment.",
        recommend="paddleocrvl [budget8192]|single-pass", confirmatory=True, sources=src_r3)
    add("tables-heldout-r1", "Tables", "Round-1 held-out check: 159 tables", "table", "confirmation v1", "desktop",
        "Did round 1's tuned table method hold up on tables kept aside?",
        "The tuned prompt did not beat the baseline on the held-out tables (0.841 against 0.851). Round 1 therefore kept the baseline table prompt.",
        "Earlier tables from the same public source as development. Superseded for table choice by the final table test.", sources=src_r1)
    add("tables-dev-desktop", "Tables", "Table development: 60 tables, desktop models", "table", "development", "desktop",
        "Which vision model and prompt read tables best during exploration?",
        "Scores sat close together (about 0.72 to 0.87). Prompt variants made small differences. Model size mattered less than expected: the 8B model scored 0.819, the 32B 0.821.",
        "Exploratory. Close scores here are not reliable differences.", sources=src_r1)
    add("tables-dev-laptop", "Tables", "Table development: 60 tables, laptop models", "table", "development", "laptop",
        "How well do the small models that fit a 12 GB laptop GPU read tables?",
        "Qwen3-VL 8B scored 0.818 at baseline, about the same as the desktop 32B. Small models are viable for tables on modest hardware.",
        "Exploratory. The laptop 8B weights differ from the desktop 8B, so this is not a same-weight reproduction.", sources=src_r1)

    # Pages
    add("pages-final", "Page text", "Final page test: 80 fresh pages", "page_text", "confirmation v3", "desktop",
        "Do small document parsers read whole pages better than the 32B vision model, without losing numbers?",
        "Nemotron 3.5 Parse recovered more of the reference words than the 32B (0.899 against 0.820) and recovered the same share of numbers on average (88.2% against 88.3%). The planned numbers test was inconclusive, so use it with a numbers check. The PaddleOCR pipeline had the highest word score but lost the most numbers after olmOCR-2.",
        "80 public pages. A higher word score does not mean the numbers are right. The official PaddleOCR pipeline adds a layout step before reading; the other rows call each model directly.",
        recommend="nemotron-parse [budget8192]|single-pass", confirmatory=True, sources=src_r3)
    add("pages-masking-desktop", "Page text", "Layout masking check: 80 pages, desktop", "page_text", "confirmation v2", "desktop",
        "Does blanking out figures and tables before reading a page help?",
        "Masking raised word overlap (0.881 against 0.814) but dropped recovered numbers from 87.2% to 69.4%. For documents with amounts, keep the baseline.",
        "Same 32B model, two ways of preparing the page. Masking removes tables, which is where many numbers are.", recommend="Qwen3-VL 32B AWQ|baseline", sources=src_r2)
    add("pages-masking-laptop", "Page text", "Layout masking check: 80 pages, laptop", "page_text", "confirmation v2", "laptop",
        "Does masking help the small laptop models read pages?",
        "Same trade-off as on the desktop: masking raised word overlap and lowered recovered numbers for both small models. The 8B baseline kept the most numbers (82.5%).",
        "Two models, each with two preparations. Not a hardware comparison.", recommend="Qwen3-VL 8B Instruct|baseline", sources=src_r2)
    add("pages-dev-desktop", "Page text", "Page development: 40 pages, desktop", "page_text", "development", "desktop",
        "Is layout masking worth testing on fresh pages?",
        "On development pages masking raised word overlap (0.895 against 0.809) and dropped numbers (72.0% against 90.9%). That led to the round-2 check.",
        "Exploratory, 40 pages.", sources=src_r1)

    # Charts
    r2 = [{"model": m, "method": METHOD_NAMES[v], "key": f"{m}|{v}", "score": s, "cases": 1322, "failed": None, "seconds": None, "numbers": None,
           "source": "merged-report", "machine": side} for m, side, v, s in ROUND2_CHARTS]
    add("charts-r2", "Charts", "Round-2 chart check: 1,322 questions on 722 charts", "chart_qa", "confirmation v2", "mixed",
        "Do vote3 and self-check really help on charts no model had seen?",
        "Vote3 helped the 7B model (55.8% to 60.3%) and the 32B (82.0% to 84.6%) but not the 8B. Self-check lifted the 7B to 73.5% but cut the 8B to 32.3%. The best result overall is still the 32B (84.6%). A larger gain for 7B does not mean 7B beats 32B.",
        "Questions about the same chart are related, so the effective sample is smaller than 1,322. Vote3 needs three answers per question. Small models ran on the laptop and the 32B on the desktop.",
        recommend="Qwen3-VL 32B AWQ|vote3", rows_=r2, sources=src_r2)
    C[-1]["hardware"] = "7B and 8B on the laptop (12 GB); 32B on the desktop (32 GB)"
    add("charts-dev-laptop", "Charts", "Chart questions development: 200 questions, laptop", "chart_qa", "development", "laptop",
        "Which small model and method answer chart questions best on a 12 GB GPU?",
        "Qwen3-VL 8B at baseline (79.5%) or with upscaled images (80.0%). Self-check works for 7B (79.0%) and badly hurts 8B (36.0%).",
        "Exploratory, 200 questions.", recommend="Qwen3-VL 8B Instruct|baseline", sources=src_r1)
    add("charts-dev-desktop", "Charts", "Chart questions development: 200 questions, desktop", "chart_qa", "development", "desktop",
        "Which model and method answer chart questions best with more GPU memory?",
        "Qwen3-VL 32B with self-check scored highest (91.0%). The same method hurt the 8B and the 27B build.",
        "Exploratory, 200 questions.", recommend="Qwen3-VL 32B AWQ|selfcheck", sources=src_r1)
    add("charts-heldout-r1", "Charts", "Round-1 held-out check: 2,022 questions", "chart_qa", "confirmation v1", "desktop",
        "Did round 1's tuned chart method hold on unseen questions?",
        "The tuned method was slightly higher than baseline for the 32B (88.3% against 86.4%).",
        "Superseded by the larger, pre-registered round-2 check.", sources=src_r1)
    add("charttable-dev-laptop", "Charts", "Chart to table: 60 charts, laptop", "chart_table", "development", "laptop",
        "Can a small model rebuild the data table behind a chart?",
        "Qwen3-VL 8B with self-check recovered 93.0% of values, up from 41.8% at baseline.",
        "Exploratory, 60 charts. Needs a larger held-out check before it is trusted.", recommend="Qwen3-VL 8B Instruct|selfcheck", sources=src_r1)
    add("charttable-dev-desktop", "Charts", "Chart to table: 60 charts, desktop", "chart_table", "development", "desktop",
        "Can the larger models rebuild chart data more reliably?",
        "The 8B model again led with self-check (0.930) and the expert prompt (0.915), ahead of the 32B (about 0.90). Bigger was not better here.",
        "Exploratory, 60 charts.", sources=src_r1)

    # Text regions
    add("crops-dev-laptop", "Text regions", "Text-region OCR: 50 cropped paragraphs, laptop", "ocr_crop", "development", "laptop",
        "How accurately do small models read a cropped block of text?",
        "Qwen3-VL 8B made 1.2% character errors, the same as the 32B models on the desktop.",
        "Exploratory. These are cropped paragraphs, not whole mixed pages. Every model recovered about 96.5% of the numbers.", recommend="Qwen3-VL 8B Instruct|baseline", sources=src_r1)
    add("crops-dev-desktop", "Text regions", "Text-region OCR: 50 cropped paragraphs, desktop", "ocr_crop", "development", "desktop",
        "Does a bigger model read cropped text better?",
        "No meaningful difference: 1.1% to 1.8% character error across models.", "Exploratory, 50 crops.", sources=src_r1)

    # Layout
    lay = [{"model": m, "method": "detect tables and figures", "key": m, "score": s, "cases": 120, "failed": None, "seconds": None, "numbers": None, "source": "round3-stats"} for m, s in LAYOUT]
    add("layout", "Layout", "Finding figures on a page: 120 pages", "layout", "development", "desktop",
        "Can a page parser also find the figures on a page, or is a dedicated detector still needed?",
        "The dedicated detector found figures far more reliably (0.876 against 0.612). Keep it for layout.",
        "Figure detection only. For tables the two were not clearly different.", recommend="DocLayout-YOLO (layout detector)", rows_=lay,
        metric=("Figures found (figure F1, 0 to 1)", "A balance between finding every reference figure and not marking things that are not figures.", False), items="pages", sources=src_r3)

    # Legal
    leg = [{"model": m, "method": "", "key": m, "score": cuad / 30, "nli": nli / 30, "cuad": cuad, "nli_n": nli, "truncated": t, "cases": 30} for m, cuad, nli, t in LEGAL_FINAL]
    C.append({"id": "legal-final", "track": "Contracts", "title": "Contract questions: the same 60 public documents", "hardware": "Desktop for local models; hosted API for Nemotron",
              "side": "desktop", "task": "legal", "stage": "Final comparison", "stage_note": "The same 60 documents and requests for every configuration, with a 16,000-token output limit.",
              "confirmatory": False, "question": "Which local language model best answers contract questions with supporting evidence?",
              "metric": "Correct out of 30, per task", "metric_note": "Strict correctness: the answer and its evidence must pass the frozen checks. Failed or cut-off answers count as wrong.",
              "lower_is_better": False, "items": "questions",
              "meaning": "On ContractNLI, Qwen3 32B with thinking off did best (18 of 30). On CUAD no configuration beat simply answering 'absent' every time (15 of 30), so CUAD does not separate these models. gpt-oss-20b at low reasoning is a smaller alternative that fits a 24 GB GPU.",
              "limits": "30 questions per task, so a difference of a few is noise. These rank configurations on public contracts, not legal accuracy on your documents. Human review is required.",
              "recommend": "Qwen3 32B, thinking off", "sources": [{"label": "Final advisory", "url": "reports/final-advisory.html"}, {"label": "Nemotron reassessment", "url": "reports/nemotron-reassessment.html"}], "rows": leg})
    return C


# ---------- reports ----------
REPORTS = [  # (slug, title, source markdown, status note)
    ("final-advisory", "Final advisory: methods, results and limits", ROOT / "docs" / "EVALUATION.md", "Current. Final advisory, 27 October 2026."),
    ("hardware-and-budget", "Hardware and budget guide", ROOT / "docs" / "hardware-and-budget.md", "Current. Dated planning estimates, not quotes."),
    ("routing-report", "Routing report, rounds 1 and 2", SITE / "downloads" / "ROUTING_REPORT_2026-10-21.md", "Historical (21 October 2026). Superseded for tables and page text by the final advisory."),
    ("nemotron-reassessment", "Hosted Nemotron reassessment", ROOT / "docs" / "nemotron-reassessment.md", "Supporting report for the legal track."),
    ("roadmap", "Implementation roadmap", ROOT / "docs" / "roadmap.md", "Current. The next phase after the evaluation."),
    ("merged-results", "Merged results, rounds 1 and 2", SITE / "downloads" / "MERGED_REPORT.md", "Historical generated tables (21 October 2026)."),
    ("data-audit", "Website data audit", ROOT / "docs" / "website-data-audit.md", "Provenance of restored round-2 values, 29 October 2026."),
]


def md_to_html(md, slug_links, src_dir=ROOT):
    def inline(t):
        t = html.escape(t, quote=False)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)

        def link(m):
            text, url = m.group(1), html.unescape(m.group(2))
            if url.split("#")[0] in slug_links:
                url = slug_links[url.split("#")[0]]
            elif not re.match(r"https?://|#|mailto:", url):
                target = (src_dir / url.split("#")[0]).resolve()
                try:
                    rel = target.relative_to(ROOT).as_posix()
                except ValueError:
                    rel = url
                if rel.startswith("site/"):
                    url = "../" + rel[len("site/"):]
                else:
                    url = f"{REPO}/{'tree' if url.endswith('/') else 'blob'}/main/{rel}"
            return f'<a href="{html.escape(url)}">{text}</a>'
        return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, t)

    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s:|-]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], rows[1:]
            out.append('<div class="table-scroll"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>" +
                       "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table></div>")
            continue
        if l.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre>" + html.escape("\n".join(lines[i + 1:j])) + "</pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,4}) (.*)", l)
        if m:
            lvl = min(len(m.group(1)) + 1, 4)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
        elif re.match(r"^\s*[-*] ", l):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*] ", lines[i]):
                items.append(re.sub(r"^\s*[-*] ", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        elif re.match(r"^\d+\. ", l):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        elif l.strip():
            para = [l]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|\||```|\s*[-*] |\d+\. )", lines[i + 1]):
                i += 1
                para.append(lines[i])
            out.append(f"<p>{inline(' '.join(para))}</p>")
        i += 1
    return "\n".join(out)


def report_page(slug, title, body, status, pdf=True):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#142b36">
<title>{html.escape(title)} · Document Intelligence Lab</title><link rel="icon" href="../favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="../site.css"></head>
<body><a href="#main" class="skip">Skip to content</a>
<header class="site-header"><a href="../index.html" class="brand" aria-label="Document Intelligence Lab home"><span class="brand-mark">DI<span>↗</span></span><span>Document<br><strong>Intelligence Lab</strong></span></a>
<nav aria-label="Main navigation"><a href="../index.html">Decision brief</a><a href="../technical.html">Evidence</a><a href="../technical.html#explorer">Results explorer</a><a href="../index.html#resources">Reports</a></nav>
<a class="repo-link" href="{REPO}">Repository <span aria-hidden="true">↗</span></a></header>
<main id="main" class="report-wrap">
<p class="eyebrow">REPORT</p><h1>{html.escape(title)}</h1>
<p class="report-status">{html.escape(status)}</p>
<p class="report-actions">{f'<a class="button primary" href="../downloads/{slug}.pdf" download>Download PDF <span aria-hidden="true">↓</span></a>' if pdf else ''}<a class="text-link" href="../index.html">Back to the decision brief</a></p>
{body}
</main>
<footer class="wrap"><div><strong>Document Intelligence Lab</strong><p>Tayler Erbe · Public benchmarks only. No private documents, labels or model responses.</p></div><a href="{REPO}">Source and frozen protocols ↗</a></footer>
</body></html>
"""


def browser():
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              shutil.which("chromium") or "", shutil.which("google-chrome") or ""):
        if p and Path(p).exists():
            return p
    return None


def build_reports():
    slug_links = {}
    for slug, _, src, _ in REPORTS:
        slug_links[src.name] = f"{slug}.html"
        slug_links[f"downloads/{src.name}"] = f"{slug}.html"
    slug_links.update({"EVALUATION.md": "final-advisory.html", "hardware-and-budget.md": "hardware-and-budget.html", "roadmap.md": "roadmap.html",
                       "nemotron-reassessment.md": "nemotron-reassessment.html"})
    (SITE / "reports").mkdir(exist_ok=True)
    exe = browser()
    for slug, title, src, status in REPORTS:
        md = src.read_text(encoding="utf-8")
        md = re.sub(r"\A# .*\n", "", md)  # the page supplies its own title
        page = report_page(slug, title, md_to_html(md, slug_links, src.parent), status)
        out = SITE / "reports" / f"{slug}.html"
        out.write_text(page, encoding="utf-8")
        if exe:
            pdf = SITE / "downloads" / f"{slug}.pdf"
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", out.resolve().as_uri()],
                           check=True, capture_output=True, timeout=120)
    # the decision brief as a PDF
    if exe:
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=4000",
                        f"--print-to-pdf={SITE / 'downloads' / 'decision-brief.pdf'}", (SITE / "index.html").resolve().as_uri()],
                       check=True, capture_output=True, timeout=120)
    return exe is not None


# ---------- validation ----------
PUBLIC_PAGES = ["index.html", "technical.html"]


def validate():
    errors = []
    comps = json.loads((SITE / "data" / "comparisons.json").read_text(encoding="utf-8"))["comparisons"]
    ids = set()
    for c in comps:
        if not c["rows"]:
            errors.append(f"comparison {c['id']} has no rows")
        if c["id"] in ids:
            errors.append(f"duplicate comparison id {c['id']}")
        ids.add(c["id"])
        if c.get("recommend") and not any(r["key"] == c["recommend"] for r in c["rows"]):
            errors.append(f"comparison {c['id']} recommends a row it does not show: {c['recommend']}")
    pages = PUBLIC_PAGES + [f"reports/{s}.html" for s, *_ in REPORTS]
    for page in pages:
        p = SITE / page
        if not p.exists():
            errors.append(f"missing page {page}")
            continue
        text = p.read_text(encoding="utf-8")
        anchors = set(re.findall(r'id="([^"]+)"', text))
        for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', text, re.S):
            href, label = html.unescape(m.group(1)), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if href.startswith("#"):
                frag = href[1:]
                if frag and not frag.startswith("cmp=") and frag not in anchors:
                    errors.append(f"{page}: anchor #{frag} not found")
                if frag.startswith("cmp=") and frag[4:] not in ids:
                    errors.append(f"{page}: comparison {frag[4:]} not found")
                continue
            path, _, frag = href.partition("#")
            target = (p.parent / path).resolve()
            if not target.exists():
                errors.append(f"{page}: link target {href} missing")
            if frag.startswith("cmp=") and frag[4:] not in ids:
                errors.append(f"{page}: comparison {frag[4:]} not found")
            if path.endswith(".md") and re.match(r"(?i)(read|download|open)", label):
                errors.append(f"{page}: reader link '{label}' points at Markdown {href}")
    if errors:
        raise SystemExit("SITE CHECK FAILED\n" + "\n".join(errors))
    print(f"PASS site: {len(comps)} populated comparisons, {len(pages)} pages, links and anchors resolve")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not a.check:
        comps = comparisons()
        (SITE / "data" / "comparisons.json").write_text(json.dumps({"generated_from": ["data/benchmark.json", "downloads/MERGED_REPORT.md", "downloads/stats.json", "results/legal/round3"],
                                                                   "comparisons": comps}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        made_pdfs = build_reports()
        print(f"built {len(comps)} comparisons, {len(REPORTS)} report pages" + (", PDFs" if made_pdfs else ", no browser for PDFs"))
    validate()


if __name__ == "__main__":
    sys.exit(main())
