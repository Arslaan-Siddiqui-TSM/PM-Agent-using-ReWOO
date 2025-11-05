from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List


class Session:
    """
    Represents a user session with uploaded documents and processing state.
    
    Simplified Pipeline: Upload → Parse to MD → Embed → Feasibility
    
    Attributes:
        session_id: Unique identifier for the session
        created_at: Timestamp when session was created
        document_paths: List of paths to uploaded PDF documents
        development_context: User's development process information from Q&A (methodology, team size, etc.)
        feasibility_assessment: Generated feasibility assessment text
        feasibility_file_path: Path to saved feasibility assessment file
        
        # RAG/Qdrant fields
        parsed_documents: List of ParsedDocument objects (with .output_md_path)
        parsed_documents_dir: Path to session's parsed markdown folder
        json_documents_dir: Path to session's JSON documents folder
        json_conversion_log: Statistics about JSON conversion
        qdrant_manager: QdrantManager instance for this session
        qdrant_collection_name: Name of Qdrant collection
        embedding_cache_stats: Statistics about embedding cache usage
        parsing_log_path: Path to parsing log JSON file
        
        # Background processing status
        processing_status: Status of background parsing/embedding (pending/processing/completed/failed)
        status_message: Human-readable status message
        processing_error: Error message if processing failed
    """
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.created_at: datetime = datetime.now()
        self.document_paths: List[str] = []
        self.development_context: Optional[str] = None
        self.feasibility_assessment: Optional[str] = None
        self.feasibility_file_path: Optional[str] = None
        self.pipeline_result: Optional[Dict[str, Any]] = None
        self.use_intelligent_processing: bool = True
        
        # Processing status fields
        self.processing_status: str = "pending"  # pending/processing/completed/failed
        self.status_message: str = ""
        self.processing_error: Optional[str] = None
        
        # RAG/Qdrant fields
        self.parsed_documents: Optional[List[Any]] = None
        self.parsed_documents_dir: Optional[str] = None
        self.json_documents_dir: Optional[str] = None
        self.json_conversion_log: Optional[Dict[str, Any]] = None
        self.qdrant_manager: Optional[Any] = None
        self.qdrant_collection_name: Optional[str] = None
        self.embedding_cache_stats: Optional[Dict[str, Any]] = None
        self.parsing_log_path: Optional[str] = None
    
    def is_expired(self, timeout_minutes=60):
        """Check if session has expired based on timeout."""
        return datetime.now() - self.created_at > timedelta(minutes=timeout_minutes)