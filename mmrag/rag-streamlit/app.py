import streamlit as st
from pathlib import Path
from typing import List
import tempfile
import os
from src.config import settings
from src.ingest import load_documents, chunk_documents, IngestConfig
from src.vectorstore import ChromaStore
from src.chains import make_qa_chain
from langchain_core.documents import Document
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="RAG - Streamlit + LangChain", layout="wide")

st.title("RAG Chatbot — Upload docs, ask questions")

with st.sidebar:
    st.header("Settings")
    persist_dir = st.text_input("Chroma persist directory", value=settings.CHROMA_PERSIST_DIRECTORY)
    collection_name = st.text_input("Collection name", value=settings.CHROMA_COLLECTION_NAME)
    max_chunk_size = st.number_input("Max chunk size", min_value=256, max_value=5000, value=settings.MAX_CHUNK_SIZE)
    chunk_overlap = st.number_input("Chunk overlap", min_value=0, max_value=1000, value=settings.CHUNK_OVERLAP)
    reindex = st.button("Clear & reindex collection")

# file uploader
uploaded_files = st.file_uploader("Upload files (PDF, TXT, DOCX)", accept_multiple_files=True, type=["pdf","txt","md","docx","pptx"])

if "store" not in st.session_state:
    st.session_state.store = None

if reindex:
    if st.session_state.store:
        try:
            st.session_state.store.clear_collection()
            st.success("Collection cleared (attempted).")
        except Exception as e:
            st.error(f"Clear failed: {e}")
    else:
        st.info("No collection in session to clear.")

# ingest
if uploaded_files:
    st.info(f"Saving {len(uploaded_files)} uploads to a temp dir and ingesting...")
    tmpdir = Path(tempfile.mkdtemp())
    saved_paths = []
    for f in uploaded_files:
        save_path = tmpdir / f.name
        with open(save_path, "wb") as out:
            out.write(f.getbuffer())
        saved_paths.append(str(save_path))
    # load & chunk
    try:
        raw_docs = load_documents(saved_paths)
        cfg = IngestConfig(max_chunk_size=int(max_chunk_size), chunk_overlap=int(chunk_overlap))
        split_docs = chunk_documents(raw_docs, cfg)
        # initialize chroma
        store = ChromaStore(persist_directory=persist_dir, collection_name=collection_name)
        # add ids for traceability
        ids = [str(uuid.uuid4()) for _ in split_docs]
        store.add_documents(split_docs, ids=ids)
        st.success(f"Ingested {len(split_docs)} chunks into Chroma collection '{collection_name}'.")
        st.session_state.store = store
    except Exception as e:
        st.exception(f"Ingestion failed: {e}")

# Chat interface
st.markdown("---")
st.subheader("Ask a question")
query = st.text_input("Enter your question", "")
k = st.slider("Retriever results (k)", min_value=1, max_value=10, value=4)
if st.button("Ask") and query.strip():
    if not st.session_state.get("store"):
        st.error("No documents indexed yet. Upload documents first.")
    else:
        try:
            retriever = st.session_state.store.as_retriever({"k": k})
            qa = make_qa_chain(retriever)
            result = qa({"query": query})
            answer = result["result"] if "result" in result else result.get("answer")
            st.write("**Answer:**")
            st.write(answer)
            # show source documents
            src_docs = result.get("source_documents", [])
            if src_docs:
                st.write("**Source documents (top results):**")
                for i, d in enumerate(src_docs[:k]):
                    st.write(f"---\n**Source {i+1} metadata:** {d.metadata if hasattr(d,'metadata') else {}}")
                    st.write(d.page_content[:1000] + ("..." if len(d.page_content) > 1000 else ""))
        except Exception as e:
            st.exception(f"Query failed: {e}")
