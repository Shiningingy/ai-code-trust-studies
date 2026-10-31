"""Render a study README as a paper-style HTML page, for printing to PDF."""
import re, sys
from markdown_it import MarkdownIt

src, out = sys.argv[1], sys.argv[2]
text = open(src, encoding='utf-8').read()
# Join hard-wrapped lines so paragraphs flow in the PDF
body = MarkdownIt('commonmark', {'html': False}).enable('table').render(text)
title = re.search(r'<h1>(.*?)</h1>', body).group(1)
body = re.sub(r'(<h1>.*?</h1>\s*)<p>(.*?)</p>', r'\1<p class="by">\2</p>', body, count=1, flags=re.S)
body = re.sub(r'<h2>Abstract</h2>\s*<p>(.*?)</p>', r'<div class="abs"><b>Abstract.</b> \1</div>', body, count=1, flags=re.S)
body = body.replace('<table>', '<table class="t">', 1)
head, refs = body.split('<h2>References</h2>')
CSS = """
@page { size: letter; margin: 0.85in 0.95in; }
body { font: 10.5pt/1.42 Georgia, 'Times New Roman', serif; color: #111; margin: 0; }
h1 { font-size: 17pt; line-height: 1.22; text-align: center; margin: 0 0 6pt; }
.by { text-align: center; font-size: 9.5pt; color: #444; margin: 0 0 12pt; }
.abs { font-size: 9.8pt; line-height: 1.38; margin: 0 16pt 12pt; padding: 8pt 12pt; border-top: 1px solid #999; border-bottom: 1px solid #999; }
h2 { font: bold 11.5pt Arial, sans-serif; margin: 15pt 0 4pt; break-after: avoid; }
p { margin: 0 0 6pt; text-align: justify; hyphens: auto; }
ul, ol { margin: 0 0 6pt; padding-left: 18pt; } li { margin-bottom: 3pt; text-align: justify; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 8pt; font: 9pt Arial, sans-serif; break-inside: avoid; }
th, td { padding: 3pt 6pt; border-bottom: 1px solid #ccc; text-align: right; }
th:first-child, td:first-child { text-align: left; }
h2 + p + table th:nth-child(2), h2 + p + table td:nth-child(2) { text-align: left; }
p + table th:nth-child(2), p + table td:nth-child(2) { text-align: right; }
table.t th:nth-child(2), table.t td:nth-child(2) { text-align: left; }
th { border-top: 1.5px solid #333; border-bottom: 1.5px solid #333; }
tr:last-child td { border-bottom: 1.5px solid #333; }
code { font: 9pt Consolas, monospace; }
.refs ol { font-size: 9pt; line-height: 1.32; } .refs li { text-align: left; }
"""
html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body>{head}<h2>References</h2><div class="refs">{refs}</div></body></html>'
open(out, 'w', encoding='utf-8').write(html)
print('html written')
