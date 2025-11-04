"""
Feature Flags Configuration

Centralized feature toggles for optional enhancements.
All new features are disabled by default (opt-in).
"""

from pydantic_settings import BaseSettings
from typing import Optional


class FeatureFlags(BaseSettings):
    """Feature flags for optional capabilities."""
    
    # Docling configuration (PRIMARY document processor)
    docling_ocr_default: bool = False  # Default OFF for performance
    docling_table_mode: str = "fast"  # "fast" or "accurate"
    docling_export_format: str = "markdown"  # "markdown" or "text"
    
    # Kroki diagram generation (FREE - no API key needed!)
    kroki_url: str = "https://kroki.io"
    enable_diagram_generation: bool = False  # Opt-in feature
    
    # Advanced features (opt-in)
    enable_rag: bool = False  # RAG-powered document querying
    enable_chat: bool = False  # Conversational plan refinement
    enable_validation: bool = False  # Plan validation agent
    
    # Performance settings
    max_file_size_mb: int = 50  # Maximum file size for upload
    parallel_workers: int = 4  # Thread pool size for CPU-bound tasks
    
    # RAG/Embedding configuration (if enabled)
    embedding_model: str = "text-embedding-3-large"  # OpenAI embedding model
    qdrant_url: str = "http://localhost:6333"  # Qdrant server URL
    qdrant_collection_prefix: str = "pm_agent"  # Collection name prefix
    max_chunk_size: int = 1000  # Chunk size for RAG
    chunk_overlap: int = 200  # Overlap between chunks
    
    # Intelligent parsing configuration
    use_intelligent_parsing: bool = True  # Enable intelligent parser routing
    parsing_complexity_threshold: float = 0.3  # Complexity threshold (0.0-1.0)
    force_docling: bool = False  # Force Docling for all docs (debugging)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global instance
feature_flags = FeatureFlags()




