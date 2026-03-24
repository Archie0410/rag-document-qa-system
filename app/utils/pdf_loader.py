from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF payload.

    Raises:
        ValueError: If bytes do not represent a valid PDF.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid PDF file.") from exc

    pages_text: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages_text.append(page_text)

    return "\n".join(pages_text).strip()
