# AI Knowledge Assistant — SCSC prototype

## Run locally
1. Install Python 3.10 or newer.
2. In this folder, run:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Open the local URL shown by Streamlit and upload an approved, text-based PDF.

## Included
- PDF upload and page-by-page text extraction
- Keyword-based passage ranking
- Concise answer extraction (maximum about 65 words)
- Source page references and supporting passages
- A safe fallback when relevant information is not found

## Important limitations
- This is a demonstrable prototype, not a production deployment.
- It does not send files to an external service and does not require an API key.
- Scanned/image-only PDFs need OCR, which is not included.
- Retrieval is keyword-based, so test with representative questions. Verify important answers against the source.
- Use only approved documents and follow SCSC data-handling rules.
