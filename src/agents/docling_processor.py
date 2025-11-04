"""
Docling Document Processor Agent

Universal document processor supporting multiple formats using Docling.
Replaces PyMuPDF for faster processing and broader format support.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import time
import logging

# Docling imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

logger = logging.getLogger(__name__)


class DoclingConfig(BaseModel):
    """Configuration for Docling document processing."""
    enable_ocr: bool = Field(default=False, description="Enable OCR for scanned documents/images (slower)")
    table_mode: str = Field(default="fast", description="Table extraction mode: 'fast' or 'accurate'")
    export_format: str = Field(default="markdown", description="Export format: 'markdown' or 'text'")
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    enable_table_extraction: bool = Field(default=True, description="Enable table structure extraction")


class ProcessedDocument(BaseModel):
    """Represents a processed document with extracted content."""
    file_path: str
    file_name: str
    text_content: str
    format: str  # File extension (pdf, docx, pptx, etc.)
    num_pages: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float  # Time taken to process in seconds


class DoclingProcessor:
    """
    Universal document processor using Docling.
    
    Supported formats:
    - PDF (including scanned with OCR)
    - DOCX, PPTX
    - XLSX, XLS, CSV
    - Images (PNG, JPG, JPEG, TIFF, BMP) with OCR
    - HTML, Markdown
    - TXT, AsciiDoc
    """
    
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.csv',
        '.png', '.jpg', '.jpeg', '.tiff', '.bmp',
        '.html', '.htm', '.md', '.txt', '.asciidoc'
    }
    
    def __init__(self, config: DoclingConfig = None):
        """Initialize the Docling processor with configuration."""
        self.config = config or DoclingConfig()
        self.converter = None
        self._setup_converter()
    
    def _setup_converter(self):
        """Set up the Docling document converter with configuration."""
        # Determine table mode
        table_mode = (
            TableFormerMode.ACCURATE 
            if self.config.table_mode == "accurate" 
            else TableFormerMode.FAST
        )
        
        # Configure PDF pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = self.config.enable_ocr
        pipeline_options.do_table_structure = self.config.enable_table_extraction
        
        if self.config.enable_table_extraction:
            pipeline_options.table_structure_options.mode = table_mode
        
        # Initialize DocumentConverter with PDF options
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )
        
        logger.info(
            f"Docling converter initialized: OCR={self.config.enable_ocr}, "
            f"Table={self.config.table_mode}, Format={self.config.export_format}"
        )
    
    def process_document(self, file_path: str) -> ProcessedDocument:
        """
        Process a single document and extract text content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ProcessedDocument with extracted content and metadata
            
        Raises:
            ValueError: If file format is not supported
            Exception: If processing fails
        """
        start_time = time.time()
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Validate file extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise ValueError(
                f"File size ({file_size_mb:.2f} MB) exceeds limit "
                f"({self.config.max_file_size_mb} MB)"
            )
        
        logger.info(f"Processing '{path.name}' with Docling...")
        
        try:
            # Convert document using Docling
            result = self.converter.convert(str(path))
            
            # Export to desired format
            if self.config.export_format == "markdown":
                content = result.document.export_to_markdown()
            else:
                content = result.document.export_to_text()
            
            # Get number of pages (if available)
            num_pages = self._get_num_pages(result.document)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Build metadata
            metadata = {
                "source": path.name,
                "file_type": path.suffix.lower(),
                "parser": "docling",
                "export_format": self.config.export_format,
                "ocr_enabled": self.config.enable_ocr,
                "table_extraction": self.config.enable_table_extraction,
                "file_size_mb": round(file_size_mb, 2)
            }
            
            logger.info(
                f"Successfully processed '{path.name}' ({path.suffix}) "
                f"in {processing_time:.2f}s - {len(content)} chars"
            )
            
            return ProcessedDocument(
                file_path=str(path.absolute()),
                file_name=path.name,
                text_content=content,
                format=path.suffix.lower().lstrip('.'),
                num_pages=num_pages,
                metadata=metadata,
                processing_time=processing_time
            )
            
        except Exception as e:
            error_msg = (
                f"Failed to process '{path.name}' ({path.suffix}). "
                f"Error: {str(e)}\n\n"
                f"Troubleshooting:\n"
                f"- Verify file is not corrupted\n"
                f"- Check format is supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}\n"
                f"- Ensure file permissions are correct\n"
                f"- Confirm Docling dependencies are installed"
            )
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def process_batch(self, file_paths: List[str]) -> List[ProcessedDocument]:
        """
        Process multiple documents sequentially.
        
        Args:
            file_paths: List of paths to document files
            
        Returns:
            List of ProcessedDocument objects
        """
        processed_docs = []
        
        logger.info(f"Batch processing {len(file_paths)} document(s)...")
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                doc = self.process_document(file_path)
                processed_docs.append(doc)
                logger.info(f"Completed {i}/{len(file_paths)}: {doc.file_name}")
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                # Continue processing other files
                continue
        
        logger.info(
            f"Batch processing complete: {len(processed_docs)}/{len(file_paths)} successful"
        )
        
        return processed_docs
    
    def _get_num_pages(self, document) -> int:
        """
        Safely extract number of pages from document.
        
        Args:
            document: Docling document object
            
        Returns:
            Number of pages, or 0 if not available
        """
        try:
            if hasattr(document, "num_pages"):
                num_pages_attr = getattr(document, "num_pages")
                # Check if it's callable (a method)
                num_pages = num_pages_attr() if callable(num_pages_attr) else num_pages_attr
                return int(num_pages) if num_pages else 0
            return 0
        except Exception as e:
            logger.warning(f"Could not determine page count: {e}")
            return 0
    
    def is_supported(self, file_path: str) -> bool:
        """
        Check if a file format is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if supported, False otherwise
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """
        Get list of supported file formats.
        
        Returns:
            Sorted list of supported extensions
        """
        return sorted(cls.SUPPORTED_EXTENSIONS)




