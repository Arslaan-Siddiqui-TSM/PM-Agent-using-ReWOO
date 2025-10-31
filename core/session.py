from datetime import datetime, timedelta


class Session:
    """
    Represents a user session with uploaded documents and processing state.
    
    Attributes:
        session_id: Unique identifier for the session
        created_at: Timestamp when session was created
        document_paths: List of paths to uploaded documents
        pre_feasibility_questions: Strategic questions generated before feasibility assessment
        pre_feasibility_file_path: Path to saved pre-feasibility questions file
        feasibility_assessment: Generated feasibility assessment text
        feasibility_file_path: Path to saved feasibility assessment file
        pipeline_result: Result from Document Intelligence Pipeline
        use_intelligent_processing: Flag to enable/disable intelligent processing
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.document_paths = []
        self.pre_feasibility_questions = None
        self.pre_feasibility_file_path = None
        self.feasibility_assessment = None
        self.feasibility_file_path = None
        self.pipeline_result = None
        self.use_intelligent_processing = True
    
    def is_expired(self, timeout_minutes=60):
        """Check if session has expired based on timeout."""
        return datetime.now() - self.created_at > timedelta(minutes=timeout_minutes)