from typing import List
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredPDFLoader,
    Docx2txtLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    CSVLoader,
)
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
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
    Load multiple file formats into LangChain Document objects.
    Supported formats:
    - Text (.txt, .md)
    - PDF (.pdf)
    - Word (.docx)
    - CSV (.csv)
    - Excel (.xls, .xlsx)
    """
    docs = []
    for path in file_paths:
        ext = Path(path).suffix.lower()
        try:
            if ext in [".txt", ".md"]:
                loader = TextLoader(path, encoding="utf-8")

            elif ext == ".pdf":
                try:
                    loader = PyPDFLoader(path)
                except Exception:
                    loader = UnstructuredPDFLoader(path)

            elif ext == ".docx":
                loader = Docx2txtLoader(path)

            elif ext == ".csv":
                loader = CSVLoader(file_path=path)

            elif ext in [".xls", ".xlsx"]:
                loader = UnstructuredExcelLoader(path, mode="single")

            else:
                logger.warning(f"Unsupported file extension {ext}. Using TextLoader fallback.")
                loader = TextLoader(path, encoding="utf-8")

            loaded_docs = loader.load()
            docs.extend(loaded_docs)
            logger.info(f"Loaded {len(loaded_docs)} document(s) from {path}")

        except Exception as e:
            logger.exception(f"Failed to load {path}: {e}")
            continue

    return docs


def chunk_documents(docs: List[Document], cfg: IngestConfig):
    """
    Split loaded documents into smaller, overlapping chunks for embedding.
    """
    splitter = create_text_splitter(cfg.max_chunk_size, cfg.chunk_overlap)
    split_docs = []
    for d in docs:
        chunks = splitter.split_documents([d])
        split_docs.extend(chunks)
    return split_docs
