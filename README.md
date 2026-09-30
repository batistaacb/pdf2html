# PDF → HTML for ChatGPT

Converts a PDF into one self-contained HTML file.

The output is designed as a practical source file for ChatGPT:
- selectable PDF text becomes real HTML text;
- PDF page boundaries are preserved;
- basic bold/italic/font-size information is retained;
- embedded PDF images are placed directly into the HTML;
- no separate image folder is required.

Inspired by the PyMuPDF implementation here:

https://gist.github.com/alecordev/9537f1a85895916a4a7b7fb4ec40fd39

## Files

- `main.py` — simple entry point.
- `codes_we_need.py` — conversion code.
- `requirements.txt` — dependency list.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Convert

```bash
python main.py Document.pdf
```

Output:

```text
your_file_chatgpt.html
```

Or choose the output filename:

```bash
python main.py your_file.pdf source.html
```

## Scanned PDFs

If the PDF is only scanned images, there may be no selectable text for PyMuPDF to extract. The HTML will still contain extracted images, but OCR should be performed first when text is needed.
