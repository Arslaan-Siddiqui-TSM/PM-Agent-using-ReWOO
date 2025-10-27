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
import json

from config.llm_config import model
from langchain_core.messages import HumanMessage
from agents.document_classifier import DocumentClassification


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
    
    def __init__(self, llm=None):
        """Initialize the extractor with an LLM model."""
        self.llm = llm or model
    
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
                
                return "\n\n".join(text_parts)
                
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
        
        # Common instructions for all types
        base_instructions = f"""You are a document analysis expert. Extract structured information from the following document.

**Document Type:** {document_type}
**Filename:** {filename} (for reference only)

Your task is to extract and structure the key information from this document in JSON format.
"""
        
        # Type-specific extraction instructions
        type_specific_instructions = self._get_type_specific_instructions(document_type)
        
        # JSON schema
        json_schema = """{
    "title": "Document title or main heading",
    "summary": "Brief 2-3 sentence summary of the document",
    "key_sections": [
        {"title": "Section name", "content": "Brief summary of section content"}
    ],
    "requirements": [
        {"id": "REQ-001", "description": "Requirement description", "priority": "high/medium/low", "type": "functional/non-functional"}
    ],
    "features": [
        {"name": "Feature name", "description": "Feature description", "priority": "high/medium/low"}
    ],
    "technical_details": {
        "architecture": "Brief architecture description",
        "technology_stack": ["tech1", "tech2"],
        "integrations": ["integration1", "integration2"],
        "data_model": "Brief data model description"
    },
    "test_cases": [
        {"id": "TC-001", "title": "Test case title", "description": "Test description", "type": "unit/integration/e2e"}
    ],
    "use_cases": [
        {"id": "UC-001", "title": "Use case title", "actors": ["actor1"], "description": "Brief description"}
    ],
    "risks": ["Risk 1", "Risk 2"],
    "assumptions": ["Assumption 1", "Assumption 2"],
    "dependencies": ["Dependency 1", "Dependency 2"],
    "constraints": ["Constraint 1", "Constraint 2"],
    "technologies": ["Technology 1", "Technology 2"],
    "stakeholders": ["Stakeholder 1", "Stakeholder 2"],
    "systems": ["System 1", "System 2"],
    "keywords": ["keyword1", "keyword2"],
    "extraction_confidence": 0.9,
    "extraction_notes": ["Note about extraction quality or missing information"]
}"""
        
        full_prompt = f"""{base_instructions}

{type_specific_instructions}

**Document Content:**
```
{document_text}
```

**Expected JSON Output Format:**
{json_schema}

**Important Guidelines:**
1. Extract ONLY information that is explicitly present in the document
2. Use empty arrays [] for sections with no relevant information
3. Be thorough but concise in descriptions
4. For requirements, try to identify IDs if present in the document
5. Set extraction_confidence based on document clarity (0.0 to 1.0)
6. Add extraction_notes if information is ambiguous or missing
7. Include all mentioned technologies, systems, and stakeholders
8. Extract key risks, assumptions, dependencies, and constraints

Provide ONLY the JSON response, no additional text.
"""
        
        return full_prompt
    
    def _get_type_specific_instructions(self, document_type: str) -> str:
        """Get extraction instructions specific to document type."""
        
        instructions = {
            "functional_specification": """
**Focus Areas for Functional Specification:**
- Extract all features and user stories
- Identify business rules and workflows
- Capture user requirements and acceptance criteria
- Note any UI/UX specifications
- Extract functional requirements with priorities
""",
            "technical_specification": """
**Focus Areas for Technical Specification:**
- Extract architecture and system design details
- Identify all technologies, frameworks, and libraries
- Capture API specifications and data models
- Note integration points with external systems
- Extract technical requirements and constraints
- Identify security and performance specifications
""",
            "requirements_document": """
**Focus Areas for Requirements Document:**
- Extract all functional and non-functional requirements
- Identify requirement IDs, priorities, and categories
- Capture acceptance criteria for each requirement
- Note any requirement dependencies
- Extract performance, security, scalability requirements
""",
            "test_plan": """
**Focus Areas for Test Plan:**
- Extract test strategies and approaches
- Identify test cases with IDs and descriptions
- Capture test types (unit, integration, e2e, UAT)
- Note testing tools and frameworks
- Extract quality metrics and acceptance criteria
""",
            "use_case": """
**Focus Areas for Use Case Document:**
- Extract all use cases with IDs and titles
- Identify actors and their roles
- Capture preconditions and postconditions
- Note main flow and alternative flows
- Extract business scenarios
""",
            "architecture_document": """
**Focus Areas for Architecture Document:**
- Extract system architecture and design patterns
- Identify components and their relationships
- Capture deployment architecture
- Note scalability and reliability considerations
- Extract technology decisions and rationale
""",
            "security_document": """
**Focus Areas for Security Document:**
- Extract security requirements and controls
- Identify authentication and authorization mechanisms
- Capture compliance requirements
- Note threat models and risk assessments
- Extract security best practices
""",
            "unknown": """
**Focus Areas for Unknown Document Type:**
- Extract any structured information found
- Identify the apparent purpose of the document
- Capture any requirements, features, or technical details
- Note key topics and themes
- Extract any mentioned stakeholders, systems, or technologies
"""
        }
        
        return instructions.get(document_type, instructions["unknown"])
    
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
