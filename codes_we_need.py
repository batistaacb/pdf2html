"""
PDF -> standalone HTML converter for use as a ChatGPT source.

Inspired by:
https://gist.github.com/alecordev/9537f1a85895916a4a7b7fb4ec40fd39

Uses PyMuPDF to extract selectable PDF text and embedded images.
"""

from pathlib import Path
from typing import Optional
import base64
import html
import re

#import fitz  # PyMuPDF
import pymupdf

def _safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "converted"


def _color_to_hex(color: int) -> str:
    return f"#{color:06x}"


def _span_html(span: dict) -> str:
    text = html.escape(span.get("text", ""))
    if not text:
        return ""

    font_name = span.get("font", "")
    size = float(span.get("size", 12))
    color = int(span.get("color", 0))

    styles = [f"font-size:{size:.2f}px"]
    if color:
        styles.append(f"color:{_color_to_hex(color)}")

    classes = ["pdf-text-span"]
    font_lower = font_name.lower()

    if "bold" in font_lower:
        classes.append("bold")
    if "italic" in font_lower or "oblique" in font_lower:
        classes.append("italic")

    return (
        f'<span class="{" ".join(classes)}" '
        f'style="{";".join(styles)}">{text}</span>'
    )


def _extract_page_text(page: pymupdf.Page) -> str:
    data = page.get_text("dict", sort=True)
    blocks_html = []

    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue

        lines_html = []

        for line in block.get("lines", []):
            spans = [_span_html(span) for span in line.get("spans", [])]
            line_html = "".join(spans).strip()

            if line_html:
                lines_html.append(f'<div class="pdf-line">{line_html}</div>')

        if lines_html:
            blocks_html.append(
                '<div class="pdf-text-block">'
                + "".join(lines_html)
                + "</div>"
            )

    return "\n".join(blocks_html)


def _extract_images(page: pymupdf.Page) -> list[dict]:
    images = []
    seen_xrefs = set()

    for image_index, image in enumerate(page.get_images(full=True)):
        xref = image[0]

        if xref in seen_xrefs:
            continue

        seen_xrefs.add(xref)

        try:
            extracted = page.parent.extract_image(xref)
            image_bytes = extracted["image"]
            extension = extracted.get("ext", "png")
            mime = f"image/{extension}"

            data_uri = (
                f"data:{mime};base64,"
                f"{base64.b64encode(image_bytes).decode('ascii')}"
            )

            images.append({
                "index": image_index + 1,
                "src": data_uri,
            })
        except Exception:
            continue

    return images


def _page_html(page_number: int, page: pymupdf.Page) -> str:
    text_html = _extract_page_text(page)
    images = _extract_images(page)

    image_html = []

    for image in images:
        image_html.append(
            f"""
            <figure class="pdf-image">
                <img src="{image['src']}"
                     alt="Image {image['index']} from PDF page {page_number}"
                     loading="lazy">
            </figure>
            """
        )

    if not text_html:
        text_html = (
            '<p class="no-text">No selectable text was found on this page. '
            'This may be a scanned/image-only page.</p>'
        )

    return f"""
    <section class="pdf-page" id="page-{page_number}">
        <header class="page-header">PDF page {page_number}</header>
        <div class="page-content">
            {text_html}
            {''.join(image_html)}
        </div>
    </section>
    """


def convert_pdf_to_html(
    pdf_path: str,
    output_path: Optional[str] = None,
) -> str:
    input_path = Path(pdf_path)

    if not input_path.exists():
        raise FileNotFoundError(f"PDF file not found: {input_path}")

    if input_path.suffix.lower() != ".pdf":
        raise ValueError("Input file must have a .pdf extension.")

    if output_path is None:
        output_path = input_path.with_name(
            f"{_safe_filename(input_path.stem)}2chatgpt.html"
        )
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pymupdf.open(input_path) as document:
        metadata = document.metadata or {}
        pages = []
        total_characters = 0

        for page_number, page in enumerate(document, start=1):
            try:
                page.clean_contents()
            except Exception:
                pass

            total_characters += len(page.get_text("text"))
            pages.append(_page_html(page_number, page))

        title = html.escape(metadata.get("title") or input_path.stem)
        source_name = html.escape(input_path.name)

        warning = ""

        if total_characters == 0:
            warning = """
            <aside class="warning">
                <strong>Note:</strong> This PDF contains no selectable text.
                It may be a scanned document. OCR is recommended before
                conversion if text extraction is required.
            </aside>
            """

        document_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
    :root {{
        color-scheme: light;
        --text: #202124;
        --muted: #5f6368;
        --border: #dadce0;
        --background: #f8f9fa;
        --page: #ffffff;
    }}

    * {{ box-sizing: border-box; }}

    body {{
        margin: 0;
        padding: 24px;
        background: var(--background);
        color: var(--text);
        font-family: Arial, Helvetica, sans-serif;
        line-height: 1.5;
    }}

    .document {{
        max-width: 1100px;
        margin: 0 auto;
    }}

    .document-header {{
        background: var(--page);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 20px;
    }}

    .document-header h1 {{
        margin: 0 0 8px;
        font-size: 24px;
    }}

    .metadata {{
        color: var(--muted);
        font-size: 14px;
    }}

    .warning {{
        margin-top: 16px;
        padding: 12px 16px;
        border: 1px solid #f0c36d;
        background: #fff8e1;
        border-radius: 6px;
    }}

    .pdf-page {{
        background: var(--page);
        border: 1px solid var(--border);
        border-radius: 6px;
        margin: 20px 0;
        overflow: hidden;
    }}

    .page-header {{
        padding: 8px 16px;
        background: #f1f3f4;
        border-bottom: 1px solid var(--border);
        color: var(--muted);
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }}

    .page-content {{
        padding: 28px;
        overflow-x: auto;
    }}

    .pdf-text-block {{
        margin: 0 0 14px;
    }}

    .pdf-line {{
        min-height: 1em;
    }}

    .pdf-text-span.bold {{
        font-weight: 700;
    }}

    .pdf-text-span.italic {{
        font-style: italic;
    }}

    .pdf-image {{
        margin: 24px 0;
        text-align: center;
    }}

    .pdf-image img {{
        max-width: 100%;
        height: auto;
    }}

    .no-text {{
        color: var(--muted);
        font-style: italic;
    }}

    @media print {{
        body {{
            background: white;
            padding: 0;
        }}

        .pdf-page {{
            break-after: page;
            border: none;
            margin: 0;
        }}
    }}
</style>
</head>
<body>
<main class="document">
    <header class="document-header">
        <h1>{title}</h1>
        <div class="metadata">
            Source PDF: {source_name}<br>
            Pages: {len(document)}<br>
            Extracted text characters: {total_characters:,}
        </div>
        {warning}
    </header>

    {''.join(pages)}
</main>
</body>
</html>
"""

    output_path.write_text(document_html, encoding="utf-8")
    return str(output_path)
