# AI Knowledge Assistant — Basic RAG

A local Retrieval-Augmented Generation (RAG) chatbot for PDF and DOCX files.

## Features
- Upload one or more PDF or Word (`.docx`) files.
- Extract text while keeping PDF page numbers and Word paragraph/table locations.
- Split content into overlapping chunks.
- Embed chunks with Sentence Transformers.
- Retrieve relevant chunks with FAISS and cosine-similarity-equivalent inner product on normalized vectors.
- Generate grounded answers with a local Ollama model.
- Show retrieved source passages with each answer.

## Requirements
- Python 3.11 recommended.
- Ollama installed and running.
- Enough RAM for the embedding model and chosen LLM.

## Setup

### 1. Create and activate a virtual environment

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:
```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
```

### 2. Install Python packages
```bash
pip install -r requirements.txt
```

### 3. Install/download the Ollama model
Install Ollama from https://ollama.com/ then run:
```bash
ollama pull llama3.2
```

If you prefer another installed Ollama model, enter its exact name in the app's sidebar.

### 4. Run the app
```bash
streamlit run app.py
```

Upload `netflix_titles.pdf` or your own PDF/DOCX file in the sidebar and ask questions.

## Example questions for netflix_titles.pdf
- What is the release year of Squid Game?
- What is the description of Kota Factory?
- Which source passage describes Jaws?
- What information is available for each title?
- What is the IMDb rating of Squid Game?

The last question should be answered as unavailable if IMDb ratings are not present in the uploaded document.

## Notes and limitations
- The app builds the index in memory whenever the uploaded-file selection changes. Restarting the app or refreshing its session may require re-uploading files.
- PDF page references are based on the page number in the uploaded PDF. Scanned/image-only PDFs may need OCR; this version extracts embedded text and does not run OCR.
- DOCX references use paragraph or table-row locations, not Word page numbers.
- Retrieval scores help rank passages but are not calibrated confidence probabilities.
- The first run downloads the embedding model, which requires internet access.
- Answers depend on the quality of the source text, retrieval, and local LLM. Always verify important answers against the cited passage.
