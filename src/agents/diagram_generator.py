"""
Diagram Generator Agent

Generates visual diagrams from project plans using Kroki.io (FREE, no API key required).

Supports multiple diagram types:
- Gantt charts (timeline/milestones)
- Dependency graphs (task relationships)
- BPMN (business process workflows)
- Sequence diagrams (interaction flows)
- ERD (entity-relationship diagrams)
- Component diagrams (system architecture)
- Flowcharts (decision flows)
"""

import httpx
import asyncio
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import base64
import json
import logging

from src.config.llm_config import model

logger = logging.getLogger(__name__)


class DiagramType(Enum):
    """Supported diagram types with their rendering engines."""
    GANTT = ("mermaid", "Timeline/Gantt chart")
    GRAPH = ("graphviz", "Dependency graph")
    BPMN = ("bpmn", "Workflow diagram")
    SEQUENCE = ("plantuml", "Sequence diagram")
    ERD = ("plantuml", "Data model (ERD)")
    COMPONENT = ("plantuml", "Architecture/Component diagram")
    FLOWCHART = ("mermaid", "Flowchart")


class DiagramSpec(BaseModel):
    """Specification for a single diagram."""
    type: str = Field(description="Diagram type (gantt, graph, bpmn, etc.)")
    title: str = Field(description="Diagram title")
    source_code: str = Field(description="Diagram DSL source code")
    description: str = Field(description="Brief description of what the diagram shows")
    engine: str = Field(description="Rendering engine (mermaid, plantuml, graphviz, etc.)")


class GeneratedDiagram(BaseModel):
    """A generated diagram with its data URL."""
    type: str
    title: str
    description: str
    url: str  # Data URL (base64 encoded SVG)
    source_code: str  # Original DSL for debugging


class DiagramGenerator:
    """
    Generate visual diagrams from project plans using Kroki.io.
    
    Kroki.io is a FREE public service that converts text descriptions (PlantUML, Mermaid, 
    Graphviz, etc.) into diagrams. No API key required!
    """
    
    def __init__(self, llm=None, kroki_url: str = "https://kroki.io"):
        """
        Initialize the diagram generator.
        
        Args:
            llm: Language model for analyzing plans and generating DSL
            kroki_url: Kroki.io instance URL (default: public instance)
        """
        self.llm = llm or model
        self.kroki_url = kroki_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def analyze_plan(self, plan_text: str, diagram_types: List[str] = None) -> List[DiagramSpec]:
        """
        Analyze a project plan and identify opportunities for visual diagrams.
        
        Args:
            plan_text: The full project plan text
            diagram_types: Specific diagram types to generate (None = auto-detect)
            
        Returns:
            List of DiagramSpec objects ready for rendering
        """
        logger.info(f"Analyzing plan for diagrams (length: {len(plan_text)} chars)")
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(plan_text, diagram_types)
        
        try:
            # Get LLM response
            response = await self.llm.ainvoke(prompt)
            response_text = str(response.content) if response.content else ""
            
            # Parse JSON response
            diagram_specs = self._parse_diagram_specs(response_text)
            
            logger.info(f"Generated {len(diagram_specs)} diagram specifications")
            return diagram_specs
            
        except Exception as e:
            logger.error(f"Error analyzing plan for diagrams: {e}")
            return []
    
    def _build_analysis_prompt(self, plan_text: str, diagram_types: List[str] = None) -> str:
        """Build the prompt for diagram analysis."""
        
        available_types = """
1. **gantt** (Mermaid) - for project timelines, milestones, phases, schedules
2. **graph** (Graphviz) - for task dependencies, relationships, hierarchies
3. **bpmn** - for business process workflows, approval flows
4. **sequence** (PlantUML) - for interaction flows, API calls, user journeys
5. **erd** (PlantUML) - for data models, database schemas
6. **component** (PlantUML) - for system architecture, microservices, modules
7. **flowchart** (Mermaid) - for decision trees, algorithm flows
"""
        
        type_filter = ""
        if diagram_types:
            type_filter = f"\n**Focus on these diagram types**: {', '.join(diagram_types)}\n"
        
        return f"""Analyze this project plan and generate visual diagrams to enhance understanding.

For each diagrammable section, generate the appropriate diagram DSL code.

**Available diagram types:**
{available_types}
{type_filter}

**Project Plan:**
```
{plan_text[:15000]}  # Truncate if too long
```

**Instructions:**
1. Identify 2-4 key sections that would benefit from visualization
2. Choose the most appropriate diagram type for each
3. Generate syntactically correct DSL code for each diagram
4. Provide a clear title and description

**Output Format (JSON):**
```json
[
  {{
    "type": "gantt",
    "title": "Project Timeline",
    "engine": "mermaid",
    "source_code": "gantt\\n    title Project Timeline\\n    dateFormat YYYY-MM-DD\\n    section Phase 1\\n    Task 1: 2024-01-01, 30d",
    "description": "Shows 4 phases over 9 months with key milestones"
  }},
  {{
    "type": "graph",
    "title": "Module Dependencies",
    "engine": "graphviz",
    "source_code": "digraph G {{\\n  A -> B;\\n  B -> C;\\n}}",
    "description": "Dependencies between system modules"
  }}
]
```

Generate the JSON array now (no other text):"""
    
    def _parse_diagram_specs(self, response_text: str) -> List[DiagramSpec]:
        """Parse LLM response into DiagramSpec objects."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if json_text.startswith("```"):
                lines = json_text.split("\n")
                json_text = "\n".join(lines[1:-1]) if len(lines) > 2 else json_text
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            
            json_text = json_text.strip()
            
            # Parse JSON
            specs_data = json.loads(json_text)
            
            # Convert to DiagramSpec objects
            specs = []
            for spec_data in specs_data:
                try:
                    spec = DiagramSpec(**spec_data)
                    specs.append(spec)
                except Exception as e:
                    logger.warning(f"Failed to parse diagram spec: {e}")
                    continue
            
            return specs
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse diagram specs JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error parsing diagram specs: {e}")
            return []
    
    async def generate_diagram(self, spec: DiagramSpec, format: str = "svg") -> Optional[str]:
        """
        Generate a diagram using Kroki.io.
        
        Args:
            spec: Diagram specification
            format: Output format (svg, png, pdf)
            
        Returns:
            Data URL (base64 encoded) or None if generation fails
        """
        try:
            # Build Kroki URL
            url = f"{self.kroki_url}/{spec.engine}/{format}"
            
            logger.info(f"Generating {spec.type} diagram: {spec.title}")
            
            # Make POST request with diagram source
            response = await self.client.post(
                url,
                content=spec.source_code.encode('utf-8'),
                headers={"Content-Type": "text/plain; charset=utf-8"}
            )
            
            response.raise_for_status()
            
            # Encode as data URL
            content = response.content
            encoded = base64.b64encode(content).decode('utf-8')
            data_url = f"data:image/{format};base64,{encoded}"
            
            logger.info(f"Successfully generated {spec.type} diagram ({len(content)} bytes)")
            return data_url
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Kroki.io HTTP error for {spec.type}: {e.response.status_code}")
            logger.error(f"Response: {e.response.text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Error generating diagram {spec.type}: {e}")
            return None
    
    async def generate_all_diagrams(
        self,
        plan_text: str,
        diagram_types: List[str] = None,
        format: str = "svg"
    ) -> List[GeneratedDiagram]:
        """
        Analyze plan and generate all identified diagrams.
        
        Args:
            plan_text: The full project plan
            diagram_types: Specific types to generate (None = auto-detect)
            format: Output format (svg, png)
            
        Returns:
            List of GeneratedDiagram objects
        """
        # Step 1: Analyze plan and generate specs
        specs = await self.analyze_plan(plan_text, diagram_types)
        
        if not specs:
            logger.warning("No diagrams identified in plan")
            return []
        
        # Step 2: Generate diagrams in parallel
        tasks = [self.generate_diagram(spec, format) for spec in specs]
        urls = await asyncio.gather(*tasks)
        
        # Step 3: Build result objects
        generated_diagrams = []
        for spec, url in zip(specs, urls):
            if url:  # Only include successful generations
                generated_diagrams.append(GeneratedDiagram(
                    type=spec.type,
                    title=spec.title,
                    description=spec.description,
                    url=url,
                    source_code=spec.source_code
                ))
        
        logger.info(f"Successfully generated {len(generated_diagrams)}/{len(specs)} diagrams")
        return generated_diagrams
    
    def embed_in_markdown(self, plan: str, diagrams: List[GeneratedDiagram]) -> str:
        """
        Insert generated diagrams into the plan markdown.
        
        Args:
            plan: Original plan text
            diagrams: Generated diagrams to embed
            
        Returns:
            Enhanced plan with embedded diagrams
        """
        if not diagrams:
            return plan
        
        # Create diagrams section
        diagrams_section = "\n\n---\n\n## 📊 Visual Diagrams\n\n"
        diagrams_section += "*Auto-generated visual representations of the project plan*\n\n"
        
        for diagram in diagrams:
            diagrams_section += f"### {diagram.title}\n\n"
            diagrams_section += f"*{diagram.description}*\n\n"
            diagrams_section += f"![{diagram.title}]({diagram.url})\n\n"
            
            # Add collapsible source code (for debugging)
            diagrams_section += f"<details>\n<summary>View diagram source</summary>\n\n"
            diagrams_section += f"```{diagram.type}\n{diagram.source_code}\n```\n\n"
            diagrams_section += "</details>\n\n"
        
        # Insert before "## Summary" or at end
        if "## Summary" in plan:
            enhanced = plan.replace("## Summary", diagrams_section + "## Summary")
        elif "## Conclusion" in plan:
            enhanced = plan.replace("## Conclusion", diagrams_section + "## Conclusion")
        else:
            enhanced = plan + diagrams_section
        
        return enhanced
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()





