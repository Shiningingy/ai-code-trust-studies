"""Render report-draft.md as a readable PDF (report-draft.pdf) through headless Edge.

Usage: python make_pdf.py
"""
import subprocess
from pathlib import Path

import markdown

STUDY = Path(__file__).resolve().parent.parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CSS = """
@page { size: A4; margin: 20mm 18mm 20mm 18mm; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 11pt; line-height: 1.5; color: #1a1a1a; }
h1 { font-size: 19pt; line-height: 1.25; margin: 0 0 6pt; }
h2 { font-size: 14pt; margin: 20pt 0 6pt; border-bottom: 1px solid #ccc; padding-bottom: 2pt; page-break-after: avoid; }
h3 { font-size: 12pt; margin: 14pt 0 4pt; page-break-after: avoid; }
p, li { text-align: justify; hyphens: auto; }
blockquote { margin: 8pt 0; padding: 4pt 10pt; border-left: 3px solid #9ab; background: #f5f7f9; color: #333; font-size: 10pt; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #f2f2f2; padding: 0 2px; }
pre { background: #f6f6f6; border: 1px solid #e2e2e2; padding: 6pt; font-size: 8pt; white-space: pre-wrap; word-wrap: break-word; }
pre code { background: none; }
img { max-width: 100%; display: block; margin: 8pt auto; }
table { border-collapse: collapse; margin: 8pt 0; font-size: 9.5pt; width: 100%; page-break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #eef1f4; }
tr { page-break-inside: avoid; }
"""


def main():
    md = (STUDY / "report-draft.md").read_text(encoding="utf-8")
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    body = body.replace('src="figures/', f'src="{(STUDY / "figures").as_uri()}/')  # the HTML is written to results/
    html = (f"<!doctype html><html><head><meta charset='utf-8'><title>Study 04 report</title>"
            f"<style>{CSS}</style></head><body>{body}</body></html>")
    src = STUDY / "results" / "report-draft.html"
    src.write_text(html, encoding="utf-8")
    out = STUDY / "report-draft.pdf"
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", f"--user-data-dir={Path(__import__('tempfile').gettempdir()) / 'edge-pdf-profile'}", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True, timeout=120)
    print(out, out.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
