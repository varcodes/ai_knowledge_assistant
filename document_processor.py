import io
import fitz
from docx import Document

def extract_documents(uploaded_files):
    """
    Return page/paragraph-level records:
    {source, location, text}
    PDF locations are page numbers. DOCX locations are paragraph numbers.
    """
    records = []
    for uploaded in uploaded_files:
        name = uploaded.name
        raw = uploaded.getvalue()
        suffix = name.lower().rsplit(".", 1)[-1]

        if suffix == "pdf":
            with fitz.open(stream=raw, filetype="pdf") as pdf:
                for page_number, page in enumerate(pdf, start=1):
                    text = page.get_text("text").strip()
                    if text:
                        records.append({
                            "source": name,
                            "location": f"Page {page_number}",
                            "text": text
                        })

        elif suffix == "docx":
            document = Document(io.BytesIO(raw))
            for paragraph_number, paragraph in enumerate(document.paragraphs, start=1):
                text = paragraph.text.strip()
                if text:
                    records.append({
                        "source": name,
                        "location": f"Paragraph {paragraph_number}",
                        "text": text
                    })

            # Include table content, which can otherwise be missed in Word files.
            table_number = 0
            for table in document.tables:
                table_number += 1
                for row_number, row in enumerate(table.rows, start=1):
                    text = " | ".join(cell.text.strip() for cell in row.cells).strip()
                    if text.replace("|", "").strip():
                        records.append({
                            "source": name,
                            "location": f"Table {table_number}, row {row_number}",
                            "text": text
                        })
        else:
            continue
    return records
