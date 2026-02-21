#!/usr/bin/env python3
"""
Generate a styled PDF from PRODUCT_ARCHITECTURE.md with embedded images.
Usage: python generate_pdf.py
Output: PRODUCT_ARCHITECTURE.pdf
"""

import base64
import os
import re
import markdown2
from xhtml2pdf import pisa

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_FILE = os.path.join(SCRIPT_DIR, "PRODUCT_ARCHITECTURE.md")
OUTPUT_PDF = os.path.join(SCRIPT_DIR, "PRODUCT_ARCHITECTURE.pdf")

# ---------------------------------------------------------------------------
# 1. Embed local images as base64 data URIs
# ---------------------------------------------------------------------------
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}


def embed_images_in_md(md_text: str) -> str:
    """Replace local image references ![alt](path) with base64 data URIs."""
    def replace_image(match):
        alt = match.group(1)
        src = match.group(2)
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        img_path = os.path.join(SCRIPT_DIR, src)
        if not os.path.isfile(img_path):
            return match.group(0)
        ext = os.path.splitext(img_path)[1].lower()
        mime = MIME_MAP.get(ext, "application/octet-stream")
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"![{alt}](data:{mime};base64,{b64})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_image, md_text)


def add_image_references(html_text: str) -> str:
    """
    In the rendered HTML, find links to local image files and replace
    them with inline <img> tags so they appear in the PDF.
    Handles patterns like:
      <a href="tables.drawio.png">...</a>
    """
    def replace_link(match):
        full = match.group(0)
        href = match.group(1)
        label = match.group(2)
        if href.startswith(("http://", "https://", "data:", "#")):
            return full
        ext = os.path.splitext(href)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            return full
        img_path = os.path.join(SCRIPT_DIR, href)
        if not os.path.isfile(img_path):
            return full
        mime = MIME_MAP.get(ext, "application/octet-stream")
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        clean_label = re.sub(r"<[^>]+>", "", label).strip()
        return (
            f'<div style="text-align:center;margin:16px 0;">'
            f'<p style="font-size:9pt;color:#6b7280;margin-bottom:6px;"><strong>{clean_label}</strong></p>'
            f'<img src="data:{mime};base64,{b64}" alt="{clean_label}" '
            f'style="max-width:95%;border:1px solid #e5e7eb;border-radius:6px;" />'
            f'</div>'
        )

    return re.sub(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', replace_link, html_text, flags=re.DOTALL)


# ---------------------------------------------------------------------------
# 2. CSS for a professional PDF layout
# ---------------------------------------------------------------------------
PDF_CSS = """
@page {
    size: A4;
    margin: 18mm 16mm 20mm 16mm;
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.5;
    color: #1a1a1a;
}

/* ── Headings ── */
h1 {
    font-size: 20pt;
    color: #059669;
    border-bottom: 3px solid #059669;
    padding-bottom: 6px;
    margin-top: 0;
    margin-bottom: 14px;
}

h2 {
    font-size: 15pt;
    color: #065f46;
    border-bottom: 2px solid #a7f3d0;
    padding-bottom: 4px;
    margin-top: 24px;
    margin-bottom: 10px;
}

h3 {
    font-size: 12pt;
    color: #047857;
    margin-top: 18px;
    margin-bottom: 6px;
}

h4 {
    font-size: 10.5pt;
    color: #064e3b;
    margin-top: 14px;
    margin-bottom: 5px;
}

/* ── Blockquotes ── */
blockquote {
    border-left: 4px solid #10b981;
    background-color: #ecfdf5;
    margin: 10px 0;
    padding: 8px 14px;
    color: #064e3b;
}

/* ── Tables ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 14px 0;
    font-size: 8.5pt;
}

th {
    background-color: #059669;
    color: white;
    font-weight: bold;
    text-align: left;
    padding: 6px 8px;
    font-size: 8pt;
}

td {
    padding: 5px 8px;
    border-bottom: 1px solid #d1d5db;
    vertical-align: top;
}

tr:nth-child(even) td {
    background-color: #f9fafb;
}

/* ── Code ── */
code {
    background-color: #f1f5f9;
    color: #be185d;
    padding: 1px 4px;
    font-size: 8pt;
    font-family: Courier, monospace;
}

pre {
    background-color: #1e293b;
    color: #e2e8f0;
    padding: 10px 12px;
    font-size: 7pt;
    line-height: 1.4;
    white-space: pre-wrap;
    word-wrap: break-word;
    margin: 8px 0 14px 0;
    border-left: 4px solid #059669;
}

pre code {
    background-color: transparent;
    color: #e2e8f0;
    padding: 0;
    font-size: 7pt;
}

/* ── Links ── */
a {
    color: #059669;
    text-decoration: none;
}

/* ── Lists ── */
ul, ol {
    margin: 4px 0 10px 0;
    padding-left: 22px;
}

li {
    margin-bottom: 2px;
}

/* ── Horizontal Rules ── */
hr {
    border: none;
    border-top: 2px solid #a7f3d0;
    margin: 20px 0;
}

/* ── Images ── */
img {
    max-width: 100%;
}

/* ── Paragraphs ── */
p {
    margin: 5px 0;
}

/* ── Strong ── */
strong {
    color: #064e3b;
}
"""


# ---------------------------------------------------------------------------
# 3. Build the PDF
# ---------------------------------------------------------------------------
def main():
    print("📄 Reading PRODUCT_ARCHITECTURE.md ...")
    with open(MD_FILE, "r", encoding="utf-8") as f:
        md_text = f.read()

    print("🖼️  Embedding local images ...")
    md_text = embed_images_in_md(md_text)

    print("🔄 Converting Markdown → HTML ...")
    html_body = markdown2.markdown(
        md_text,
        extras=[
            "fenced-code-blocks",
            "tables",
            "header-ids",
            "strike",
            "task_list",
            "cuddled-lists",
            "code-friendly",
        ],
    )

    # Embed linked image files as inline <img> in the HTML
    print("🖼️  Embedding linked image references ...")
    html_body = add_image_references(html_body)

    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Pollivu — Product &amp; Architecture Document</title>
    <style>
    {PDF_CSS}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    print("📑 Generating PDF ...")
    with open(OUTPUT_PDF, "wb") as pdf_file:
        status = pisa.CreatePDF(full_html, dest=pdf_file, encoding="utf-8")

    if status.err:
        print(f"❌ Error generating PDF: {status.err}")
        return

    size_kb = os.path.getsize(OUTPUT_PDF) / 1024
    print(f"✅ PDF created: {OUTPUT_PDF}")
    print(f"   Size: {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
