"""
Upload Handler

Handles file upload logic, validation, and document parsing.
"""

from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from datetime import datetime
import threading

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
    4. Parse documents to markdown and JSON
    5. Return upload statistics
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize upload handler.
        
        Args:
            verbose: Enable verbose console output
        """
        self.verbose = verbose
    
    async def handle_upload(
        self,
        use_default_files: bool = False,
        files: Optional[List[UploadFile]] = None
    ) -> dict:
        """
        Handle file upload and document parsing.
        
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
        
        # ============================================================
        # HARDCODED SESSION MODE (Fast path for development/testing)
        # ============================================================
        from src.config.feature_flags import feature_flags
        
        if feature_flags.use_hardcoded_session and use_default_files:
            print("\n" + "="*80)
            print("HARDCODED SESSION MODE ENABLED")
            print("Using pre-processed files")
            print("="*80 + "\n")
            
            try:
                # Create mock ParsedDocument objects
                class MockParsedDoc:
                    def __init__(self, md_path):
                        self.source_pdf = f"data/files/{md_path.stem}.pdf"
                        self.output_md_path = str(md_path)
                
                # Get MD files from hardcoded directory
                md_dir = Path(feature_flags.hardcoded_md_dir)
                md_files = sorted(md_dir.glob("*.md"))
                
                if not md_files:
                    raise Exception(f"No MD files found in {md_dir}")
                
                session.parsed_documents = [MockParsedDoc(md) for md in md_files]
                session.parsed_documents_dir = str(md_dir)
                session.json_documents_dir = feature_flags.hardcoded_json_dir
                
                # Set completed status
                session.processing_status = "completed"
                session.status_message = f"Hardcoded session ready ({len(md_files)} docs)"
                
                # Store session
                sessions[session_id] = session
                
                print(f"Hardcoded session created: {session_id}")
                print(f"  MD files: {len(md_files)}")
                print(f"  JSON dir: {session.json_documents_dir}\n")
                
                return {
                    "session_id": session_id,
                    "message": session.status_message,
                    "uploaded_files": [doc.source_pdf.split('/')[-1] for doc in session.parsed_documents],
                    "total_files": len(session.parsed_documents),
                    "status": "completed"
                }
                
            except Exception as e:
                print(f"Hardcoded session failed: {e}")
                print("Falling back to normal pipeline...\n")
                # Continue to normal pipeline below
        
        # ============================================================
        # NORMAL PIPELINE (Full processing)
        # ============================================================
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
            
            # Process documents SYNCHRONOUSLY (blocking)
            print(f"\n🚀 Starting document processing (parsing only)...")
            print(f"   This will block until complete (30-60 seconds with cache)\n")
            
            # Set status to processing
            session.processing_status = "processing"
            session.status_message = "Processing documents..."
            
            # Process synchronously (BLOCKS until complete)
            self._process_documents_sync(session, uploaded_files)
            
            # After processing completes, check status
            if session.processing_status == "completed":
                message = session.status_message
            else:
                message = f"Processing failed: {session.processing_error or 'Unknown error'}"
            
            # Return after processing completes
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
    
    def _process_documents_sync(self, session: Session, uploaded_files: List[str]) -> None:
        """
        Process documents: Parse → Convert → Ready
        Updates session status upon completion or failure.
        
        Workflow:
            1. Parse PDFs → Markdown files (DoclingParser)
            2. Convert Markdown → JSON (LLM-based)
            3. Ready for feasibility questions and plan generation
        
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
            # before marking session as complete.
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
            # STEP 2: Store Results in Session
            # ========================================
            session.parsed_documents = parsed_documents
            session.parsed_documents_dir = parsing_result["md_directory"]
            session.parsing_log_path = parsing_result["parsing_log_path"]
            
            # Update session status to completed
            # CRITICAL: Only set to "completed" after ALL steps are done:
            # - Parsing (PDF → MD)
            # - JSON Conversion (MD → JSON)
            session.processing_status = "completed"
            
            json_status = ""
            if session.json_documents_dir and session.json_conversion_log:
                successful = session.json_conversion_log.get('summary', {}).get('successful', 0)
                json_status = f"Converted {successful} documents to JSON. "
            
            session.status_message = (
                f"✅ Successfully processed {len(uploaded_files)} files. "
                f"Created {len(parsed_documents)} MD files. "
                f"{json_status}"
                f"Ready for feasibility questions and plan generation!"
            )
            
            print(f"\n{'='*80}")
            print(f"✅ Processing Complete!")
            print(f"{'='*80}")
            print(f"   Session ID: {session.session_id}")
            print(f"   MD Files: {len(parsed_documents)}")
            print(f"   Status: Ready for feasibility questions and plan generation")
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

