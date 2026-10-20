"""Render a Markdown document (headings, paragraphs, lists, tables, code blocks) to PDF with headless Edge.

  python tools/render_handoff_pdf.py docs/handoff/CODEX_HANDOFF.md [--copy-to DIR]
"""
import argparse
import html
import re
import shutil
import subprocess
from pathlib import Path

EDGE = [Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"), Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe")]


def inline(text):
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append(f"<code>{html.escape(p[1:-1])}</code>")
            continue
        e = html.escape(p)
        e = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e)
        e = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", e)
        e = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', e)
        out.append(e)
    return "".join(out)


def md_to_html(text):
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre>" + html.escape("\n".join(lines[i + 1:j])) + "</pre>")
            i = j + 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s:|-]+\|?$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr>" +
                       "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:]) + "</table>")
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.) (.*)", line)
        if m:
            tag = "ol" if m.group(2)[0].isdigit() else "ul"
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.) ", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.) ", "", lines[i]))
                i += 1
                while i < len(lines) and lines[i].startswith("   ") and lines[i].strip():
                    items[-1] += " " + lines[i].strip()
                    i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        m = re.match(r"^(#{1,4}) (.*)", line)
        if m:
            out.append(f"<h{len(m.group(1))}>{inline(m.group(2))}</h{len(m.group(1))}>")
        elif line.strip():
            para = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|\||```|\s*([-*]|\d+\.) )", lines[i + 1]):
                i += 1
                para.append(lines[i])
            out.append(f"<p>{inline(' '.join(para))}</p>")
        i += 1
    return "\n".join(out)


CSS = """body{font-family:'Segoe UI',Arial,sans-serif;max-width:900px;margin:28px auto;color:#1d2330;line-height:1.45;font-size:12.5px}
h1{font-size:22px;border-bottom:2px solid #2f5d8a;padding-bottom:4px}h2{font-size:16px;color:#2f5d8a;margin-top:22px;page-break-after:avoid}
h3{font-size:13.5px;margin-top:14px}table{border-collapse:collapse;width:100%;font-size:11px;margin:8px 0;page-break-inside:auto}
th,td{border:1px solid #c9d1dc;padding:3px 6px;vertical-align:top;text-align:left}th{background:#e8eef5}tr{page-break-inside:avoid}
code{font-family:Consolas,monospace;font-size:11px;background:#f1f3f6;padding:0 3px;border-radius:3px;word-break:break-all}
pre{font-family:Consolas,monospace;font-size:10.5px;background:#f6f7f9;border:1px solid #dde2e8;padding:8px;white-space:pre-wrap;word-break:break-all}"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("markdown", type=Path)
    ap.add_argument("--copy-to", type=Path)
    a = ap.parse_args()
    src = a.markdown.resolve()
    title = next((l[2:] for l in src.read_text(encoding="utf-8").splitlines() if l.startswith("# ")), src.stem)
    page = f"<!doctype html><meta charset='utf-8'><title>{html.escape(title)}</title><style>{CSS}</style>{md_to_html(src.read_text(encoding='utf-8'))}"
    html_path = src.with_suffix(".html")
    html_path.write_text(page, encoding="utf-8")
    pdf = src.with_suffix(".pdf")
    edge = next(e for e in EDGE if e.exists())
    subprocess.run([str(edge), "--headless", "--disable-gpu", f"--print-to-pdf={pdf}", "--no-pdf-header-footer", html_path.as_uri()], check=True, timeout=180)
    html_path.unlink()
    if a.copy_to:
        shutil.copy2(pdf, a.copy_to / pdf.name)
    print(pdf)


if __name__ == "__main__":
    main()
