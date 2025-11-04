"""
Qdrant Manager

Manages vector embeddings and semantic search using Qdrant.
Replaces the ChromaDB-based RAGManager with Qdrant functionality.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_text_splitters  import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

from src.config.feature_flags import feature_flags

logger = logging.getLogger(__name__)


class QdrantManager:
    """
    Manages vector embeddings and semantic search for document retrieval.
    
    Uses Qdrant for vector storage and OpenAI embeddings for semantic similarity.
    """
    
    def __init__(
        self,
        session_id: str,
        qdrant_url: Optional[str] = None,
        embedding_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Initialize Qdrant manager for a session.
        
        Args:
            session_id: Unique session identifier (used for collection name)
            qdrant_url: URL of Qdrant server
            embedding_model: OpenAI embedding model name
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
        """
        self.session_id = session_id
        self.collection_name = f"{feature_flags.qdrant_collection_prefix}_{session_id[:8]}"
        self.cache_collection = f"{feature_flags.qdrant_collection_prefix}_cache"
        
        # Use feature flags or provided values
        self.qdrant_url = qdrant_url or feature_flags.qdrant_url
        self.embedding_model = embedding_model or feature_flags.embedding_model
        self.chunk_size = chunk_size or feature_flags.max_chunk_size
        self.chunk_overlap = chunk_overlap or feature_flags.chunk_overlap
        
        logger.info(
            f"Initializing QdrantManager for session {session_id[:8]}: "
            f"url={self.qdrant_url}, model={self.embedding_model}, "
            f"chunks={self.chunk_size}/{self.chunk_overlap}"
        )
        
        # Initialize embeddings
        try:
            self.embeddings = OpenAIEmbeddings(model=self.embedding_model)
            logger.info(f"OpenAI embeddings initialized: {self.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {e}")
            raise RuntimeError(
                f"Failed to initialize embeddings. Ensure OPENAI_API_KEY is set. Error: {e}"
            )
        
        # Initialize Qdrant client
        try:
            self.client = QdrantClient(url=self.qdrant_url)
            logger.info(f"Qdrant client connected: {self.qdrant_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise RuntimeError(
                f"Failed to connect to Qdrant at {self.qdrant_url}. "
                f"Ensure Qdrant is running (docker-compose up -d qdrant). Error: {e}"
            )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # Initialize vector store
        self._init_vectorstore()
    
    def _init_vectorstore(self):
        """Initialize or connect to Qdrant vectorstore."""
        
        try:
            # Determine embedding dimensions based on model
            # text-embedding-3-small: 1536 dims
            # text-embedding-3-large: 3072 dims
            dimension = 3072 if "large" in self.embedding_model else 1536
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
                )
                logger.info(
                    f"Created Qdrant collection: {self.collection_name} "
                    f"(dimension={dimension})"
                )
            else:
                logger.info(f"Connected to existing collection: {self.collection_name}")
            
            # Also ensure global cache collection exists
            if self.cache_collection not in collection_names:
                self.client.create_collection(
                    collection_name=self.cache_collection,
                    vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
                )
                logger.info(f"Created global cache collection: {self.cache_collection}")
            
            # Initialize LangChain Qdrant vector store
            self.vectorstore = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.embeddings
            )
            
            logger.info(f"Qdrant vector store initialized: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant vector store: {e}")
            raise RuntimeError(f"Failed to initialize vector store: {e}")
    
    def ingest_documents(self, parsed_documents: List[Any]) -> Dict[str, Any]:
        """
        Ingest parsed documents into the vector store.
        
        Args:
            parsed_documents: List of ParsedDocument objects
            
        Returns:
            Dictionary with ingestion statistics
        """
        if not parsed_documents:
            logger.warning("No documents provided for ingestion")
            return {"chunks_created": 0, "chunks_added": 0}
        
        logger.info(f"Ingesting {len(parsed_documents)} document(s) into Qdrant...")
        
        try:
            # Convert to LangChain Document objects and split
            all_chunks = []
            point_ids = []
            
            for doc in parsed_documents:
                # Check if document has pre-chunked data (from Docling HybridChunker)
                if doc.metadata.get("chunks") and doc.metadata.get("chunker") == "HybridChunker":
                    # Use pre-chunked data from Docling
                    logger.info(
                        f"  - {doc.file_name}: Using {doc.metadata['num_chunks']} "
                        f"pre-chunked segments from HybridChunker"
                    )
                    
                    for chunk_data in doc.metadata["chunks"]:
                        # Create LangChain Document from pre-chunked data
                        chunk_doc = Document(
                            page_content=chunk_data["content"],
                            metadata={
                                "source": doc.file_name,
                                "file_path": doc.file_path,
                                "parser": doc.parser_used,
                                "chunker": "HybridChunker",
                                "session_id": self.session_id,
                                **chunk_data.get("metadata", {})
                            }
                        )
                        all_chunks.append(chunk_doc)
                    
                else:
                    # Fall back to text splitter for documents without pre-chunked data
                    logger.info(
                        f"  - {doc.file_name}: Chunking with RecursiveCharacterTextSplitter "
                        f"({len(doc.text_content)} chars, parser={doc.parser_used})"
                    )
                    
                    langchain_doc = Document(
                        page_content=doc.text_content,
                        metadata={
                            "source": doc.file_name,
                            "file_path": doc.file_path,
                            "parser": doc.parser_used,
                            "session_id": self.session_id,
                            **doc.metadata
                        }
                    )
                    
                    # Split into chunks
                    chunks = self.text_splitter.split_documents([langchain_doc])
                    all_chunks.extend(chunks)
                    
                    logger.info(f"    → Created {len(chunks)} chunks")
            
            logger.info(f"Total chunks created: {len(all_chunks)}")
            
            # Add documents to vector store and get IDs
            ids = self.vectorstore.add_documents(all_chunks)
            
            logger.info(f"Successfully added {len(all_chunks)} chunks to Qdrant")
            
            return {
                "documents_processed": len(parsed_documents),
                "chunks_created": len(all_chunks),
                "chunks_added": len(all_chunks),
                "collection_name": self.collection_name,
                "point_ids": ids if ids else []
            }
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise RuntimeError(f"Failed to ingest documents: {e}")
    
    def copy_cached_embeddings(
        self,
        file_hash: str,
        cache_manager: Any,
        target_collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Copy embeddings from global cache to session collection.
        
        Args:
            file_hash: SHA256 hash of the cached file
            cache_manager: EmbeddingCacheManager instance
            target_collection: Target collection name (defaults to session collection)
            
        Returns:
            Statistics about the copy operation
        """
        target_collection = target_collection or self.collection_name
        
        try:
            # Get cached document info
            cached_info = cache_manager.get_cached_document_info(file_hash)
            if not cached_info:
                raise ValueError(f"No cached info found for hash {file_hash[:16]}")
            
            cached_point_ids = cached_info.get("qdrant_point_ids", [])
            source_collection = cached_info.get("qdrant_collection", self.cache_collection)
            
            if not cached_point_ids:
                logger.warning(f"No point IDs found in cache for hash {file_hash[:16]}")
                return {"points_copied": 0}
            
            logger.info(
                f"Copying {len(cached_point_ids)} cached embeddings from "
                f"{source_collection} to {target_collection}"
            )
            
            # Retrieve points from cache collection
            points = self.client.retrieve(
                collection_name=source_collection,
                ids=cached_point_ids,
                with_payload=True,
                with_vectors=True
            )
            
            # Copy points to target collection with new IDs
            new_points = []
            for point in points:
                # Update metadata to reflect new session
                payload = point.payload
                payload["session_id"] = self.session_id
                
                # Create new point with new UUID
                new_point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=point.vector,
                    payload=payload
                )
                new_points.append(new_point)
            
            # Upsert to target collection
            self.client.upsert(
                collection_name=target_collection,
                points=new_points
            )
            
            logger.info(f"Successfully copied {len(new_points)} points to {target_collection}")
            
            return {
                "points_copied": len(new_points),
                "source_collection": source_collection,
                "target_collection": target_collection
            }
            
        except Exception as e:
            logger.error(f"Failed to copy cached embeddings: {e}")
            return {"points_copied": 0, "error": str(e)}
    
    def query(
        self,
        query_text: str,
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store for relevant context.
        
        Args:
            query_text: Search query
            k: Number of results to return
            score_threshold: Minimum relevance score (0.0-1.0)
            
        Returns:
            List of relevant document chunks with metadata
        """
        if not query_text or not query_text.strip():
            logger.warning("Empty query provided")
            return []
        
        try:
            logger.info(f"Querying Qdrant: '{query_text[:100]}...' (k={k}, threshold={score_threshold})")
            
            # Use similarity search with score
            if score_threshold > 0:
                results = self.vectorstore.similarity_search_with_relevance_scores(
                    query_text,
                    k=k
                )
                # Filter by threshold
                filtered_results = [
                    (doc, score) for doc, score in results if score >= score_threshold
                ]
                logger.info(
                    f"Found {len(filtered_results)} results above threshold {score_threshold}"
                )
            else:
                docs = self.vectorstore.similarity_search(query_text, k=k)
                filtered_results = [(doc, 1.0) for doc in docs]
                logger.info(f"Found {len(filtered_results)} results")
            
            # Format results
            formatted_results = []
            for doc, score in filtered_results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return []
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Retrieve all documents from the collection.
        
        Returns:
            List of all points in the collection
        """
        try:
            # Scroll through all points
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            points = scroll_result[0]
            logger.info(f"Retrieved {len(points)} documents from collection")
            
            return [{"id": str(p.id), "payload": p.payload} for p in points]
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            stats = {
                "collection_name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "embedding_model": self.embedding_model,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "qdrant_url": self.qdrant_url
            }
            
            logger.info(f"Collection stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "collection_name": self.collection_name,
                "error": str(e)
            }
    
    def delete_collection(self):
        """Delete the session collection."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    def get_collection_name(self) -> str:
        """Get the current collection name."""
        return self.collection_name
    
    def collection_exists(self) -> bool:
        """Check if the collection exists."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            return self.collection_name in collection_names
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False

