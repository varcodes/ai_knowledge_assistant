import streamlit as st
from document_processor import extract_documents
from rag_pipeline import build_index, retrieve_chunks, generate_answer

# Page configuration
st.set_page_config(
    page_title="AI Knowledge Assistant",
    page_icon="📚",
    layout="wide"
)

# Simple styling
st.markdown("""
<style>
    .stApp {
        background-color: #fafafa;
    }

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
    }

    h1 {
        color: #243447;
        font-size: 30px !important;
    }

    .subtitle {
        color: #6b7280;
        font-size: 15px;
        margin-bottom: 25px;
    }

    section[data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }

    [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 12px;
    }

    .status {
        color: #64748b;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)


# Header
st.title("📚 AI Knowledge Assistant")
st.markdown(
    '<div class="subtitle">'
    'Upload your documents and ask questions. '
    'I will help you find the information you need.'
    '</div>',
    unsafe_allow_html=True
)


# Sidebar
with st.sidebar:
    st.subheader("Your documents")

    uploaded_files = st.file_uploader(
        "Upload PDF or Word files",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    st.divider()

    st.subheader("Settings")

    top_k = st.slider(
        "Passages to search",
        min_value=1,
        max_value=8,
        value=4
    )

    model_name = st.text_input(
        "Ollama model",
        value="llama3.2"
    )

    st.caption("Make sure Ollama is running.")

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chunks" not in st.session_state:
    st.session_state.chunks = []

if "index" not in st.session_state:
    st.session_state.index = None

if "embedder" not in st.session_state:
    st.session_state.embedder = None

if "sources_signature" not in st.session_state:
    st.session_state.sources_signature = None


# Process uploaded documents
if uploaded_files:
    signature = tuple(
        (f.name, f.size, getattr(f, "file_id", None))
        for f in uploaded_files
    )

    if signature != st.session_state.sources_signature:
        try:
            with st.spinner("Reading your documents..."):
                docs = extract_documents(uploaded_files)
                chunks, index, embedder = build_index(docs)

                st.session_state.chunks = chunks
                st.session_state.index = index
                st.session_state.embedder = embedder
                st.session_state.sources_signature = signature
                st.session_state.messages = []

            st.success(
                f"Ready! Processed {len(uploaded_files)} document(s) "
                f"into {len(chunks)} passages."
            )

        except Exception as exc:
            st.error(f"Could not process the documents: {exc}")

else:
    if st.session_state.sources_signature is not None:
        st.session_state.chunks = []
        st.session_state.index = None
        st.session_state.embedder = None
        st.session_state.sources_signature = None
        st.session_state.messages = []


# Show uploaded document names
if st.session_state.chunks:
    with st.expander("View uploaded documents"):
        for name in sorted({
            chunk["source"] for chunk in st.session_state.chunks
        }):
            st.write(f"📄 {name}")

    st.markdown("### Chat")

else:
    st.info("👈 Upload a PDF or Word document from the sidebar to get started.")

    st.markdown("### Chat")


# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sources"):
            with st.expander("View sources"):
                for source in message["sources"]:
                    st.markdown(
                        f"**{source['source']}** — {source['location']}"
                    )
                    st.write(source["text"])
                    st.divider()


# Chat input
question = st.chat_input(
    "Ask a question about your documents...",
    disabled=not bool(st.session_state.chunks)
)

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Finding the answer..."):
            try:
                results = retrieve_chunks(
                    question,
                    st.session_state.chunks,
                    st.session_state.index,
                    st.session_state.embedder,
                    top_k=top_k
                )

                answer = generate_answer(
                    question,
                    results,
                    model_name=model_name
                )

                st.markdown(answer)

                sources = [
                    {
                        "source": item["source"],
                        "location": item["location"],
                        "score": float(item["score"]),
                        "text": item["text"]
                    }
                    for item in results
                ]

                if sources:
                    with st.expander("View sources"):
                        for source in sources:
                            st.markdown(
                                f"**{source['source']}** — "
                                f"{source['location']}"
                            )
                            st.write(source["text"])
                            st.divider()

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except Exception as exc:
                error_message = (
                    f"Sorry, I couldn't generate an answer. "
                    f"Check that Ollama is running and the model "
                    f"'{model_name}' is installed.\n\nDetails: {exc}"
                )

                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "sources": []
                })