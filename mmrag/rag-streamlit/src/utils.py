from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_text_splitter(max_chunk_size: int, chunk_overlap: int):
    """
    Returns a LangChain text splitter configured for chunking large documents.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=max_chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

def clean_filename(filename: str) -> str:
    return filename.replace(" ", "_")
