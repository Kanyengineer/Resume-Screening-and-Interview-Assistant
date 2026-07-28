"""
resume_parser.py
-----------------
Extracts clean, usable text from a PDF resume.

Week 1: basic single-column PDF text extraction.
Week 6: added two-column layout detection and correct reading order
reconstruction using word-level bounding box analysis.

Two-column fix:
    The original approach used page.extract_text() which reads text based on
    vertical Y-position only. For two-column layouts, this merges left and
    right column lines at the same height into one garbled line.

    The fix uses page.extract_words() to get every word with its X,Y
    coordinates, then detects a gap in the horizontal distribution of word
    positions (indicating the space between two columns), and reads each
    column top-to-bottom separately before combining.
"""

import pdfplumber
import re


def detect_column_split(words: list, page_width: float):
    """
    Detects whether a page has a two-column layout by finding a large gap
    in the horizontal distribution of word X-start positions.

    Args:
        words: list of word dicts from page.extract_words()
        page_width: width of the page in points

    Returns:
        X-coordinate of the column split point if two-column layout detected,
        None if single-column layout.
    """
    if len(words) < 10:
        return None

    bucket_size = 10
    buckets = {}
    for w in words:
        bucket = int(w["x0"] // bucket_size) * bucket_size
        buckets[bucket] = buckets.get(bucket, 0) + 1

    margin_left = page_width * 0.05
    margin_right = page_width * 0.85
    populated = sorted([b for b in buckets.keys() if margin_left <= b <= margin_right])

    if len(populated) < 2:
        return None

    max_gap = 0
    gap_center = None
    for i in range(len(populated) - 1):
        gap = populated[i + 1] - populated[i]
        if gap > max_gap:
            max_gap = gap
            gap_center = (populated[i] + populated[i + 1]) / 2

    # Only call it two-column if the gap is at least 80 points wide
    if max_gap >= 80 and gap_center is not None:
        return gap_center

    return None


def extract_two_column_text(page, split_x: float) -> str:
    """
    Extracts text from a two-column page by reading each column
    top-to-bottom separately, then combining left column + right column.

    Args:
        page: pdfplumber page object
        split_x: X-coordinate separating left and right columns

    Returns:
        Extracted text with correct reading order.
    """
    words = page.extract_words()

    left_words = [w for w in words if w["x0"] < split_x]
    right_words = [w for w in words if w["x0"] >= split_x]

    def words_to_text(word_list):
        if not word_list:
            return ""
        sorted_words = sorted(word_list, key=lambda w: (round(w["top"], 1), w["x0"]))
        lines = []
        current_line = []
        current_y = None
        y_tolerance = 3

        for word in sorted_words:
            word_y = round(word["top"], 1)
            if current_y is None or abs(word_y - current_y) <= y_tolerance:
                current_line.append(word["text"])
                current_y = word_y
            else:
                lines.append(" ".join(current_line))
                current_line = [word["text"]]
                current_y = word_y

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    left_text = words_to_text(left_words)
    right_text = words_to_text(right_words)

    combined = []
    if left_text.strip():
        combined.append(left_text)
    if right_text.strip():
        combined.append(right_text)

    return "\n".join(combined)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts raw text from all pages of a PDF resume.

    Detects two-column layouts per page and handles them separately.
    Falls back to standard extract_text() for single-column pages.

    Args:
        pdf_path: path to the resume PDF file.

    Returns:
        A single string containing all extracted text.
    """
    full_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            split_x = detect_column_split(words, page.width)

            if split_x is not None:
                page_text = extract_two_column_text(page, split_x)
            else:
                page_text = page.extract_text()

            if page_text:
                full_text.append(page_text)

    return "\n".join(full_text)


def clean_text(text: str) -> str:
    """
    Cleans raw extracted text.
    """
    text = re.sub(r"[•●▪]", "-", text)
    lines = [line.strip() for line in text.split("\n")]
    cleaned_lines = [line for line in lines if line != ""]
    return "\n".join(cleaned_lines)


def parse_resume(pdf_path: str) -> dict:
    """
    Main entry point. Takes a PDF path, returns cleaned text + metadata.
    """
    raw_text = extract_text_from_pdf(pdf_path)
    cleaned = clean_text(raw_text)

    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)

    return {
        "raw_text": raw_text,
        "clean_text": cleaned,
        "num_pages": num_pages,
        "char_count": len(cleaned),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python resume_parser.py <path_to_resume.pdf>")
        sys.exit(1)

    result = parse_resume(sys.argv[1])
    print(f"Pages: {result['num_pages']}")
    print(f"Characters: {result['char_count']}")
    print("---- First 500 chars ----")
    print(result["clean_text"][:500])