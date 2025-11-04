"""
Content Extractor Agent

This agent extracts structured information from documents based on their classified type.
It uses type-specific extraction strategies with a generic fallback for unknown types.
"""

try:
    import fitz  # PyMuPDF
except ImportError:
    import pymupdf as fitz  # Alternative import for newer versions

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
from string import Template
import json
import re

from src.config.llm_config import model
from langchain_core.messages import HumanMessage
from src.agents.document_classifier import DocumentClassification


@dataclass
class ExtractedContent:
    """Represents structured content extracted from a document."""
    filename: str
    document_type: str
    
    # Core extracted elements (common across all types)
    title: Optional[str] = None
    summary: Optional[str] = None
    key_sections: List[Dict[str, str]] = field(default_factory=list)  # [{title, content}]
    
    # Structured extractions (type-specific)
    requirements: List[Dict[str, Any]] = field(default_factory=list)
    features: List[Dict[str, Any]] = field(default_factory=list)
    technical_details: Dict[str, Any] = field(default_factory=dict)
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    use_cases: List[Dict[str, Any]] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    # Entities and keywords
    technologies: List[str] = field(default_factory=list)
    stakeholders: List[str] = field(default_factory=list)
    systems: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Metadata
    extraction_confidence: float = 0.0
    extraction_notes: List[str] = field(default_factory=list)


class ContentExtractorAgent:
    """
    Extracts structured information from documents using LLM-based analysis.
    Adapts extraction strategy based on document type.
    """
    
    # Maximum characters to send to LLM for extraction
    MAX_DOCUMENT_LENGTH = 20000
    PROMPT_FILENAME = "content_extraction_prompt.txt"
    
    def __init__(self, llm=None):
        """Initialize the extractor with an LLM model."""
        self.llm = llm or model
        self._prompt_cache: Optional[str] = None
    
    def _prompt_path(self) -> Path:
        """Get path to external prompt template."""
        # agents/ -> project root -> prompts/content_extraction_prompt.txt
        return Path(__file__).resolve().parents[1] / "prompts" / self.PROMPT_FILENAME
    
    def _load_prompt_template(self) -> str:
        """Load and cache the external prompt template; fallback to minimal inline prompt if missing."""
        if self._prompt_cache is not None:
            return self._prompt_cache
        
        path = self._prompt_path()
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._prompt_cache = f.read()
        except Exception:
            # Minimal fallback to avoid hard failures
            self._prompt_cache = (
                "SYSTEM\nYou are a document analysis assistant.\n\n"
                "DOCUMENT TYPE: $document_type\nFILENAME: $filename\n\n"
                "TEXT\n$document_text\n\n"
                "Output only valid JSON with fields: "
                "title, summary, key_sections, requirements, features, technical_details, "
                "test_cases, use_cases, risks, assumptions, dependencies, constraints, "
                "technologies, stakeholders, systems, keywords, extraction_confidence, extraction_notes."
            )
        return self._prompt_cache
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text to reduce token usage while preserving meaning."""
        # Collapse multiple spaces/tabs to single space
        text = re.sub(r"[ \t]+", " ", text)
        # Limit runs of newlines to max 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip leading/trailing whitespace
        return text.strip()
    
    def extract_full_text(self, pdf_path: str) -> str:
        """Extract full text from PDF, truncated if too long."""
        try:
            with fitz.open(pdf_path) as doc:
                text_parts = []
                total_chars = 0
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text("text")
                    
                    if total_chars + len(page_text) > self.MAX_DOCUMENT_LENGTH:
                        # Truncate and stop
                        remaining = self.MAX_DOCUMENT_LENGTH - total_chars
                        text_parts.append(page_text[:remaining])
                        text_parts.append(f"\n\n[Document truncated - {len(doc) - page_num - 1} pages omitted]")
                        break
                    
                    text_parts.append(page_text)
                    total_chars += len(page_text)
                
                full_text = "\n\n".join(text_parts)
                # Normalize text to reduce token usage
                normalized = self._normalize_text(full_text)
                return normalized if normalized else ""
                
        except Exception as e:
            return f"[Error extracting text: {str(e)}]"
    
    def extract_content(
        self,
        classification: DocumentClassification
    ) -> ExtractedContent:
        """
        Extract structured content from a document based on its type.
        
        Args:
            classification: The document classification result
            
        Returns:
            ExtractedContent object with extracted information
        """
        # Extract full text
        full_text = self.extract_full_text(classification.filepath)
        
        # Choose extraction strategy based on document type
        extraction_prompt = self._build_extraction_prompt(
            full_text,
            classification.document_type,
            classification.filename
        )
        
        # Get LLM response
        response = self.llm.invoke([HumanMessage(content=extraction_prompt)])
        
        # Parse response into structured format
        response_text = str(response.content) if response.content else ""
        extracted_content = self._parse_extraction_response(
            response_text,
            classification
        )
        
        return extracted_content
    
    def _build_extraction_prompt(
        self,
        document_text: str,
        document_type: str,
        filename: str
    ) -> str:
        """Build type-specific extraction prompt."""
        
        # Load external prompt template and substitute placeholders
        template = Template(self._load_prompt_template())
        return template.safe_substitute(
            document_type=document_type,
            filename=filename,
            document_text=document_text
        )
    
    def _parse_extraction_response(
        self,
        response_text: str,
        classification: DocumentClassification
    ) -> ExtractedContent:
        """Parse LLM response into ExtractedContent object."""
        
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                data = json.loads(json_text)
            else:
                raise ValueError("No JSON found in response")
            
            # Create ExtractedContent object
            extracted = ExtractedContent(
                filename=classification.filename,
                document_type=classification.document_type,
                title=data.get("title"),
                summary=data.get("summary"),
                key_sections=data.get("key_sections", []),
                requirements=data.get("requirements", []),
                features=data.get("features", []),
                technical_details=data.get("technical_details", {}),
                test_cases=data.get("test_cases", []),
                use_cases=data.get("use_cases", []),
                risks=data.get("risks", []),
                assumptions=data.get("assumptions", []),
                dependencies=data.get("dependencies", []),
                constraints=data.get("constraints", []),
                technologies=data.get("technologies", []),
                stakeholders=data.get("stakeholders", []),
                systems=data.get("systems", []),
                keywords=data.get("keywords", []),
                extraction_confidence=data.get("extraction_confidence", 0.5),
                extraction_notes=data.get("extraction_notes", [])
            )
            
            return extracted
            
        except Exception as e:
            # Fallback with minimal information
            return ExtractedContent(
                filename=classification.filename,
                document_type=classification.document_type,
                extraction_confidence=0.0,
                extraction_notes=[f"Extraction failed: {str(e)}"]
            )
    
    def extract_multiple_documents(
        self,
        classifications: List[DocumentClassification]
    ) -> List[ExtractedContent]:
        """
        Extract content from multiple documents.
        
        Args:
            classifications: List of document classifications
            
        Returns:
            List of ExtractedContent objects
        """
        extracted_contents = []
        
        for classification in classifications:
            print(f"🔍 Extracting content from: {classification.filename}...")
            extracted = self.extract_content(classification)
            extracted_contents.append(extracted)
            print(f"   ✓ Confidence: {extracted.extraction_confidence:.2f}")
        
        return extracted_contents
    
    def export_extractions_to_json(
        self,
        extractions: List[ExtractedContent],
        output_path: str
    ):
        """Export extracted content to JSON file for caching."""
        data = {
            "extractions": [asdict(e) for e in extractions]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_extractions_from_json(
        self,
        input_path: str
    ) -> List[ExtractedContent]:
        """Load extracted content from JSON cache file."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        extractions = []
        for item in data["extractions"]:
            extractions.append(ExtractedContent(**item))
        
        return extractions
    
    def get_extraction_summary(
        self,
        extractions: List[ExtractedContent]
    ) -> Dict:
        """Generate a summary of all extracted content."""
        summary = {
            "total_documents": len(extractions),
            "total_requirements": sum(len(e.requirements) for e in extractions),
            "total_features": sum(len(e.features) for e in extractions),
            "total_test_cases": sum(len(e.test_cases) for e in extractions),
            "total_use_cases": sum(len(e.use_cases) for e in extractions),
            "all_technologies": list(set(tech for e in extractions for tech in e.technologies)),
            "all_stakeholders": list(set(s for e in extractions for s in e.stakeholders)),
            "all_systems": list(set(sys for e in extractions for sys in e.systems)),
            "high_confidence_extractions": [],
            "low_confidence_extractions": [],
            "documents_with_risks": [],
            "documents_with_dependencies": []
        }
        
        for extraction in extractions:
            if extraction.extraction_confidence >= 0.7:
                summary["high_confidence_extractions"].append(extraction.filename)
            elif extraction.extraction_confidence < 0.5:
                summary["low_confidence_extractions"].append(extraction.filename)
            
            if extraction.risks:
                summary["documents_with_risks"].append(extraction.filename)
            
            if extraction.dependencies:
                summary["documents_with_dependencies"].append(extraction.filename)
        
        return summary
