#!/usr/bin/env python3
# Generates MD sidecars for PDFs that don't already have one.
# Text-layer PDFs use pdfplumber (fast); image PDFs use tesseract (CPU OCR).
from pathlib import Path

import pdfplumber
import pypdfium2
import pytesseract

REPO_ROOT = Path(".")
TEXT_THRESHOLD = 100  # chars per page to consider text-based


def has_text_layer(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:3]:
                if len((page.extract_text() or "").strip()) > TEXT_THRESHOLD:
                    return True
        return False
    except Exception:
        return False


def extract_pdfplumber(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n\n".join(page.extract_text() or "" for page in pdf.pages)


def extract_tesseract(pdf_path):
    doc = pypdfium2.PdfDocument(str(pdf_path))
    pages = []
    for page in doc:
        bitmap = page.render(scale=2)
        img = bitmap.to_pil()
        pages.append(pytesseract.image_to_string(img))
    return "\n\n".join(pages)


def main():
    pdfs = [
        p for p in REPO_ROOT.rglob("*.pdf")
        if ".git" not in p.parts
        and not (p.parent / f"{p.stem}.md").exists()
    ]

    if not pdfs:
        print("No new PDFs found.")
        return

    for pdf in pdfs:
        print(f"Processing: {pdf}")
        if has_text_layer(pdf):
            print("  text layer → pdfplumber")
            content = extract_pdfplumber(pdf)
        else:
            print("  image PDF → tesseract")
            content = extract_tesseract(pdf)

        if content:
            dest = pdf.parent / f"{pdf.stem}.md"
            dest.write_text(content, encoding="utf-8")
            print(f"  → {dest}")
        else:
            print(f"  failed: {pdf}")


if __name__ == "__main__":
    main()
