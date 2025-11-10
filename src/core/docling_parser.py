"""
Simple Docling Parser - LangChain Integration

Single file that handles:
1. PDF → Markdown parsing using LangChain Docling
2. File caching (skip re-parsing same PDFs)
3. Progress logging
4. Error handling

Uses LangChain's DoclingLoader with Markdown export for optimal token efficiency.
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

# LangChain Docling imports
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    """Simple document representation."""
    file_path: str
    file_name: str
    markdown_content: str  # Markdown representation from Docling
    output_md_path: str
    metadata: dict
    parser_used: str = "langchain_docling"
    processing_time: float = 0.0
    num_pages: int = 0


class DoclingParser:
    """
    LangChain Docling parser with Markdown export.
    
    Usage:
        parser = DoclingParser(session_id="abc123")
        docs = parser.parse_pdfs(pdf_paths)
        # Markdown files saved to: output/session_abc123_DATE/markdown/*.md
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
        
        # Setup output folders - using markdown instead of json
        date_str = datetime.now().strftime("%Y%m%d")
        self.session_dir = Path(output_dir) / f"session_{session_id[:8]}_{date_str}"
        self.markdown_dir = self.session_dir / "markdown"
        self.metadata_dir = self.session_dir / "metadata"
        self.cache_dir = Path("data/parsing_cache")
        
        # Create directories
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        if enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Parsing log
        self.parsing_log = []
        
        logger.info(f"DoclingParser initialized: session={session_id[:8]}, ocr={ocr_enabled}, table_mode={table_mode}")
    
    def parse_pdfs(self, pdf_paths: List[str], force_reparse: bool = False) -> Dict[str, Any]:
        """
        Parse list of PDFs to Markdown files using LangChain Docling.
        
        Args:
            pdf_paths: List of PDF file paths
            force_reparse: Skip cache and re-parse everything
            
        Returns:
            Dictionary with:
            - parsed_documents: List of ParsedDocument objects
            - cache_hits: Number of cached documents skipped
            - cache_misses: Number of documents parsed
            - parsing_log_path: Path to parsing log JSON
            - markdown_directory: Path to markdown output directory
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 Starting LangChain Docling Parsing (Markdown Export)")
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
                    new_md_path = self.markdown_dir / cached_md_path.name
                    
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
            
            # Parse with LangChain Docling
            cache_misses += 1
            try:
                doc = self._parse_one_pdf(pdf_path, i, len(pdf_paths))
                parsed_documents.append(doc)
                
                # Log success
                self.parsing_log.append({
                    "file_name": doc.file_name,
                    "parser_used": "langchain_docling",
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
        
        # Create consolidated context file
        context_file_path = None
        if parsed_documents:
            context_file_path = self._create_consolidated_context(parsed_documents)
            logger.info(f"✅ Consolidated context file created: {context_file_path}")
        
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
            "markdown_directory": str(self.markdown_dir),
            "context_file_path": context_file_path
        }
    
    def _create_consolidated_context(self, parsed_documents: List[ParsedDocument]) -> str:
        """
        Create a single consolidated requirement_context.md file from all parsed documents.
        
        Returns:
            Path to the created requirement_context.md file
        """
        # Create context directory
        context_dir = self.session_dir / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        
        # Build consolidated content with headers and separators
        consolidated_content = []
        
        for doc in parsed_documents:
            # Add document header
            doc_name = Path(doc.file_name).stem
            consolidated_content.append(f"# Document: {doc_name}\n\n")
            
            # Add the markdown content
            consolidated_content.append(doc.markdown_content)
            
            # Add separator
            consolidated_content.append("\n\n---\n\n")
        
        # Join all content
        full_content = "".join(consolidated_content)
        
        # Save to requirement_context.md
        context_file = context_dir / "requirement_context.md"
        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"Created consolidated context file: {context_file}")
        logger.info(f"Total size: {len(full_content):,} characters from {len(parsed_documents)} documents")
        
        return str(context_file)
    
    def _parse_one_pdf(self, pdf_path: str, index: int, total: int) -> ParsedDocument:
        """Parse a single PDF with LangChain Docling to Markdown."""
        start_time = time.time()
        path = Path(pdf_path)
        
        logger.info(f"   📄 Parsing with LangChain Docling (Markdown export)...")
        logger.info(f"      OCR: {self.ocr_enabled} | Tables: True | Mode: {self.table_mode}")
        
        try:
            # Use LangChain DoclingLoader with Markdown export
            loader = DoclingLoader(
                file_path=str(path.absolute()),
                export_type=ExportType.MARKDOWN
            )
            
            # Load documents (returns list of LangChain Documents)
            documents = loader.load()
            
            if not documents:
                raise Exception("No documents returned from DoclingLoader")
            
            # Get the markdown content from the first document
            markdown_content = documents[0].page_content
            
            # Extract metadata
            doc_metadata = documents[0].metadata if hasattr(documents[0], 'metadata') else {}
            num_pages = doc_metadata.get('total_pages', 0)
            
            # Save Markdown file
            safe_filename = self._sanitize_filename(path.stem)
            md_path = self.markdown_dir / f"{safe_filename}.md"
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            processing_time = time.time() - start_time
            
            logger.info(f"   ✅ Done in {processing_time:.1f}s ({num_pages} pages)")
            logger.info(f"      Output: {md_path.name}")
            logger.info(f"      Size: {len(markdown_content):,} characters")
            
            return ParsedDocument(
                file_path=str(path.absolute()),
                file_name=path.name,
                markdown_content=markdown_content,
                output_md_path=str(md_path),
                metadata={
                    "source": path.name,
                    "file_type": "pdf",
                    "parser": "langchain_docling",
                    "ocr_enabled": self.ocr_enabled,
                    "table_mode": self.table_mode,
                    "num_pages": num_pages,
                    "export_type": "markdown"
                },
                processing_time=processing_time,
                num_pages=num_pages
            )
            
        except Exception as e:
            logger.error(f"   ❌ LangChain Docling failed: {e}")
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
                    
                    # Check for md_path (new format)
                    md_path = cache_data.get('md_path', '')
                    if md_path and md_path != '.':
                        md_path_obj = Path(md_path)
                        if md_path_obj.exists():
                            return str(md_path_obj)
                    
                    # Old JSON format exists - skip and re-parse to MD
                    json_path = cache_data.get('json_path', '')
                    if json_path:
                        logger.info(f"      Old cache format detected (JSON file), will re-parse to MD")
                        return None
                        
            except Exception as e:
                logger.warning(f"      Failed to read cache file: {e}")
                pass
        
        return None
    
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

