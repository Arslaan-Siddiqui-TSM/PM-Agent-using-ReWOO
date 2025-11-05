"""
Embedding Handler

RESPONSIBILITY: Embed Markdown files to Qdrant vector store ONLY
- Input: Markdown (.md) files
- Output: Vector embeddings in Qdrant collection
- Does NOT handle PDF parsing

Workflow:
  Markdown Files → UnstructuredMarkdownLoader → OpenAI Embeddings → Qdrant Vector Store
  
Uses LangChain's UnstructuredMarkdownLoader for proper markdown structure recognition.
Uses global caching to avoid re-embedding the same documents.
"""

from typing import List, Dict, Any
from pathlib import Path
from rich.console import Console
import logging

from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_core.documents import Document

from src.core.qdrant_manager import QdrantManager
from src.core.embedding_cache_manager import EmbeddingCacheManager
from src.core.docling_parser import ParsedDocument

logger = logging.getLogger(__name__)


class EmbeddingHandler:
    """
    Handles embedding markdown files into Qdrant with global caching.
    
    Workflow:
    1. Check global cache for embeddings (SHA256 hash)
    2. If cached: Copy existing embeddings to session collection
    3. If not cached: Create new embeddings from markdown
    4. Store vectors in Qdrant collection (pm_agent_sessionID)
    5. Update global cache for future reuse
    """
    
    def __init__(
        self,
        session_id: str,
        qdrant_url: str = "http://localhost:6333",
        embedding_model: str = "text-embedding-3-large",
        embedding_provider: str = "openai",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        verbose: bool = False
    ):
        """
        Initialize embedding handler.
        
        Args:
            session_id: Unique session identifier
            qdrant_url: URL of Qdrant server
            embedding_model: Embedding model name
            embedding_provider: "openai" or "gemini"
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
            verbose: Enable verbose console output
        """
        self.session_id = session_id
        self.collection_name = f"pm_agent_{session_id[:8]}"
        self.verbose = verbose
        self.console = Console() if verbose else None
        
        # Initialize Qdrant manager
        self.qdrant_manager = QdrantManager(
            session_id=session_id,
            qdrant_url=qdrant_url,
            embedding_model=embedding_model,
            embedding_provider=embedding_provider,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Initialize cache manager
        self.cache_manager = EmbeddingCacheManager(cache_dir="data/embedding_cache")
    
    def _load_markdown_with_unstructured(self, md_file_path: str) -> List[Document]:
        """
        Load markdown file using LangChain's UnstructuredMarkdownLoader.
        
        This provides better structure recognition for:
        - Headers (H1, H2, H3, etc.)
        - Lists (ordered and unordered)
        - Code blocks
        - Links and images
        - Tables
        
        Args:
            md_file_path: Path to the markdown file
            
        Returns:
            List of LangChain Document objects with structured content
        """
        try:
            logger.info(f"Loading markdown with UnstructuredMarkdownLoader: {Path(md_file_path).name}")
            
            # Use "elements" mode for better structure recognition
            loader = UnstructuredMarkdownLoader(
                md_file_path,
                mode="elements",  # Split by structural elements (headers, paragraphs, lists, etc.)
                strategy="fast"   # Fast processing without OCR
            )
            
            docs = loader.load()
            
            logger.info(f"  → Loaded {len(docs)} structured elements from {Path(md_file_path).name}")
            
            return docs
            
        except Exception as e:
            logger.warning(f"UnstructuredMarkdownLoader failed for {md_file_path}: {e}")
            logger.info(f"  → Falling back to simple text loading")
            
            # Fallback: Simple text loading if unstructured fails
            with open(md_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return [Document(
                page_content=content,
                metadata={
                    "source": Path(md_file_path).name,
                    "file_path": str(md_file_path),
                    "loader": "fallback_text"
                }
            )]
    
    def embed_documents(
        self,
        parsed_documents: List[ParsedDocument],
        cached_documents_info: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Embed markdown files into Qdrant with caching.
        
        Uses UnstructuredMarkdownLoader for better structure recognition.
        
        Args:
            parsed_documents: List of newly parsed documents
            cached_documents_info: List of cached document metadata
        
        Returns:
            Dictionary containing:
            - qdrant_manager: QdrantManager instance
            - qdrant_stats: Statistics about embedding creation/storage
            - collection_name: Name of Qdrant collection
        """
        if self.verbose and self.console:
            self.console.rule("[bold yellow]🧠 Loading & Embedding Markdown with UnstructuredMarkdownLoader[/bold yellow]")
        
        qdrant_stats = {
            "chunks_created": 0,
            "chunks_added": 0,
            "documents_processed": 0
        }
        
        # Load markdown files using UnstructuredMarkdownLoader
        if parsed_documents:
            logger.info(f"\n📚 Loading {len(parsed_documents)} markdown files with UnstructuredMarkdownLoader...")
            
            all_langchain_docs = []
            
            for parsed_doc in parsed_documents:
                # Load the markdown file with structure recognition
                md_docs = self._load_markdown_with_unstructured(parsed_doc.output_md_path)
                
                # Add session and document metadata to each element
                for doc in md_docs:
                    doc.metadata.update({
                        "original_pdf": parsed_doc.file_name,
                        "original_pdf_path": parsed_doc.file_path,
                        "markdown_path": parsed_doc.output_md_path,
                        "parser": parsed_doc.parser_used,
                        "session_id": self.session_id,
                        "processing_time": parsed_doc.processing_time,
                        "num_pages": parsed_doc.num_pages
                    })
                
                all_langchain_docs.extend(md_docs)
                
                if self.verbose and self.console:
                    self.console.print(f"  [cyan]✓[/cyan] {parsed_doc.file_name}: {len(md_docs)} elements")
            
            logger.info(f"✅ Loaded {len(all_langchain_docs)} structured elements from {len(parsed_documents)} markdown files\n")
            
            # Ingest LangChain documents directly to Qdrant
            qdrant_stats = self.qdrant_manager.ingest_langchain_documents(all_langchain_docs)
            
            # Add to cache
            for doc in parsed_documents:
                file_hash = self.cache_manager.calculate_file_hash(doc.file_path)
                self.cache_manager.add_to_cache(
                    file_hash=file_hash,
                    metadata={
                        "original_filename": doc.file_name,
                        "file_size_bytes": Path(doc.file_path).stat().st_size,
                        "parsed_md_path": doc.output_md_path,
                        "qdrant_collection": self.collection_name,
                        "qdrant_point_ids": qdrant_stats.get("point_ids", []),
                        "chunk_count": qdrant_stats["chunks_created"] // len(parsed_documents) if parsed_documents else 0,
                        "embedding_model": "text-embedding-3-large",
                        "sessions_used_in": [self.session_id]
                    }
                )
        
        # Copy cached embeddings to session collection
        for cached_doc in cached_documents_info:
            copy_result = self.qdrant_manager.copy_cached_embeddings(
                file_hash=cached_doc["file_hash"],
                cache_manager=self.cache_manager
            )
            qdrant_stats["chunks_added"] += copy_result.get("points_copied", 0)
        
        if self.verbose and self.console:
            self.console.print(f"\n[green]✓ Ingested into Qdrant[/green]")
            self.console.print(f"  - Collection: {self.collection_name}")
            self.console.print(f"  - New chunks: {qdrant_stats.get('chunks_created', 0)}")
            self.console.print(f"  - Cached chunks: {sum([cached_doc.get('cached_info', {}).get('chunk_count', 0) for cached_doc in cached_documents_info])}")
            self.console.print(f"  - Total chunks: {qdrant_stats.get('chunks_added', 0)}")
            self.console.print()
        
        return {
            "qdrant_manager": self.qdrant_manager,
            "qdrant_stats": qdrant_stats,
            "collection_name": self.collection_name
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache_manager.get_cache_stats()

