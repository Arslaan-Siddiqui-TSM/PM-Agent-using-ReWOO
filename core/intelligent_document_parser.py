"""
Intelligent Document Parser

Routes PDFs to appropriate parser based on complexity:
- Simple text-only PDFs: PyMuPDF (fast)
- Complex PDFs with images/tables: LangChain Docling (comprehensive)

Saves parsed content as markdown files with proper folder structure.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import logging
import time
import json
from datetime import datetime
from langchain_docling import DoclingLoader
from pathlib import Path
from langchain_docling.loader import ExportType
from docling.chunking import HybridChunker
from config.feature_flags import feature_flags  

logger = logging.getLogger(__name__)

from pathlib import Path
from core.intelligent_document_parser import IntelligentDocumentParser

# Get all PDF files from the folder
files_dir = Path("files")
pdf_files = list(files_dir.glob("*.pdf"))

print(f"Found {len(pdf_files)} PDF files:")
for pdf in pdf_files:
    print(f"  - {pdf.name}")

# Parse all files
parser = IntelligentDocumentParser(session_id="my_session")
parsed_docs = parser.parse_batch([str(p) for p in pdf_files])

print(f"\n✅ Parsed {len(parsed_docs)} documents")
for doc in parsed_docs:
    print(f"  - {doc.file_name}: {doc.parser_used}")
   

@dataclass
class ParsedDocument:
    """Unified document representation."""
    file_path: str
    file_name: str
    text_content: str
    markdown_content: str
    metadata: Dict[str, Any]
    parser_used: str  # "pymupdf" or "docling"
    processing_time: float
    output_md_path: Optional[str] = None


class IntelligentDocumentParser:
    """
    Intelligently routes documents to the appropriate parser.
    Uses latest LangChain Docling for complex documents.
    Saves parsed content as markdown files.
    """
    
    def __init__(
        self,
        session_id: str,
        output_base_dir: str = "parsed_documents",
        complexity_threshold: float = 0.3,
        force_docling: bool = False
    ):
        """
        Initialize the intelligent parser.
        
        Args:
            session_id: Session ID for folder organization
            output_base_dir: Base directory for parsed documents
            complexity_threshold: Threshold for determining complexity (0.0-1.0)
            force_docling: If True, always use Docling
        """
        self.session_id = session_id
        self.complexity_threshold = complexity_threshold
        self.force_docling = force_docling
        
        # Setup output directories with date
        date_str = datetime.now().strftime("%Y%m%d")
        self.session_dir = Path(output_base_dir) / f"session_{session_id[:8]}_{date_str}"
        self.raw_dir = self.session_dir / "raw"
        self.metadata_dir = self.session_dir / "metadata"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Parsing log
        self.parsing_log = []
        
        logger.info(
            f"IntelligentDocumentParser initialized: "
            f"session={session_id[:8]}, threshold={complexity_threshold}, "
            f"force_docling={force_docling}, output_dir={self.session_dir}"
        )
    
    def analyze_pdf_complexity(self, pdf_path: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Analyze PDF to determine if it's complex or simple.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (is_complex: bool, analysis: dict)
        """
        try:
            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)
                has_images = False
                has_tables = False
                image_count = 0
                
                # Sample first 3 pages for analysis
                pages_to_check = min(3, total_pages)
                
                for page_num in range(pages_to_check):
                    page = doc[page_num]
                    
                    # Check for images
                    image_list = page.get_images(full=True)
                    if image_list:
                        has_images = True
                        image_count += len(image_list)
                    
                    # Heuristic for tables: check for many small text blocks
                    text_blocks = page.get_text("blocks")
                    if len(text_blocks) > 20:
                        has_tables = True
                
                # Calculate complexity score
                complexity_score = 0.0
                if has_images:
                    complexity_score += 0.5
                if has_tables:
                    complexity_score += 0.3
                if image_count > 5:
                    complexity_score += 0.2
                
                is_complex = complexity_score >= self.complexity_threshold
                
                analysis = {
                    "total_pages": total_pages,
                    "has_images": has_images,
                    "image_count": image_count,
                    "has_tables": has_tables,
                    "complexity_score": complexity_score,
                    "is_complex": is_complex,
                    "recommended_parser": "docling" if is_complex else "pymupdf"
                }
                
                return is_complex, analysis
                
        except Exception as e:
            logger.warning(f"Error analyzing PDF complexity: {e}. Defaulting to Docling.")
            return True, {"error": str(e), "is_complex": True, "recommended_parser": "docling"}
    
    def parse_with_pymupdf(self, pdf_path: str) -> ParsedDocument:
        """Parse simple PDF with PyMuPDF (fast)."""
        start_time = time.time()
        path = Path(pdf_path)
        
        with fitz.open(pdf_path) as doc:
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text("text"))
            
            text_content = "\n\n".join(text_parts)
            
            # Create markdown representation
            markdown_content = f"""# {path.stem}

**Source:** {path.name}  
**Parser:** PyMuPDF  
**Pages:** {len(doc)}  
**Parsed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{text_content}
"""
            
            # Save markdown file
            safe_filename = self._sanitize_filename(path.stem)
            md_path = self.raw_dir / f"{safe_filename}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            metadata = {
                "source": path.name,
                "file_type": "pdf",
                "parser": "pymupdf",
                "num_pages": len(doc),
                "file_path": str(path.absolute()),
                "md_output_path": str(md_path),
                "parsing_timestamp": datetime.now().isoformat()
            }
            
            processing_time = time.time() - start_time
            
            return ParsedDocument(
                file_path=str(path.absolute()),
                file_name=path.name,
                text_content=text_content,
                markdown_content=markdown_content,
                metadata=metadata,
                parser_used="pymupdf",
                processing_time=processing_time,
                output_md_path=str(md_path)
            )
    
    def parse_with_docling(self, pdf_path: str) -> ParsedDocument:
        """
        Parse complex PDF with LangChain Docling using HybridChunker.
        Uses DOC_CHUNKS export type for optimized chunking.
        """
        start_time = time.time()
        path = Path(pdf_path)
        
        try:
            # Import required modules
            from langchain_docling import DoclingLoader
            from langchain_docling.loader import ExportType
            from docling.chunking import HybridChunker
            from config.feature_flags import feature_flags
            
            logger.info(f"Parsing with Docling HybridChunker: {path.name}")
            
            # Initialize loader with HybridChunker for optimal chunking
            absolute_path = str(path.absolute())
            
            # Use HybridChunker with embedding model tokenizer
            chunker = HybridChunker(
                tokenizer=feature_flags.embedding_model,
                max_tokens=feature_flags.max_chunk_size
            )
            
            loader = DoclingLoader(
                file_path=absolute_path,
                export_type=ExportType.DOC_CHUNKS,  # Pre-chunked documents
                chunker=chunker
            )
            
            # Load and parse document (already chunked)
            docs = loader.load()
            
            # Process document chunks (pre-chunked by HybridChunker)
            if docs:
                logger.info(f"Received {len(docs)} pre-chunked documents from Docling")
                
                # Get markdown content from all chunks
                markdown_parts = [doc.page_content for doc in docs]
                markdown_content = "\n\n---\n\n".join(markdown_parts)
                
                # Extract metadata from first chunk (representative)
                combined_metadata = docs[0].metadata if docs else {}
                
                # Store chunks for later use by Qdrant (already optimally chunked)
                chunks_data = [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in docs
                ]
                
                # Create enhanced markdown with header
                enhanced_markdown = f"""# {path.stem}

**Source:** {path.name}  
**Parser:** LangChain Docling with HybridChunker  
**Chunks:** {len(docs)}  
**Parsed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{markdown_content}
"""
                
                # Save markdown file
                safe_filename = self._sanitize_filename(path.stem)
                md_path = self.raw_dir / f"{safe_filename}.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_markdown)
                
                # Build metadata including chunks
                metadata = {
                    "source": path.name,
                    "file_type": "pdf",
                    "parser": "docling",
                    "chunker": "HybridChunker",
                    "num_chunks": len(docs),
                    "chunks": chunks_data,  # Store pre-chunked data
                    "file_path": str(path.absolute()),
                    "md_output_path": str(md_path),
                    "parsing_timestamp": datetime.now().isoformat(),
                    **combined_metadata
                }
                
                processing_time = time.time() - start_time
                
                # Extract plain text from markdown (for compatibility)
                text_content = self._markdown_to_text(markdown_content)
                
                logger.info(
                    f"Successfully parsed with Docling HybridChunker: '{path.name}' "
                    f"({len(docs)} pre-chunked segments, {processing_time:.2f}s)"
                )
                
                return ParsedDocument(
                    file_path=str(path.absolute()),
                    file_name=path.name,
                    text_content=text_content,
                    markdown_content=enhanced_markdown,
                    metadata=metadata,
                    parser_used="docling",
                    processing_time=processing_time,
                    output_md_path=str(md_path)
                )
            else:
                raise ValueError("Docling returned no documents")
                
        except Exception as e:
            logger.error(f"Docling parsing failed for '{path.name}': {e}")
            raise Exception(f"Failed to parse with Docling: {e}")
    
    def parse_document(self, pdf_path: str) -> ParsedDocument:
        """
        Intelligently parse a document using the appropriate parser.
        Handles errors gracefully with fallback mechanism.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ParsedDocument with extracted content and saved markdown
        """
        path = Path(pdf_path)
        
        # Only PDF files supported
        if path.suffix.lower() != '.pdf':
            raise ValueError(f"Only PDF files supported. Got: {path.suffix}")
        
        # Force Docling if configured
        if self.force_docling:
            logger.info(f"Force Docling mode: Using Docling for '{path.name}'")
            try:
                parsed_doc = self.parse_with_docling(pdf_path)
                return parsed_doc
            except Exception as e:
                logger.error(f"Docling failed (force mode): {e}")
                # Try fallback to PyMuPDF
                logger.info(f"Attempting fallback to PyMuPDF for '{path.name}'")
                try:
                    parsed_doc = self.parse_with_pymupdf(pdf_path)
                    return parsed_doc
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise Exception(f"Both parsers failed for '{path.name}': Primary={e}, Fallback={fallback_error}")
        
        # Analyze complexity
        is_complex, analysis = self.analyze_pdf_complexity(pdf_path)
        
        logger.info(
            f"Document '{path.name}': "
            f"complexity={analysis['complexity_score']:.2f}, "
            f"images={analysis.get('image_count', 0)}, "
            f"parser={analysis['recommended_parser']}"
        )
        
        # Route to appropriate parser with fallback
        if is_complex:
            logger.info(f"Using Docling for complex document: '{path.name}'")
            try:
                parsed_doc = self.parse_with_docling(pdf_path)
            except Exception as e:
                logger.warning(f"Docling failed, trying PyMuPDF fallback: {e}")
                try:
                    parsed_doc = self.parse_with_pymupdf(pdf_path)
                except Exception as fallback_error:
                    raise Exception(f"Both parsers failed: Primary={e}, Fallback={fallback_error}")
        else:
            logger.info(f"Using PyMuPDF for simple document: '{path.name}'")
            try:
                parsed_doc = self.parse_with_pymupdf(pdf_path)
            except Exception as e:
                logger.warning(f"PyMuPDF failed, trying Docling fallback: {e}")
                try:
                    parsed_doc = self.parse_with_docling(pdf_path)
                except Exception as fallback_error:
                    raise Exception(f"Both parsers failed: Primary={e}, Fallback={fallback_error}")
        
        return parsed_doc
    
    def parse_batch(self, pdf_paths: List[str]) -> List[ParsedDocument]:
        """
        Parse multiple documents and save parsing log.
        Continues processing even if some documents fail.
        """
        parsed_docs = []
        
        logger.info(f"Batch parsing {len(pdf_paths)} document(s)...")
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            try:
                doc = self.parse_document(pdf_path)
                parsed_docs.append(doc)
                
                # Log success
                self.parsing_log.append({
                    "file_name": doc.file_name,
                    "parser_used": doc.parser_used,
                    "processing_time": doc.processing_time,
                    "output_md_path": doc.output_md_path,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(
                    f"Completed {i}/{len(pdf_paths)}: {doc.file_name} "
                    f"({doc.parser_used}, {doc.processing_time:.2f}s) → {doc.output_md_path}"
                )
            except Exception as e:
                logger.error(f"Failed to parse {pdf_path}: {e}")
                
                # Log failure
                self.parsing_log.append({
                    "file_name": Path(pdf_path).name,
                    "parser_used": "none",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Write to error log
                self._write_error_log(Path(pdf_path).name, str(e))
                
                # Continue processing other files
                continue
        
        # Save parsing log
        self._save_parsing_log()
        
        logger.info(
            f"Batch parsing complete: {len(parsed_docs)}/{len(pdf_paths)} successful"
        )
        
        return parsed_docs
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system use."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename.strip()
    
    def _markdown_to_text(self, markdown: str) -> str:
        """Convert markdown to plain text (simple version)."""
        import re
        
        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', markdown, flags=re.MULTILINE)
        
        # Remove bold/italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        
        # Remove links but keep text
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        return text.strip()
    
    def _save_parsing_log(self):
        """Save parsing log to JSON file."""
        log_path = self.metadata_dir / "parsing_log.json"
        
        log_data = {
            "session_id": self.session_id,
            "parsing_started": self.parsing_log[0]["timestamp"] if self.parsing_log else None,
            "parsing_completed": datetime.now().isoformat(),
            "total_documents": len(self.parsing_log),
            "successful_parses": sum(1 for log in self.parsing_log if log.get("status") == "success"),
            "failed_parses": sum(1 for log in self.parsing_log if log.get("status") == "failed"),
            "documents": self.parsing_log
        }
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Parsing log saved to: {log_path}")
    
    def _write_error_log(self, filename: str, error_message: str):
        """Write error to persistent error log file."""
        error_log_path = Path("logs") / "parsing_errors.log"
        
        try:
            with open(error_log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR - session_{self.session_id[:8]} - {filename}\n")
                f.write(f"Error: {error_message}\n")
                f.write("-" * 80 + "\n")
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")
    
    def get_parsed_markdown_files(self) -> List[Path]:
        """Get list of all parsed markdown files."""
        return list(self.raw_dir.glob("*.md"))
    
    def get_parsing_summary(self) -> Dict[str, Any]:
        """Get summary of parsing operations."""
        return {
            "session_id": self.session_id,
            "session_dir": str(self.session_dir),
            "raw_dir": str(self.raw_dir),
            "metadata_dir": str(self.metadata_dir),
            "total_parsed": len(self.parsing_log),
            "successful": sum(1 for log in self.parsing_log if log.get("status") == "success"),
            "failed": sum(1 for log in self.parsing_log if log.get("status") == "failed"),
            "markdown_files": [str(p) for p in self.get_parsed_markdown_files()]
        }

