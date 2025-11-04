from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List


class Session:
    """
    Represents a user session with uploaded documents and processing state.
    
    Attributes:
        session_id: Unique identifier for the session
        created_at: Timestamp when session was created
        document_paths: List of paths to uploaded documents
        development_context: User's development process information (methodology, team size, etc.)
        feasibility_assessment: Generated feasibility assessment text
        feasibility_file_path: Path to saved feasibility assessment file
        pipeline_result: Result from Document Intelligence Pipeline
        use_intelligent_processing: Flag to enable/disable intelligent processing
        
        # RAG/Qdrant fields
        parsed_documents: List of ParsedDocument objects
        parsed_documents_dir: Path to session's parsed markdown folder
        qdrant_manager: QdrantManager instance for this session
        qdrant_collection_name: Name of Qdrant collection
        embedding_cache_stats: Statistics about embedding cache usage
        parsing_log_path: Path to parsing log JSON file
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.document_paths = []
        self.development_context = None
        self.feasibility_assessment = None
        self.feasibility_file_path = None
        self.pipeline_result = None
        self.use_intelligent_processing = True
        
        # RAG/Qdrant fields
        self.parsed_documents: Optional[List[Any]] = None
        self.parsed_documents_dir: Optional[str] = None
        self.qdrant_manager: Optional[Any] = None
        self.qdrant_collection_name: Optional[str] = None
        self.embedding_cache_stats: Optional[Dict[str, Any]] = None
        self.parsing_log_path: Optional[str] = None
    
    def is_expired(self, timeout_minutes=60):
        """Check if session has expired based on timeout."""
        return datetime.now() - self.created_at > timedelta(minutes=timeout_minutes)