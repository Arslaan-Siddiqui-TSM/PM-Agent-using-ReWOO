"""
Simple Docling Parser - All-in-One

Single file that handles:
1. PDF → Markdown parsing using Docling
2. File caching (skip re-parsing same PDFs)
3. Progress logging
4. Error handling

Easy to debug and track issues.
"""

from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import logging
import time
import json
import hashlib
import shutil
from datetime import datetime

# Docling imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    """Simple document representation."""
    file_path: str
    file_name: str
    markdown_content: str
    text_content: str  # Plain text for embedding
    output_md_path: str
    metadata: dict
    parser_used: str = "docling"
    processing_time: float = 0.0
    num_pages: int = 0


class DoclingParser:
    """
    Simple all-in-one Docling parser.
    
    Usage:
        parser = DoclingParser(session_id="abc123")
        docs = parser.parse_pdfs(pdf_paths)
        # MD files saved to: output/session_abc123_DATE/raw/*.md
    """
    
    def __init__(
        self,
        session_id: str,
        output_dir: str = "output",
        ocr_enabled: bool = True,
        table_mode: str = "fast",  # "fast" or "accurate"
        enable_cache: bool = True
    ):
        """
        Initialize parser.
        
        Args:
            session_id: Unique session ID
            output_dir: Base output directory
            ocr_enabled: Enable OCR for scanned documents
            table_mode: "fast" (20-30s/PDF) or "accurate" (45-60s/PDF)
            enable_cache: Skip re-parsing identical PDFs
        """
        self.session_id = session_id
        self.ocr_enabled = ocr_enabled
        self.table_mode = table_mode
        self.enable_cache = enable_cache
        
        # Setup output folders
        date_str = datetime.now().strftime("%Y%m%d")
        self.session_dir = Path(output_dir) / f"session_{session_id[:8]}_{date_str}"
        self.raw_dir = self.session_dir / "raw"
        self.metadata_dir = self.session_dir / "metadata"
        self.cache_dir = Path("data/embedding_cache")
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        if enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Docling converter
        self._init_docling()
        
        # Parsing log
        self.parsing_log = []
        
        logger.info(f"DoclingParser initialized: session={session_id[:8]}, ocr={ocr_enabled}, table_mode={table_mode}")
    
    def _init_docling(self):
        """Initialize Docling DocumentConverter."""
        # Configure table extraction
        table_mode = TableFormerMode.ACCURATE if self.table_mode == "accurate" else TableFormerMode.FAST
        
        # Pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = self.ocr_enabled
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.mode = table_mode
        
        # Create converter
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )
        
        logger.info(f"Docling converter ready: OCR={self.ocr_enabled}, TableMode={self.table_mode}")
    
    def parse_pdfs(self, pdf_paths: List[str], force_reparse: bool = False) -> Dict[str, Any]:
        """
        Parse list of PDFs to markdown files.
        
        Args:
            pdf_paths: List of PDF file paths
            force_reparse: Skip cache and re-parse everything
            
        Returns:
            Dictionary with:
            - parsed_documents: List of ParsedDocument objects
            - cache_hits: Number of cached documents skipped
            - cache_misses: Number of documents parsed
            - parsing_log_path: Path to parsing log JSON
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 Starting Docling Parsing")
        logger.info(f"{'='*80}")
        logger.info(f"📋 Files to parse: {len(pdf_paths)}")
        logger.info(f"⏱️  Estimated time: {len(pdf_paths) * 20} seconds (~{len(pdf_paths) * 20 / 60:.1f} minutes)")
        logger.info(f"{'='*80}\n")
        
        parsed_documents = []
        cache_hits = 0
        cache_misses = 0
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            pdf_name = Path(pdf_path).name
            
            logger.info(f"\n[{i}/{len(pdf_paths)}] Processing: {pdf_name}")
            
            # Check cache
            if self.enable_cache and not force_reparse:
                cached_md = self._check_cache(pdf_path)
                if cached_md:
                    logger.info(f"   ✅ Cache HIT - Reusing existing MD file")
                    cache_hits += 1
                    
                    # Copy cached MD file to new session directory
                    cached_md_path = Path(cached_md)
                    new_md_path = self.raw_dir / cached_md_path.name
                    
                    if cached_md_path.exists():
                        shutil.copy2(cached_md_path, new_md_path)
                        logger.info(f"      Copied to: {new_md_path.name}")
                    else:
                        logger.warning(f"      Cached MD file not found: {cached_md_path}")
                    
                    # Add to log
                    self.parsing_log.append({
                        "file_name": pdf_name,
                        "status": "cached",
                        "cached_from": str(cached_md_path),
                        "copied_to": str(new_md_path),
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
            
            # Parse with Docling
            cache_misses += 1
            try:
                doc = self._parse_one_pdf(pdf_path, i, len(pdf_paths))
                parsed_documents.append(doc)
                
                # Log success
                self.parsing_log.append({
                    "file_name": doc.file_name,
                    "parser_used": "docling",
                    "processing_time": doc.processing_time,
                    "output_md_path": doc.output_md_path,
                    "num_pages": doc.num_pages,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Save to cache
                if self.enable_cache:
                    self._save_to_cache(pdf_path, doc.output_md_path)
                
            except Exception as e:
                logger.error(f"   ❌ FAILED: {str(e)}")
                
                # Log failure
                self.parsing_log.append({
                    "file_name": pdf_name,
                    "error": str(e),
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                })
                
                continue
        
        # Save parsing log
        log_path = self._save_log()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ Parsing Complete!")
        logger.info(f"   • Parsed: {len(parsed_documents)} documents")
        logger.info(f"   • Cached: {cache_hits} documents")
        logger.info(f"   • Total: {len(parsed_documents) + cache_hits}/{len(pdf_paths)}")
        logger.info(f"{'='*80}\n")
        
        return {
            "parsed_documents": parsed_documents,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "parsing_log_path": str(log_path),
            "md_directory": str(self.raw_dir)
        }
    
    def _parse_one_pdf(self, pdf_path: str, index: int, total: int) -> ParsedDocument:
        """Parse a single PDF with Docling."""
        start_time = time.time()
        path = Path(pdf_path)
        
        logger.info(f"   📄 Parsing with Docling...")
        logger.info(f"      OCR: {self.ocr_enabled} | Tables: True | Mode: {self.table_mode}")
        
        try:
            # Convert PDF
            result = self.converter.convert(str(path.absolute()))
            
            # Export to markdown
            markdown_content = result.document.export_to_markdown()
            
            # Get page count
            try:
                num_pages = result.document.num_pages if hasattr(result.document, 'num_pages') else 0
                if callable(num_pages):
                    num_pages = num_pages()
            except:
                num_pages = 0
            
            # Create enhanced markdown with header
            enhanced_markdown = f"""# {path.stem}

**Source:** {path.name}  
**Parser:** Docling DocumentConverter  
**OCR:** {self.ocr_enabled}  
**Table Mode:** {self.table_mode}  
**Pages:** {num_pages}  
**Parsed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{markdown_content}
"""
            
            # Save markdown file
            safe_filename = self._sanitize_filename(path.stem)
            md_path = self.raw_dir / f"{safe_filename}.md"
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_markdown)
            
            processing_time = time.time() - start_time
            
            logger.info(f"   ✅ Done in {processing_time:.1f}s ({num_pages} pages)")
            logger.info(f"      Output: {md_path.name}")
            
            # Extract plain text from markdown for embedding
            text_content = self._markdown_to_text(markdown_content)
            
            return ParsedDocument(
                file_path=str(path.absolute()),
                file_name=path.name,
                markdown_content=enhanced_markdown,
                text_content=text_content,  # For embedding
                output_md_path=str(md_path),
                metadata={
                    "source": path.name,
                    "file_type": "pdf",
                    "parser": "docling",
                    "ocr_enabled": self.ocr_enabled,
                    "table_mode": self.table_mode,
                    "num_pages": num_pages
                },
                processing_time=processing_time,
                num_pages=num_pages
            )
            
        except Exception as e:
            logger.error(f"   ❌ Docling failed: {e}")
            raise Exception(f"Failed to parse '{path.name}': {e}")
    
    def _check_cache(self, pdf_path: str):
        """
        Check if PDF was already parsed (by file hash).
        
        Returns:
            str: Path to cached MD file if found, None otherwise
        """
        file_hash = self._calculate_hash(pdf_path)
        cache_file = self.cache_dir / f"{file_hash}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    md_path = Path(cache_data.get('md_path', ''))
                    if md_path.exists():
                        return str(md_path)  # Return the path, not True
            except:
                pass
        
        return None  # Return None instead of False
    
    def _save_to_cache(self, pdf_path: str, md_path: str):
        """Save parsing result to cache."""
        file_hash = self._calculate_hash(pdf_path)
        cache_file = self.cache_dir / f"{file_hash}.json"
        
        cache_data = {
            "pdf_path": str(pdf_path),
            "md_path": str(md_path),
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
    
    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename for safe use."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:200].strip()
    
    def _markdown_to_text(self, markdown: str) -> str:
        """Convert markdown to plain text for embedding."""
        import re
        
        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', markdown, flags=re.MULTILINE)
        
        # Remove bold/italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        
        # Remove links but keep text
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        return text.strip()
    
    def _save_log(self) -> Path:
        """Save parsing log to JSON."""
        log_path = self.metadata_dir / "parsing_log.json"
        
        log_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "total_documents": len(self.parsing_log),
            "successful": sum(1 for log in self.parsing_log if log.get("status") == "success"),
            "cached": sum(1 for log in self.parsing_log if log.get("status") == "cached"),
            "failed": sum(1 for log in self.parsing_log if log.get("status") == "failed"),
            "documents": self.parsing_log
        }
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info(f"   📝 Log saved: {log_path}")
        
        return log_path

