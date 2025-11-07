"""
LLM-based Markdown to JSON Converter

Uses mini LLMs (GPT-4o-mini, Gemini Flash, Claude Haiku) to convert markdown 
documents into enhanced, flexible JSON structures with semantic understanding.

Features:
- Configurable mini model selection for fast, cost-effective conversion
- Flexible schema that adapts to document type
- Semantic extraction of sections, requirements, relationships, metadata
- Not hardcoded - handles any document type intelligently
- Batch processing with progress tracking
- Error handling and fallback mechanisms
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class LLMMarkdownToJsonConverter:
    """
    Converts markdown files to structured JSON using LLM semantic understanding.
    
    The LLM analyzes the markdown and produces a flexible JSON structure that:
    - Identifies document type and purpose
    - Extracts hierarchical sections with semantic meaning
    - Finds tables, lists, and structured data
    - Identifies relationships and dependencies
    - Generates enhanced metadata
    
    The schema is NOT hardcoded - it adapts to the document content.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        verbose: bool = False
    ):
        """
        Initialize converter with configurable LLM.
        
        Args:
            provider: LLM provider ("openai", "gemini", "anthropic")
            model: Model name (e.g., "gpt-4o-mini", "gemini-1.5-flash")
            verbose: Enable detailed logging
        """
        self.provider = provider
        self.model = model
        self.verbose = verbose
        
        # Initialize LLM client
        self._init_llm()
        
        if self.verbose:
            logger.info(f"LLM Converter initialized: {provider}/{model}")
    
    def _init_llm(self):
        """Initialize the LLM client based on provider."""
        from src.config.llm_config import UnifiedLLM
        
        # Don't specify temperature - let the model use its default
        # This avoids compatibility issues with different models
        self.llm = UnifiedLLM(
            provider=self.provider,
            openai_model=self.model if self.provider == "openai" else "gpt-4o-mini",
            gemini_model=self.model if self.provider in ("gemini", "google") else "gemini-1.5-flash",
            nvidia_model=self.model if self.provider == "nvidia" else "qwen3-next-80b-a3b-instruct",
            max_output_tokens=16000  # Allow large JSON output
        )
    
    def _create_conversion_prompt(self, markdown_content: str, filename: str) -> str:
        """
        Create the prompt for LLM to convert markdown to JSON.
        
        This prompt is designed to be flexible and adaptive to any document type.
        """
        prompt = f"""You are a document analysis expert. Convert the following markdown document into a structured JSON format.

**Document Filename:** {filename}

**Instructions:**
1. Analyze the document and infer its type (e.g., Technical Specification, Test Plan, Requirements, etc.)
2. Extract the document structure intelligently - adapt to what's actually in the document
3. Identify and extract:
   - Document metadata (title, type, purpose, key information)
   - Hierarchical sections with their content
   - Tables (with headers and data)
   - Lists (ordered/unordered)
   - Requirements, specifications, or key points
   - Relationships between sections or concepts
   - Any dependencies or references

**Output Format:**
Return ONLY valid JSON (no markdown code blocks, no explanations). Use this flexible structure:

```json
{{
  "document_id": "auto_generated_from_filename",
  "filename": "original_filename",
  "document_type": "inferred_type",
  "metadata": {{
    "title": "extracted_or_inferred_title",
    "purpose": "document_purpose",
    "sections_count": 0,
    "has_tables": true/false,
    "has_requirements": true/false,
    "processing_timestamp": "ISO_timestamp",
    "additional_metadata": {{}}
  }},
  "sections": [
    {{
      "heading": "section_name",
      "level": 1,
      "content": "section_content",
      "subsections": [],
      "extracted_entities": {{
        "requirements": [],
        "specifications": [],
        "key_points": []
      }}
    }}
  ],
  "tables": [
    {{
      "title": "table_title_or_context",
      "headers": ["col1", "col2"],
      "rows": [["data1", "data2"]],
      "metadata": {{}},
    }}
  ],
  "lists": [
    {{
      "type": "ordered|unordered",
      "items": ["item1", "item2"],
      "context": "what_this_list_represents"
    }}
  ],
  "relationships": [
    {{
      "type": "depends_on|references|relates_to",
      "from": "section_or_item",
      "to": "section_or_item",
      "description": "relationship_description"
    }}
  ],
  "summary": {{
    "key_topics": [],
    "main_purpose": "",
    "critical_information": []
  }}
}}
```

**Important:**
- Be flexible - not all documents will have all fields
- Add fields if the document contains other important structured data
- Extract semantic meaning, not just structure
- Identify implicit relationships and dependencies
- Return ONLY the JSON object, nothing else

**Markdown Document:**

{markdown_content}
"""
        return prompt
    
    def convert_file(self, md_file_path: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert a single markdown file to structured JSON using LLM.
        
        Args:
            md_file_path: Path to the markdown file
            document_id: Optional custom document ID
        
        Returns:
            Dictionary with structured document data
        """
        md_path = Path(md_file_path)
        
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {md_file_path}")
        
        # Read file content
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate document ID if not provided
        if not document_id:
            document_id = md_path.stem.lower().replace(' ', '_')
        
        if self.verbose:
            logger.info(f"Converting {md_path.name} to JSON using LLM...")
            logger.info(f"  - Size: {len(content)} chars")
        
        try:
            # Create prompt and invoke LLM
            prompt = self._create_conversion_prompt(content, md_path.name)
            response = self.llm.invoke(prompt)
            
            # Extract JSON from response
            response_text = response.content.strip()
            
            # Clean response - remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            document_json = json.loads(response_text)
            
            # Ensure required fields
            if "document_id" not in document_json:
                document_json["document_id"] = document_id
            if "filename" not in document_json:
                document_json["filename"] = md_path.name
            if "metadata" not in document_json:
                document_json["metadata"] = {}
            
            # Add processing metadata
            if "processing_timestamp" not in document_json.get("metadata", {}):
                document_json["metadata"]["processing_timestamp"] = datetime.now().isoformat()
            
            document_json["metadata"]["source_md_path"] = str(md_file_path)
            document_json["metadata"]["converter"] = f"llm_{self.provider}_{self.model}"
            
            if self.verbose:
                logger.info(f"  ✅ Conversion successful")
                logger.info(f"     Type: {document_json.get('document_type', 'unknown')}")
                logger.info(f"     Sections: {len(document_json.get('sections', []))}")
                logger.info(f"     Tables: {len(document_json.get('tables', []))}")
            
            return document_json
            
        except json.JSONDecodeError as e:
            logger.error(f"  ❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"     Response preview: {response_text[:500]}")
            
            # Fallback: return minimal structure
            return {
                "document_id": document_id,
                "filename": md_path.name,
                "document_type": "unknown",
                "error": f"JSON parsing failed: {str(e)}",
                "metadata": {
                    "processing_timestamp": datetime.now().isoformat(),
                    "converter": f"llm_{self.provider}_{self.model}",
                    "source_md_path": str(md_file_path)
                },
                "raw_response": response_text[:1000]  # Include preview for debugging
            }
            
        except Exception as e:
            logger.error(f"  ❌ Conversion failed: {e}")
            raise
    
    def convert_multiple_files(
        self,
        md_file_paths: List[str],
        output_dir: Optional[str] = None,
        save_json: bool = True
    ) -> Dict[str, Any]:
        """
        Convert multiple markdown files to JSON.
        
        Args:
            md_file_paths: List of paths to markdown files
            output_dir: Directory to save JSON files (if save_json=True)
            save_json: Whether to save individual JSON files
        
        Returns:
            Dictionary with conversion results and statistics
        """
        if self.verbose:
            logger.info(f"\n{'='*80}")
            logger.info(f"🔄 Starting LLM-based MD → JSON conversion")
            logger.info(f"{'='*80}")
            logger.info(f"Files to convert: {len(md_file_paths)}")
            logger.info(f"Model: {self.provider}/{self.model}")
            logger.info(f"{'='*80}\n")
        
        converted_documents = []
        conversion_log = []
        
        # Create output directory if needed
        if save_json and output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        for i, md_path in enumerate(md_file_paths, 1):
            md_file = Path(md_path)
            
            if self.verbose:
                logger.info(f"[{i}/{len(md_file_paths)}] {md_file.name}")
            
            try:
                # Convert file
                doc_id = f"doc_{i:03d}"
                doc_json = self.convert_file(md_path, document_id=doc_id)
                converted_documents.append(doc_json)
                
                # Save individual JSON file
                if save_json and output_dir:
                    json_filename = f"{md_file.stem}.json"
                    json_path = Path(output_dir) / json_filename
                    
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(doc_json, f, indent=2, ensure_ascii=False)
                    
                    if self.verbose:
                        logger.info(f"     Saved: {json_filename}")
                
                # Log success
                conversion_log.append({
                    "filename": md_file.name,
                    "document_id": doc_json.get("document_id"),
                    "document_type": doc_json.get("document_type"),
                    "status": "success",
                    "json_path": str(Path(output_dir) / f"{md_file.stem}.json") if save_json and output_dir else None,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"     Failed: {e}")
                
                # Log failure
                conversion_log.append({
                    "filename": md_file.name,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                continue
        
        # Calculate statistics
        successful = sum(1 for log in conversion_log if log["status"] == "success")
        failed = sum(1 for log in conversion_log if log["status"] == "failed")
        
        result = {
            "documents": converted_documents,
            "conversion_log": conversion_log,
            "summary": {
                "total_files": len(md_file_paths),
                "successful": successful,
                "failed": failed,
                "output_directory": str(output_dir) if output_dir else None,
                "converter_model": f"{self.provider}/{self.model}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        if self.verbose:
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ Conversion Complete")
            logger.info(f"   • Successful: {successful}/{len(md_file_paths)}")
            logger.info(f"   • Failed: {failed}")
            if output_dir:
                logger.info(f"   • Output: {output_dir}")
            logger.info(f"{'='*80}\n")
        
        return result


def convert_markdown_to_json(
    md_file_paths: List[str],
    output_dir: str,
    provider: str = None,
    model: str = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to convert markdown files to JSON using LLM.
    
    Args:
        md_file_paths: List of markdown file paths
        output_dir: Directory to save JSON files
        provider: LLM provider (reads from env if None)
        model: Model name (reads from env if None)
        verbose: Enable verbose logging
    
    Returns:
        Dictionary with conversion results
    """
    # Read configuration from environment if not provided
    if provider is None:
        provider = os.getenv("CONVERTER_PROVIDER", os.getenv("LLM_PROVIDER", "openai"))
    if model is None:
        # Default mini models by provider
        default_models = {
            "openai": "gpt-4o-mini",
            "gemini": "gemini-1.5-flash",
            "google": "gemini-1.5-flash",
            "nvidia": "qwen3-next-80b-a3b-instruct",
            "anthropic": "claude-3-haiku-20240307"
        }
        model = os.getenv("CONVERTER_MODEL", default_models.get(provider, "gpt-4o-mini"))
    
    converter = LLMMarkdownToJsonConverter(
        provider=provider,
        model=model,
        verbose=verbose
    )
    
    result = converter.convert_multiple_files(
        md_file_paths=md_file_paths,
        output_dir=output_dir,
        save_json=True
    )
    
    return result


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python llm_md_to_json_converter.py <output_dir> <md_file1> <md_file2> ...")
        sys.exit(1)
    
    output_directory = sys.argv[1]
    md_files = sys.argv[2:]
    
    print(f"Converting {len(md_files)} markdown files to JSON...")
    print(f"Output directory: {output_directory}")
    
    result = convert_markdown_to_json(
        md_file_paths=md_files,
        output_dir=output_directory,
        verbose=True
    )
    
    print(f"\n✅ Complete: {result['summary']['successful']}/{result['summary']['total_files']} successful")

