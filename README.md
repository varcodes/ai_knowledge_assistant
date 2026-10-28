# AI Knowledge Assistant — India 2026 + user PDF

## Deploy online
1. Upload `app.py`, `requirements.txt`, and `india_2026_qa.json` to a GitHub repository.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Create an app, choose the repository/branch, and set Main file path to `app.py`.
4. Deploy.

## Features
- Built-in India 2026 Q&A knowledge base extracted from the supplied PDF.
- Sample question selector containing the source's question-and-answer pairs.
- User PDF upload with sample prompts based on its extracted text.
- One-sentence answers and page references for uploaded PDFs.
- Fallback message if a relevant answer is not found.

## Limitations
This is retrieval over a curated Q&A dataset and uploaded PDF text, not model-weight training. It requires text-based PDFs; OCR for scanned PDFs is not included. The retrieval is lexical and can miss paraphrases; test against representative questions and verify important answers against the source.
