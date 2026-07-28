"""
jd_input.py
-----------
Handles job description input from three sources:
    1. Plain pasted text (no extraction needed)
    2. PDF file (reuses the same PDF extraction approach as resume_parser.py)
    3. Image file (screenshot of a job posting) - extracted via OCR using
       pytesseract + Tesseract

This module's job is ONLY to get clean text out of whatever format the JD
was provided in. Once we have text, jd_parser.py (Week 3) takes over to
extract structured info (required skills, experience, education) - that
logic doesn't need to know or care where the text came from.
"""

import os
import platform
import shutil
import pdfplumber
import pytesseract
from PIL import Image

# Only override the Tesseract path on Windows, and only if it isn't
# already resolvable on the system PATH (e.g. via an installer that
# registered it, or a user who added it manually). On Mac/Linux,
# Tesseract is normally installed via brew/apt and is already on PATH,
# so hardcoding a Windows-specific path here would break OCR entirely
# on those systems.
if platform.system() == "Windows" and shutil.which("tesseract") is None:
    _default_windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_default_windows_path):
        pytesseract.pytesseract.tesseract_cmd = _default_windows_path


def extract_text_from_jd_pdf(pdf_path: str) -> str:
    """
    Extracts text from a JD provided as a PDF file.

    Reuses the same approach as resume_parser.extract_text_from_pdf() -
    JDs are usually simpler single-column documents, so this works
    reliably for the common case.

    Args:
        pdf_path: path to the JD PDF file.

    Returns:
        Extracted raw text from all pages, joined by newlines.
    """
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text.append(page_text)
    return "\n".join(full_text)


def extract_text_from_jd_image(image_path: str) -> str:
    """
    Extracts text from a JD provided as an image (e.g. a screenshot of
    a job posting from LinkedIn, Naukri, WhatsApp, etc.) using OCR.

    Args:
        image_path: path to the image file (png, jpg, etc.)

    Returns:
        Extracted text as a string. May contain OCR errors/noise -
        quality depends heavily on image resolution and clarity.
    """
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text


def clean_jd_text(text: str) -> str:
    """
    Light cleanup for JD text, regardless of source (pasted, PDF, or OCR).

    OCR output in particular tends to have extra blank lines and stray
    whitespace, so this normalizes that. Does not alter actual words,
    since over-cleaning OCR text risks corrupting real content.

    Args:
        text: raw JD text from any source.

    Returns:
        Cleaned text.
    """
    lines = [line.strip() for line in text.split("\n")]
    cleaned_lines = [line for line in lines if line != ""]
    return "\n".join(cleaned_lines)


def get_jd_text(source_type: str, source) -> str:
    """
    Unified entry point - takes the JD in whatever form it was provided
    and returns clean text, ready for jd_parser.extract_jd_info().

    Args:
        source_type: one of "text", "pdf", "image"
        source: the actual content -
            - for "text": the raw string the user pasted
            - for "pdf": file path to the PDF
            - for "image": file path to the image

    Returns:
        Cleaned JD text as a string.

    Raises:
        ValueError: if source_type is not one of the supported types.
    """
    if source_type == "text":
        raw_text = source
    elif source_type == "pdf":
        raw_text = extract_text_from_jd_pdf(source)
    elif source_type == "image":
        raw_text = extract_text_from_jd_image(source)
    else:
        raise ValueError(f"Unsupported source_type: {source_type}")

    return clean_jd_text(raw_text)


if __name__ == "__main__":
    # Quick manual test
    import sys

    if len(sys.argv) < 3:
        print("Usage: python jd_input.py <text|pdf|image> <path_or_text>")
        sys.exit(1)

    mode = sys.argv[1]
    arg = sys.argv[2]

    if mode == "text":
        with open(arg, "r", encoding="utf-8") as f:
            arg = f.read()

    result = get_jd_text(mode, arg)
    print("---- Extracted JD Text ----")
    print(result[:1000])
