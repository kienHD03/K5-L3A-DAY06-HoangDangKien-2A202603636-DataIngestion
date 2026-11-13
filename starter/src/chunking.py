"""Implement fixed-size and structure-aware chunking."""
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    """TODO: split text into overlapping windows and retain page metadata."""
    chunks = []
    text = page.text
    step = max(1, size - overlap)
    
    chunk_index = 0
    for i in range(0, len(text), step):
        chunk_text = text[i:i + size]
        chunks.append(Chunk(
            chunk_id=f"{page.document_id}_p{page.page}_f{chunk_index}",
            document_id=page.document_id,
            source=page.source,
            page=page.page,
            text=chunk_text
        ))
        chunk_index += 1
        
    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """TODO: group paragraphs, split oversized paragraphs and retain metadata."""
    chunks = []
    paragraphs = [p.strip() for p in page.text.split('\n\n') if p.strip()]
    current_text = ""
    chunk_index = 0
    
    def _create_chunk(t: str):
        nonlocal chunk_index
        chunks.append(Chunk(
            chunk_id=f"{page.document_id}_p{page.page}_para{chunk_index}",
            document_id=page.document_id,
            source=page.source,
            page=page.page,
            text=t
        ))
        chunk_index += 1

    for p in paragraphs:
        if not current_text:
            if len(p) > max_size:
                for i in range(0, len(p), max_size):
                    _create_chunk(p[i:i + max_size])
            else:
                current_text = p
        elif len(current_text) + 2 + len(p) <= max_size:
            current_text += f"\n\n{p}"
        else:
            _create_chunk(current_text)
            if len(p) > max_size:
                for i in range(0, len(p), max_size):
                    _create_chunk(p[i:i + max_size])
                current_text = ""
            else:
                current_text = p
                
    if current_text:
        _create_chunk(current_text)
        
    return chunks