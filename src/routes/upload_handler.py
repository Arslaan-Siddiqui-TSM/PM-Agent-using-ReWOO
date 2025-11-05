"""
Upload Handler

Handles file upload logic, validation, and RAG pipeline integration.
"""

from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from datetime import datetime

from fastapi import HTTPException, UploadFile

from src.core.session import Session
from src.core.session_storage import sessions
from src.utils.constants import UPLOAD_DIR


class UploadHandler:
    """
    Handles document upload and processing workflow.
    
    Workflow:
    1. Validate uploaded files or use default files
    2. Save to data/uploads/ (if uploaded)
    3. Create session and store file paths
    4. Trigger RAG pipeline (parse + embed)
    5. Return upload statistics
    """
    
    def __init__(self, enable_rag: bool = True, verbose: bool = False):
        """
        Initialize upload handler.
        
        Args:
            enable_rag: Enable automatic RAG processing
            verbose: Enable verbose console output
        """
        self.enable_rag = enable_rag
        self.verbose = verbose
    
    async def handle_upload(
        self,
        use_default_files: bool = False,
        files: Optional[List[UploadFile]] = None
    ) -> dict:
        """
        Handle file upload and RAG processing.
        
        Args:
            use_default_files: Use default files from data/files/
            files: List of uploaded files
        
        Returns:
            Dictionary with session_id, message, uploaded_files, total_files
        """
        # Create new session
        session_id = str(uuid.uuid4())
        print(f"Created new session: {session_id}")
        session = Session(session_id)
        
        uploaded_files = []
        
        try:
            # Option 1: Use default files from data/files/ directory
            if use_default_files:
                print(f"Using default files from data/files/ directory for session {session_id}")
                files_dir = Path("data/files")
                default_pdf_files = list(files_dir.glob("*.pdf"))
                
                if not default_pdf_files:
                    raise HTTPException(
                        status_code=404,
                        detail="No default PDF files found in data/files/ directory"
                    )
                
                if len(default_pdf_files) > 15:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Too many default files ({len(default_pdf_files)}). Maximum 15 files allowed."
                    )
                
                print(f"Found {len(default_pdf_files)} default PDF files")
                for pdf_path in default_pdf_files:
                    # Use the files directly without copying
                    session.document_paths.append(str(pdf_path.absolute()))
                    uploaded_files.append(pdf_path.name)
                    print(f"Added default file: {pdf_path.name}")
            
            # Option 2: Upload custom files
            else:
                if not files or len(files) == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="No files provided. Either upload files or set use_default_files=true"
                    )
                
                print(f"Upload endpoint called with {len(files)} files")
                
                if len(files) > 15:
                    raise HTTPException(
                        status_code=400,
                        detail="Maximum 15 files allowed per upload"
                    )
                
                print(f"Starting file upload for session {session_id}")
                for file in files:
                    print(f"Processing file: {file.filename}")
                    
                    # Validate file type
                    if not file.filename or not file.filename.lower().endswith('.pdf'):
                        print(f"Invalid file type rejected: {file.filename}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Only PDF files are allowed. Invalid file: {file.filename}"
                        )
                    
                    # Generate unique filename
                    file_id = str(uuid.uuid4())[:8]
                    safe_filename = f"{session_id}_{file_id}_{file.filename}"
                    file_path = UPLOAD_DIR / safe_filename
                    print(f"Saving file to: {file_path}")
                    
                    # Save file
                    with file_path.open("wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    
                    # Store path in session
                    session.document_paths.append(str(file_path))
                    uploaded_files.append(file.filename)
                    print(f"Successfully uploaded: {file.filename}")
            
            # Store session
            sessions[session_id] = session
            print(f"Session {session_id} stored with {len(uploaded_files)} files")
            
            # Process documents SYNCHRONOUSLY - no background thread
            # The upload request will wait until all processing is complete
            if self.enable_rag:
                print(f"\n🚀 Starting SYNCHRONOUS document processing...")
                print(f"   This will take 3-5 minutes - request will wait until complete\n")
                
                # Set status to processing
                session.processing_status = "processing"
                session.status_message = "Processing documents..."
                
                # Process synchronously (blocks until complete)
                self._process_with_rag_sync(session, uploaded_files)
                
                # After processing, check final status
                if session.processing_status == "completed":
                    message = session.status_message
                else:
                    # Processing failed
                    message = f"Processing failed: {session.processing_error or 'Unknown error'}"
            else:
                session.processing_status = "completed"
                message = f"Uploaded {len(uploaded_files)} files. RAG processing disabled."
            
            return {
                "session_id": session_id,
                "message": message,
                "uploaded_files": uploaded_files,
                "total_files": len(uploaded_files),
                "status": session.processing_status
            }
            
        except HTTPException:
            print(f"HTTPException during upload for session {session_id}")
            # Clean up any uploaded files if there's an error
            self._cleanup_files(session)
            raise
            
        except Exception as e:
            print(f"Error during file upload for session {session_id}: {str(e)}")
            # Clean up any uploaded files if there's an error
            self._cleanup_files(session)
            raise HTTPException(
                status_code=500,
                detail=f"Error during file upload: {str(e)}"
            )
    
    def _process_with_rag_sync(self, session: Session, uploaded_files: List[str]) -> None:
        """
        Process documents with clean separation: Parse → Embed → Ready
        Updates session status upon completion or failure.
        
        Workflow:
            1. Parse PDFs → Markdown files (ParsingHandler)
            2. Embed MD files → Qdrant (EmbeddingHandler)
            3. Ready for manual input (feasibility questions)
        
        Args:
            session: Session object
            uploaded_files: List of uploaded file names
        """
        print(f"\n{'='*80}")
        print(f"🚀 Starting Document Processing for session {session.session_id}")
        print(f"{'='*80}\n")
        
        try:
            # ========================================
            # STEP 1: PARSE PDFs → Markdown Files
            # ========================================
            print(f"📄 STEP 1: Parsing {len(session.document_paths)} PDFs to Markdown...")
            print(f"-" * 80)
            
            from src.core.docling_parser import DoclingParser
            
            # Simple all-in-one parser
            parser = DoclingParser(
                session_id=session.session_id,
                output_dir="output",
                ocr_enabled=True,  # OCR for scanned documents
                table_mode="fast",  # Fast mode: 20-30s per PDF
                enable_cache=True  # Skip re-parsing same PDFs
            )
            
            parsing_result = parser.parse_pdfs(
                pdf_paths=session.document_paths,
                force_reparse=False
            )
            
            parsed_documents = parsing_result["parsed_documents"]
            cache_hits = parsing_result["cache_hits"]
            cache_misses = parsing_result["cache_misses"]
            
            print(f"\n✅ Parsing Complete:")
            print(f"   • Parsed: {len(parsed_documents)} documents")
            print(f"   • Cache hits: {cache_hits}")
            print(f"   • Cache misses: {cache_misses}")
            
            # ========================================
            # STEP 1.5: CONVERT Markdown → JSON (LLM-based)
            # ========================================
            # CRITICAL: This runs SYNCHRONOUSLY to ensure JSON files are ready
            # before proceeding to embedding and marking session as complete.
            print(f"\n{'='*80}")
            print(f"📊 STEP 1.5: Converting Markdown to JSON using LLM...")
            print(f"⚠️  This step runs synchronously and blocks until complete.")
            print(f"-" * 80)
            
            from src.config.llm_config import USE_LLM_CONVERTER
            from src.core.llm_md_to_json_converter import convert_markdown_to_json
            
            json_conversion_result = None
            
            if USE_LLM_CONVERTER:
                try:
                    # Get markdown file paths
                    md_file_paths = [doc.output_md_path for doc in parsed_documents]
                    
                    print(f"   Converting {len(md_file_paths)} markdown files to JSON...")
                    
                    # Create JSON output directory
                    date_str = datetime.now().strftime("%Y%m%d")
                    json_dir = f"output/session_{session.session_id[:8]}_{date_str}/json"
                    
                    # SYNCHRONOUS CONVERSION - blocks until all files are converted
                    json_conversion_result = convert_markdown_to_json(
                        md_file_paths=md_file_paths,
                        output_dir=json_dir,
                        verbose=True
                    )
                    
                    print(f"\n✅ JSON Conversion Complete:")
                    print(f"   • Successful: {json_conversion_result['summary']['successful']}")
                    print(f"   • Failed: {json_conversion_result['summary']['failed']}")
                    print(f"   • Output: {json_dir}")
                    
                    # Store in session
                    session.json_documents_dir = json_dir
                    session.json_conversion_log = json_conversion_result
                    
                except Exception as e:
                    print(f"\n⚠️  JSON Conversion Warning: {e}")
                    print(f"   This is not a fatal error - continuing with markdown-only processing...")
                    print(f"   Note: JSON files are optional. Feasibility analysis will work with markdown files.")
                    session.json_documents_dir = None
                    session.json_conversion_log = {"error": str(e), "status": "skipped"}
            else:
                print(f"   ⏭️  LLM converter disabled (USE_LLM_CONVERTER=false)")
                print(f"   Skipping JSON conversion - using markdown files only...")
                session.json_documents_dir = None
                session.json_conversion_log = {"status": "disabled"}
            
            # ========================================
            # STEP 2: EMBED Markdown → Qdrant
            # ========================================
            # NOTE: This step runs SYNCHRONOUSLY after JSON conversion
            # The pipeline is: Parse → JSON → Embed (all in sequence)
            print(f"\n{'='*80}")
            print(f"🧠 STEP 2: Embedding Markdown files to Qdrant...")
            print(f"⚠️  This step runs synchronously - no race conditions!")
            print(f"-" * 80)
            
            from src.core.embedding_handler import EmbeddingHandler
            from src.config.feature_flags import feature_flags
            
            embedding_handler = EmbeddingHandler(
                session_id=session.session_id,
                qdrant_url=feature_flags.qdrant_url,
                embedding_model=(
                    feature_flags.gemini_embedding_model 
                    if feature_flags.embedding_provider == "gemini" 
                    else feature_flags.embedding_model
                ),
                embedding_provider=feature_flags.embedding_provider,
                chunk_size=feature_flags.max_chunk_size,
                chunk_overlap=feature_flags.chunk_overlap,
                verbose=True
            )
            
            embedding_result = embedding_handler.embed_documents(
                parsed_documents=parsed_documents,
                cached_documents_info=[]  # Not needed with new simple parser
            )
            
            qdrant_manager = embedding_result["qdrant_manager"]
            qdrant_stats = embedding_result["qdrant_stats"]
            collection_name = embedding_result["collection_name"]
            
            print(f"\n✅ Embedding Complete:")
            print(f"   • Collection: {collection_name}")
            print(f"   • Chunks created: {qdrant_stats.get('chunks_created', 0)}")
            print(f"   • Chunks added: {qdrant_stats.get('chunks_added', 0)}")
            
            # ========================================
            # STEP 3: Store Results in Session
            # ========================================
            session.parsed_documents = parsed_documents
            session.parsed_documents_dir = parsing_result["md_directory"]
            session.qdrant_manager = qdrant_manager
            session.qdrant_collection_name = collection_name
            session.parsing_log_path = parsing_result["parsing_log_path"]
            
            # Build embedding cache stats for compatibility
            session.embedding_cache_stats = {
                "session_cache_hits": cache_hits,
                "session_cache_misses": cache_misses,
                "total_chunks_created": qdrant_stats.get('chunks_created', 0)
            }
            
            # Update session status to completed
            # CRITICAL: Only set to "completed" after ALL steps are done:
            # - Parsing (PDF → MD)
            # - JSON Conversion (MD → JSON) 
            # - Embedding (MD → Qdrant)
            session.processing_status = "completed"
            
            json_status = ""
            if session.json_documents_dir and session.json_conversion_log:
                successful = session.json_conversion_log.get('summary', {}).get('successful', 0)
                json_status = f"Converted {successful} documents to JSON. "
            
            session.status_message = (
                f"✅ Successfully processed {len(uploaded_files)} files. "
                f"Created {len(parsed_documents)} MD files, "
                f"{json_status}"
                f"{qdrant_stats.get('chunks_added', 0)} embeddings. "
                f"Ready for feasibility questions and plan generation!"
            )
            
            print(f"\n{'='*80}")
            print(f"✅ Processing Complete!")
            print(f"{'='*80}")
            print(f"   Session ID: {session.session_id}")
            print(f"   MD Files: {len(parsed_documents)}")
            print(f"   Embeddings: {qdrant_stats.get('chunks_added', 0)}")
            print(f"   Collection: {collection_name}")
            print(f"   Status: Ready for manual input (feasibility questions)")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"❌ ERROR: Processing failed for session {session.session_id}")
            print(f"{'='*80}")
            print(f"Error: {e}")
            print(f"{'='*80}\n")
            
            import traceback
            traceback.print_exc()
            
            session.processing_status = "failed"
            session.status_message = f"Processing failed: {str(e)}"
            session.processing_error = str(e)
    
    def _cleanup_files(self, session: Session):
        """Clean up uploaded files on error."""
        for doc_path in session.document_paths:
            file_path = Path(doc_path)
            # Only delete files in uploads directory (not default files)
            if file_path.exists() and "data/uploads" in str(file_path):
                try:
                    file_path.unlink()
                    print(f"Cleaned up: {file_path}")
                except Exception as e:
                    print(f"Warning: Could not delete {file_path}: {e}")

