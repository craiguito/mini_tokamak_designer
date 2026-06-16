"""HTML report generation."""

from __future__ import annotations

import html
from pathlib import Path


def markdown_to_simple_html(markdown_text: str) -> str:
    body_lines: list[str] = []
    in_table = False
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            body_lines.append(f"<h1>{html.escape(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            body_lines.append(f"<h2>{html.escape(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            body_lines.append(f"<h3>{html.escape(stripped[4:])}</h3>")
        elif stripped.startswith("- "):
            body_lines.append(f"<p>{html.escape(stripped)}</p>")
        elif stripped.startswith("|"):
            if not in_table:
                body_lines.append("<pre>")
                in_table = True
            body_lines.append(html.escape(line))
        else:
            if in_table:
                body_lines.append("</pre>")
                in_table = False
            if stripped:
                body_lines.append(f"<p>{html.escape(stripped)}</p>")
            else:
                body_lines.append("")
    if in_table:
        body_lines.append("</pre>")
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>MiniTokamak Designer Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 980px; line-height: 1.45; }
    code, pre { background: #f4f4f5; padding: 0.1rem 0.25rem; }
    pre { overflow-x: auto; padding: 1rem; }
    h1, h2, h3 { color: #1d3557; }
  </style>
</head>
<body>
""" + "\n".join(body_lines) + "\n</body>\n</html>\n"


def write_html_report(markdown_path: str | Path, output_path: str | Path) -> str:
    markdown_text = Path(markdown_path).read_text(encoding="utf-8")
    html_text = markdown_to_simple_html(markdown_text)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_text, encoding="utf-8")
    return str(out)

