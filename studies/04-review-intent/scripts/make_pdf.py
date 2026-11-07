"""Render report-draft.md as a readable PDF (report-draft.pdf) through headless Edge.

Usage: python make_pdf.py
"""
import os
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
table { border-collapse: collapse; margin: 8pt 0; font-size: 9.5pt; width: 100%; }
thead { display: table-header-group; }
th, td { border: 1px solid #bbb; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #eef1f4; }
tr { page-break-inside: avoid; }
h2.appendix { break-before: page; page-break-before: always; }
.keep { break-inside: avoid; page-break-inside: avoid; }
"""


def keep_together(body):
    """Wrap each figure (image paragraph + its caption) and each table (+ a caption right after it) so that the pair is
    never split across pages; start every appendix on a new page."""
    import re
    body = body.replace("<h2>Appendix", '<h2 class="appendix">Appendix')
    cap = r"(?:\s*<p><em>[^<]*(?:<[^>]+>[^<]*)*?</em></p>)?"
    body = re.sub(r"(<p><img [^>]*/?></p>" + cap + ")", r'<div class="keep">\1</div>', body)
    def wrap_short(m):  # short tables stay whole; long ones may break between rows (the header row repeats)
        return f'<div class="keep">{m.group(1)}</div>' if m.group(1).count("<tr>") <= 9 else m.group(1)

    body = re.sub(r"(<table>.*?</table>" + cap + ")", wrap_short, body, flags=re.S)
    return body


def main():
    md = (STUDY / "report-draft.md").read_text(encoding="utf-8")
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    body = body.replace('src="figures/', f'src="{(STUDY / "figures").as_uri()}/')  # the HTML is written to results/
    body = keep_together(body)
    html = (f"<!doctype html><html><head><meta charset='utf-8'><title>Study 04 report</title>"
            f"<style>{CSS}</style></head><body>{body}</body></html>")
    src = STUDY / "results" / "report-draft.html"
    src.write_text(html, encoding="utf-8")
    out = STUDY / "report-draft.pdf"
    tmp = STUDY / "results" / "report-draft.tmp.pdf"
    tmp.unlink(missing_ok=True)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", f"--user-data-dir={__import__('tempfile').mkdtemp(prefix='edge-pdf-')}", "--no-pdf-header-footer",
                    f"--print-to-pdf={tmp}", src.as_uri()], check=True, capture_output=True, timeout=120)
    for _ in range(40):  # Edge can return before the file is written
        if tmp.exists() and tmp.stat().st_size > 0:
            break
        __import__('time').sleep(0.5)
    if not tmp.exists():
        raise SystemExit("Edge wrote no PDF")
    try:
        os.replace(tmp, out)  # fails if a viewer holds report-draft.pdf open
    except PermissionError:
        raise SystemExit(f"{out} is open in a viewer and could not be replaced; close it and rerun (new PDF kept at {tmp})")
    print(out, out.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
