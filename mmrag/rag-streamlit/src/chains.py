from langchain_classic.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
# represent chunks of documents before embedding or retrieval
from typing import Any
from .config import settings
import logging

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = """You are an assistant that answers questions using provided context from documents.
If the answer is not in the context, say you don't know and offer to search or request clarifying info.
Context:
{context}

Question: {question}
Helpful, concise answer:
"""

def make_qa_chain(retriever, openai_model: str = None) -> RetrievalQA:
    """
    Build a RetrievalQA chain using the selected LLM and retriever.
    """
    llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.0, client=None)
    prompt = PromptTemplate(template=DEFAULT_PROMPT, input_variables=["context", "question"])
    try:
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True,
        )
        return qa
    except Exception as e:
        logger.exception("Failed to create QA chain: %s", e)
        raise
