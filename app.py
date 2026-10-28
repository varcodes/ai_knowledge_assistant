import io
import json
import re
from pathlib import Path
from collections import Counter

import streamlit as st
from pypdf import PdfReader

st.set_page_config(page_title="AI Knowledge Assistant", page_icon="📚", layout="centered")
st.title("AI Knowledge Assistant")
st.caption("Choose a sample question or ask your own. Answers are kept to one line and grounded in the selected source.")

DATA_PATH = Path(__file__).with_name("india_2026_qa.json")
with DATA_PATH.open("r", encoding="utf-8") as f:
    INDIA_QA = json.load(f)

def tokens(s):
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)?", s)]

def similarity(question, candidate):
    q = set(tokens(question))
    c = set(tokens(candidate))
    if not q or not c:
        return 0.0
    # Jaccard-style overlap with question coverage weighted more heavily.
    return (len(q & c) / len(q)) * 0.75 + (len(q & c) / len(q | c)) * 0.25

def find_india_answer(question):
    ranked = sorted(
        ((max(similarity(question, x["question"]), similarity(question, x["answer"])), x)
         for x in INDIA_QA),
        key=lambda item: item[0], reverse=True
    )
    if ranked and (ranked[0][0] >= 0.38 or question.strip().lower() == ranked[0][1]["question"].lower()):
        return ranked[0][1]["answer"], ranked[0][1]["question"], ranked[0][0]
    return None, None, ranked[0][0] if ranked else 0

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def extract_pdf(uploaded_bytes):
    reader = PdfReader(io.BytesIO(uploaded_bytes))
    pages, sentences = [], []
    for page_num, page in enumerate(reader.pages, start=1):
        page_text = clean(page.extract_text() or "")
        if page_text:
            pages.append({"page": page_num, "text": page_text})
            for sentence in re.split(r"(?<=[.!?])\s+", page_text):
                sentence = sentence.strip(" •-\t")
                if 5 <= len(sentence.split()) <= 45:
                    sentences.append({"page": page_num, "text": sentence})
    return pages, sentences

def sample_questions_from_pdf(sentences, limit=6):
    # Offer concise topic-based sample prompts drawn from actual sentences in the uploaded PDF.
    seen, samples = set(), []
    for item in sentences:
        words = tokens(item["text"])
        if len(words) < 7:
            continue
        key = item["text"].lower()
        if key in seen:
            continue
        seen.add(key)
        sample_answer = item["text"]
        if len(sample_answer.split()) > 32:
            sample_answer = " ".join(sample_answer.split()[:32]).rstrip(" ,;:") + "…"
        samples.append({
            "question": "What does the PDF say about: " + " ".join(item["text"].split()[:8]).rstrip(".,;:") + "?",
            "answer": sample_answer,
            "page": item["page"]
        })
        if len(samples) >= limit:
            break
    return samples

def answer_pdf(question, sentences):
    q = set(tokens(question))
    if not q:
        return None, None, 0
    scored = []
    for item in sentences:
        terms = set(tokens(item["text"]))
        if not terms:
            continue
        overlap = len(q & terms)
        coverage = overlap / max(1, len(q))
        score = coverage * 0.75 + overlap / len(q | terms) * 0.25
        if overlap:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored or scored[0][0] < 0.12:
        return None, None, 0
    best_score, best = scored[0]
    answer = best["text"]
    # One sentence only; trim long passages to a single concise line.
    words = answer.split()
    if len(words) > 32:
        answer = " ".join(words[:32]).rstrip(" ,;:") + "…"
    return answer, best["page"], best_score

source = st.radio("Choose knowledge source", ["India 2026 knowledge base", "Upload my own PDF"], horizontal=True)

if source == "India 2026 knowledge base":
    st.markdown("**Sample questions**")
    sample_labels = ["Choose a sample question…"] + [x["question"] for x in INDIA_QA]
    selected = st.selectbox("Select a question", sample_labels, index=0)
    custom = st.text_input("Or type your own question", placeholder="e.g. When did India become independent?")
    question = custom.strip() if custom.strip() else (selected if selected != sample_labels[0] else "")
    if question and st.button("Get one-line answer", type="primary"):
        answer, matched_q, confidence = find_india_answer(question)
        if answer:
            st.markdown("**Answer**")
            st.write(answer)
            if matched_q and matched_q.lower() != question.lower():
                st.caption(f"Matched knowledge-base question: {matched_q}")
        else:
            st.info("I couldn't find a sufficiently close answer in the India 2026 knowledge base. Try a sample question or upload a source PDF.")
    st.caption(f"Knowledge base: {len(INDIA_QA)} sample question-and-answer pairs from the supplied India 2026 PDF.")
else:
    uploaded = st.file_uploader("Upload your own text-based PDF", type=["pdf"])
    if uploaded:
        try:
            pages, sentences = extract_pdf(uploaded.getvalue())
            if not sentences:
                st.error("No selectable text was found. This may be a scanned PDF; OCR is not included.")
            else:
                st.success(f"Loaded {len(pages)} page(s) with extractable text.")
                samples = sample_questions_from_pdf(sentences)
                st.markdown("**Sample questions from your PDF**")
                options = ["Choose a sample question…"] + [x["question"] for x in samples]
                chosen = st.selectbox("Choose a sample question", options)
                custom = st.text_input("Or type your own question", placeholder="Ask something specific about this PDF")
                question = custom.strip() if custom.strip() else (chosen if chosen != options[0] else "")
                if question and st.button("Get one-line answer", type="primary"):
                    # For a generated sample prompt, answer the exact source sentence that created it.
                    sample_match = next((x for x in samples if x["question"] == question), None)
                    if sample_match:
                        answer, page = sample_match["answer"], sample_match["page"]
                    else:
                        answer, page, confidence = answer_pdf(question, sentences)
                    if answer:
                        st.markdown("**Answer**")
                        st.write(answer)
                        st.caption(f"Source: page {page}")
                    else:
                        st.info("I couldn't find enough relevant information in this PDF to answer that question.")
                with st.expander("Show PDF sample answers"):
                    for item in samples:
                        st.markdown(f"**Q:** {item['question']}")
                        st.write(f"**A:** {item['answer']} (page {item['page']})")
        except Exception as e:
            st.error(f"Could not read this PDF: {e}")
    else:
        st.info("Upload a PDF to generate sample questions and answer your own questions from that document.")

st.divider()
st.caption("Accuracy note: this prototype retrieves answers from the supplied text; it does not train new model weights. Check important answers against the cited source. Current statistics remain estimates where the source labels them as estimates.")
