from pathlib import Path
import fitz


def extract_text(path: str) -> str:
    file_path = Path(path)
    if file_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files can be processed by extract_text().")

    pages = []
    with fitz.open(file_path) as document:
        for page in document:
            text = page.get_text("text")
            if text:
                pages.append(text)
    return "\n".join(pages).strip()


def extract_pdf_text(path: str) -> str:
    return extract_text(path)


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size.")

    text = " ".join(text.split()).strip()
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks
