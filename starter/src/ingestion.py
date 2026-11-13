"""Read and normalize source data. TODO: implement functions."""
import unicodedata
import re
from pathlib import Path
from pypdf import PdfReader
from .models import DocumentPage


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """TODO: extract each physical page; keep its page number and source."""
    pages = []
    reader = PdfReader(path)
    for i, page in enumerate(reader.pages):
        raw_text = page.extract_text()
        text = normalize_text(raw_text) if raw_text else ""
        
        pages.append(DocumentPage(
            document_id=document_id,
            source=source,
            page=i + 1,
            text=text
        ))
    return pages

def normalize_text(text: str) -> str:
    """TODO: normalize Unicode and whitespace without discarding useful structure."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()