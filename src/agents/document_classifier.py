"""
Document Classifier Agent

This agent analyzes PDF documents and classifies them into predefined categories
without relying on filenames. It uses LLM-based content analysis to determine
document types with confidence scores.
"""

import fitz  # PyMuPDF

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json

from src.config.llm_config import model
from langchain_core.messages import HumanMessage


@dataclass
class DocumentClassification:
    """Represents the classification result for a document."""
    filename: str
    filepath: str
    document_type: str
    confidence: float
    secondary_types: List[Tuple[str, float]]  # Alternative classifications
    key_indicators: List[str]  # Why this classification was chosen
    page_count: int
    extracted_sample: str  # First portion of content used for classification
    

class DocumentClassifierAgent:
    """
    Classifies documents based on content analysis using LLM.
    
    Supported document types:
    - functional_specification
    - technical_specification
    - requirements_document
    - test_plan
    - use_case
    - architecture_document
    - security_document
    - deployment_guide
    - user_manual
    - api_documentation
    - unknown
    """
    
    DOCUMENT_TYPES = [
        "functional_specification",
        "technical_specification",
        "requirements_document",
        "test_plan",
        "use_case",
        "architecture_document",
        "security_document",
        "deployment_guide",
        "user_manual",
        "api_documentation",
        "business_requirements",
        "design_document",
        "SoW (Statement of Work)",
        "unknown"
    ]
    
    # How many pages to analyze for classification
    SAMPLE_PAGES = 3
    # Maximum characters to extract per page
    MAX_CHARS_PER_PAGE = 2000
    
    def __init__(self, llm=None):
        """Initialize the classifier with an LLM model."""
        self.llm = llm or model
        
    def extract_text_sample(self, pdf_path: str) -> Tuple[str, int]:
        """
        Extract a text sample from the first few pages of the PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, total_page_count)
        """
        try:
            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)
                pages_to_read = min(self.SAMPLE_PAGES, total_pages)
                
                text_parts = []
                for page_num in range(pages_to_read):
                    page = doc[page_num]
                    page_text = str(page.get_text("text"))
                    
                    # Truncate if too long
                    if len(page_text) > self.MAX_CHARS_PER_PAGE:
                        page_text = page_text[:self.MAX_CHARS_PER_PAGE] + "..."
                    
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                
                return "\n\n".join(text_parts), total_pages
                
        except Exception as e:
            return f"[Error extracting text: {str(e)}]", 0
    
    def classify_document(self, pdf_path: str, filename: str) -> DocumentClassification:
        """
        Classify a single document based on its content.
        
        Args:
            pdf_path: Path to the PDF file
            filename: Name of the file (for reference only, not used in classification)
            
        Returns:
            DocumentClassification object with classification results
        """
        # Extract text sample
        text_sample, page_count = self.extract_text_sample(pdf_path)
        
        # Build classification prompt
        prompt = self._build_classification_prompt(text_sample, filename)
        
        # Get LLM response
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Parse the response
        classification = self._parse_classification_response(
            str(response.content),
            filename,
            pdf_path,
            page_count,
            text_sample
        )
        
        return classification
    
    def _build_classification_prompt(self, text_sample: str, filename: str) -> str:
        """Build the classification prompt for the LLM."""
        
        document_types_list = "\n".join([f"- {dt}" for dt in self.DOCUMENT_TYPES])
        
        prompt = f"""You are a document classification expert. Analyze the following document excerpt and classify it into one of the predefined document types.

**IMPORTANT**: Base your classification ONLY on the content, structure, and language of the document. 
DO NOT rely on the filename for classification.

**Available Document Types:**
{document_types_list}

**Document Type Definitions:**

1. **functional_specification**: Describes what the system should do from a user/business perspective. Contains features, user stories, workflows, business rules.

2. **technical_specification**: Describes how the system will be built. Contains architecture, technology stack, APIs, data models, integration details.

3. **requirements_document**: Lists requirements (functional and non-functional) in structured format. May contain NFRs like performance, security, scalability requirements.

4. **test_plan**: Describes testing strategy, test cases, test scenarios, QA processes, acceptance criteria.

5. **use_case**: Describes specific scenarios of system usage. Contains actors, preconditions, main flows, alternative flows, postconditions.

6. **architecture_document**: Focuses on system architecture, design patterns, component diagrams, deployment architecture.

7. **security_document**: Focuses on security requirements, threat models, authentication/authorization, compliance, security controls.

8. **deployment_guide**: Instructions for deploying, configuring, and maintaining the system in production.

9. **user_manual**: End-user documentation, how-to guides, user interface descriptions.

10. **api_documentation**: API endpoints, request/response formats, authentication, SDK documentation.

11. **business_requirements**: High-level business goals, objectives, stakeholder requirements, business context.

12. **design_document**: UI/UX design, mockups, design specifications, branding guidelines.

13. **unknown**: Document doesn't clearly fit into any of the above categories.

**Document Excerpt to Classify:**
(Filename provided for reference only: {filename})

```
{text_sample}
```

**Your Task:**
Analyze the content above and provide a classification in the following JSON format:

{{
    "primary_type": "document_type_here",
    "confidence": 0.95,
    "secondary_types": [
        {{"type": "alternative_type_1", "confidence": 0.70}},
        {{"type": "alternative_type_2", "confidence": 0.50}}
    ],
    "key_indicators": [
        "reason 1 for classification",
        "reason 2 for classification",
        "reason 3 for classification"
    ]
}}

**Guidelines:**
- Confidence should be between 0.0 and 1.0
- If confidence is below 0.6, consider using "unknown" as primary type
- Provide 2-3 secondary types if the document has mixed characteristics
- Key indicators should be specific observations from the document content
- Focus on content structure, terminology, and purpose rather than filename

Provide ONLY the JSON response, no additional text.
"""
        return prompt
    
    def _parse_classification_response(
        self,
        response_text: str,
        filename: str,
        filepath: str,
        page_count: int,
        text_sample: str
    ) -> DocumentClassification:
        """Parse the LLM response and create a DocumentClassification object."""
        
        try:
            # Extract JSON from response (in case LLM adds extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                result = json.loads(json_text)
            else:
                raise ValueError("No JSON found in response")
            
            # Parse secondary types
            secondary_types = []
            for item in result.get("secondary_types", []):
                try:
                    conf = float(item["confidence"])
                except (ValueError, TypeError):
                    conf = 0.0
                secondary_types.append((item["type"], conf))
            
            # Ensure primary confidence is a float
            try:
                primary_confidence = float(result["confidence"])
            except (ValueError, TypeError):
                print(f"WARNING: classification confidence is {type(result.get('confidence'))}, using default 0.5")
                primary_confidence = 0.5
            
            return DocumentClassification(
                filename=filename,
                filepath=filepath,
                document_type=result["primary_type"],
                confidence=primary_confidence,
                secondary_types=secondary_types,
                key_indicators=result.get("key_indicators", []),
                page_count=page_count,
                extracted_sample=text_sample[:500] + "..." if len(text_sample) > 500 else text_sample
            )
            
        except Exception as e:
            # Fallback classification if parsing fails
            return DocumentClassification(
                filename=filename,
                filepath=filepath,
                document_type="unknown",
                confidence=0.0,
                secondary_types=[],
                key_indicators=[f"Classification failed: {str(e)}"],
                page_count=page_count,
                extracted_sample=text_sample[:500] + "..." if len(text_sample) > 500 else text_sample
            )
    
    def classify_multiple_documents(
        self,
        pdf_paths: List[str]
    ) -> List[DocumentClassification]:
        """
        Classify multiple documents.
        
        Args:
            pdf_paths: List of paths to PDF files
            
        Returns:
            List of DocumentClassification objects
        """
        classifications = []
        
        for pdf_path in pdf_paths:
            import os
            filename = os.path.basename(pdf_path)
            
            print(f"📄 Classifying: {filename}...")
            classification = self.classify_document(pdf_path, filename)
            classifications.append(classification)
            print(f"   ✓ Type: {classification.document_type} (confidence: {classification.confidence:.2f})")
        
        return classifications
    
    def get_classification_summary(
        self,
        classifications: List[DocumentClassification]
    ) -> Dict:
        """
        Get a summary of all classifications.
        
        Returns:
            Dictionary with summary statistics and grouped documents
        """
        summary = {
            "total_documents": len(classifications),
            "by_type": {},
            "high_confidence": [],  # confidence >= 0.8
            "medium_confidence": [],  # 0.5 <= confidence < 0.8
            "low_confidence": [],  # confidence < 0.5
            "unknown_documents": []
        }
        
        for classification in classifications:
            doc_type = classification.document_type
            
            # Group by type
            if doc_type not in summary["by_type"]:
                summary["by_type"][doc_type] = []
            summary["by_type"][doc_type].append(classification.filename)
            
            # Group by confidence
            if classification.confidence >= 0.8:
                summary["high_confidence"].append(classification.filename)
            elif classification.confidence >= 0.5:
                summary["medium_confidence"].append(classification.filename)
            else:
                summary["low_confidence"].append(classification.filename)
            
            # Track unknown documents
            if doc_type == "unknown":
                summary["unknown_documents"].append(classification.filename)
        
        return summary
    
    def export_classifications_to_json(
        self,
        classifications: List[DocumentClassification],
        output_path: str
    ):
        """Export classifications to a JSON file for caching."""
        data = {
            "classifications": [asdict(c) for c in classifications],
            "summary": self.get_classification_summary(classifications)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_classifications_from_json(
        self,
        input_path: str
    ) -> List[DocumentClassification]:
        """Load classifications from a JSON cache file."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        classifications = []
        for item in data["classifications"]:
            classifications.append(DocumentClassification(**item))
        
        return classifications
