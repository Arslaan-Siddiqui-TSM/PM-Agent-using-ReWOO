from typing import Optional, List
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from .config import settings
import logging
import os

logger = logging.getLogger(__name__)

class ChromaStore:
    """
    Thin wrapper around Chroma vectorstore for upsert and query.
    """

    def __init__(self, persist_directory: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        # embeddings init
        self.embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL, openai_api_key=settings.OPENAI_API_KEY)
        # Create or connect to Chroma
        try:
            self.store = Chroma(
                collection_name=self.collection_name,
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )
        except Exception as e:
            logger.exception("Failed to initialize Chroma: %s", e)
            raise

    def add_documents(self, documents: List[Document], ids: Optional[List[str]] = None):
        """
        Upsert (add) documents to Chroma. Documents should be LangChain Document objects.
        """
        try:
            self.store.add_documents(documents, ids=ids)
            # persist to disk
            try:
                self.store.persist()
            except Exception:
                # some Chroma versions auto-persist; ignore if not supported
                logger.debug("Chroma persist not supported in this version or already persisted.")
        except Exception as e:
            logger.exception("Failed to add documents to Chroma: %s", e)
            raise

    def as_retriever(self, search_kwargs: Optional[dict] = None):
        return self.store.as_retriever(search_kwargs=search_kwargs or {"k": 4})

    def clear_collection(self):
        try:
            self.store.delete_collection(self.collection_name)
        except Exception as e:
            logger.debug("delete_collection failed or not available: %s", e)
            # fallback: try remove collection via client API if available
