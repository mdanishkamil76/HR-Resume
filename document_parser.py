import fitz
from docx import Document

def extract_text(uploaded_file, filename: str) -> str:
    data = uploaded_file.getvalue()
    lower = filename.lower()
    if lower.endswith(".pdf"):
        doc = fitz.open(stream=data, filetype="pdf")
        text = "\n".join(page.get_text("text") for page in doc)
        doc.close()
    elif lower.endswith(".docx"):
        import io
        doc = Document(io.BytesIO(data))
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        text = "\n".join(parts)
    else:
        raise ValueError("Unsupported file type. Upload PDF or DOCX.")
    if not text.strip():
        raise ValueError("No selectable text found. This may be a scanned PDF; run OCR first or upload a DOCX.")
    return text[:50000]
