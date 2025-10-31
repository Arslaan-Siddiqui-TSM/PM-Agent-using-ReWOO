from typing import List, Tuple
import os
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredPDFLoader,
    Docx2txtLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_core.documents import Document
from .utils import create_text_splitter
from pydantic import BaseModel
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class IngestConfig(BaseModel):
    max_chunk_size: int = 1000
    chunk_overlap: int = 200

def load_documents(file_paths: List[str]) -> List[Document]:
    """
    Load a list of file paths into LangChain Document objects using
    appropriate loaders per file extension. Missing/unsupported files raise.
    """
    docs = []
    for path in file_paths:
        ext = Path(path).suffix.lower()
        try:
            if ext in [".txt", ".md"]:
                loader = TextLoader(path, encoding="utf-8")
            elif ext in [".pdf"]:
                # prefer PyPDFLoader or UnstructuredPDFLoader depending on system
                try:
                    loader = PyPDFLoader(path)
                except Exception:
                    loader = UnstructuredPDFLoader(path)
            elif ext in [".docx"]:
                loader = Docx2txtLoader(path)
            else:
                # fallback to text loader
                loader = TextLoader(path, encoding="utf-8")
            loaded = loader.load()
            docs.extend(loaded)
        except Exception as e:
            logger.exception("Failed to load %s: %s", path, e)
            # raise or skip depending on policy. We'll skip but log.
            continue
    return docs


def chunk_documents(docs: List[Document], cfg: IngestConfig):
    splitter = create_text_splitter(cfg.max_chunk_size, cfg.chunk_overlap)
    split_docs = []
    for d in docs:
        for chunk in splitter.split_documents([d]):
            split_docs.append(chunk)
    return split_docs
