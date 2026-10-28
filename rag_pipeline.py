import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import ollama

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def split_into_chunks(records, chunk_words=180, overlap_words=35):
    """Split each page/paragraph record into overlapping word chunks."""
    chunks = []
    for record in records:
        words = record["text"].split()
        if not words:
            continue
        start = 0
        while start < len(words):
            end = min(start + chunk_words, len(words))
            text = " ".join(words[start:end]).strip()
            if text:
                chunks.append({
                    "source": record["source"],
                    "location": record["location"],
                    "text": text
                })
            if end == len(words):
                break
            start = max(end - overlap_words, start + 1)
    return chunks

def build_index(records):
    if not records:
        raise ValueError("No readable text found in the uploaded documents.")
    chunks = split_into_chunks(records)
    if not chunks:
        raise ValueError("No searchable text chunks were created.")

    embedder = SentenceTransformer(EMBEDDING_MODEL)
    texts = [chunk["text"] for chunk in chunks]
    vectors = embedder.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    ).astype("float32")

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return chunks, index, embedder

def retrieve_chunks(question, chunks, index, embedder, top_k=4):
    query_vector = embedder.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")
    k = min(top_k, len(chunks))
    scores, ids = index.search(query_vector, k)
    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0:
            continue
        item = dict(chunks[int(idx)])
        item["score"] = float(score)
        results.append(item)
    return results

def generate_answer(question, retrieved_chunks, model_name="llama3.2"):
    if not retrieved_chunks:
        return "I couldn't find relevant information in the uploaded documents."

    context_parts = []
    for i, item in enumerate(retrieved_chunks, start=1):
        context_parts.append(
            f"[Source {i}: {item['source']}, {item['location']}]\n{item['text']}"
        )
    context = "\n\n".join(context_parts)

    prompt = f"""You are an AI Knowledge Assistant.
Answer the user's question using ONLY the source passages below.
Do not use outside knowledge or invent missing details.
If the passages do not contain the answer, say: "I couldn't find this information in the uploaded documents."
Keep the answer clear and concise.
When making a factual claim, cite the supporting source inline using the format [filename, Page N] or [filename, Paragraph N].

SOURCE PASSAGES:
{context}

USER QUESTION:
{question}

ANSWER:"""

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
    return response["message"]["content"].strip()
