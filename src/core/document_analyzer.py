"""
Document Analyzer

Analyzes multiple documents together to:
- Identify gaps in documentation
- Find conflicts between documents
- Cross-reference information
- Generate confidence scores for planning readiness
- Create comprehensive context for planning
"""

from typing import Dict, List, Set, Any
from dataclasses import dataclass, asdict, field
import json

from src.config.llm_config import model
from langchain_core.messages import HumanMessage
from src.agents.document_classifier import DocumentClassification
from src.agents.content_extractor import ExtractedContent


@dataclass
class DocumentGapAnalysis:
    """Represents gaps in documentation coverage."""
    missing_document_types: List[str] = field(default_factory=list)
    missing_critical_info: List[str] = field(default_factory=list)
    low_coverage_areas: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DocumentConflictAnalysis:
    """Represents conflicts found between documents."""
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    inconsistencies: List[Dict[str, Any]] = field(default_factory=list)
    severity_high: int = 0
    severity_medium: int = 0
    severity_low: int = 0


@dataclass
class DocumentAnalysisReport:
    """Complete analysis report for a document set."""
    
    # Summary statistics
    total_documents: int
    document_types_present: List[str]
    document_types_missing: List[str]
    
    # Coverage analysis
    coverage_score: float  # 0.0 to 1.0
    readiness_for_planning: str  # "high", "medium", "low"
    
    # Gap analysis
    gaps: DocumentGapAnalysis
    
    # Conflict analysis
    conflicts: DocumentConflictAnalysis
    
    # Cross-references
    common_requirements: List[Dict[str, Any]] = field(default_factory=list)
    common_technologies: List[str] = field(default_factory=list)
    common_stakeholders: List[str] = field(default_factory=list)
    
    # Consolidated information
    all_risks: List[Dict[str, str]] = field(default_factory=list)  # {source, risk}
    all_assumptions: List[Dict[str, str]] = field(default_factory=list)
    all_dependencies: List[Dict[str, str]] = field(default_factory=list)
    all_constraints: List[Dict[str, str]] = field(default_factory=list)
    
    # Planning readiness
    confidence_score: float = 0.0
    critical_questions: List[str] = field(default_factory=list)
    
    # Notes
    analysis_notes: List[str] = field(default_factory=list)


class DocumentAnalyzer:
    """
    Analyzes a set of documents to prepare for planning.
    """
    
    # Expected document types for a complete project
    EXPECTED_DOCUMENT_TYPES = [
        "functional_specification",
        "technical_specification",
        "requirements_document",
        "test_plan",
        "use_case"
    ]
    
    # Critical information categories that should be present
    CRITICAL_INFO_CATEGORIES = [
        "functional_requirements",
        "non_functional_requirements",
        "technical_architecture",
        "technology_stack",
        "testing_strategy",
        "user_workflows"
    ]
    
    def __init__(self, llm=None):
        """Initialize the analyzer with an LLM model."""
        self.llm = llm or model
    
    def analyze_documents(
        self,
        classifications: List[DocumentClassification],
        extractions: List[ExtractedContent]
    ) -> DocumentAnalysisReport:
        """
        Perform comprehensive analysis of document set.
        
        Args:
            classifications: List of document classifications
            extractions: List of extracted contents
            
        Returns:
            DocumentAnalysisReport with complete analysis
        """
        
        print("\n🔬 Analyzing document set...")
        
        # Basic statistics
        document_types_present = list(set(c.document_type for c in classifications))
        document_types_missing = [
            dt for dt in self.EXPECTED_DOCUMENT_TYPES
            if dt not in document_types_present
        ]
        
        # Gap analysis
        gaps = self._analyze_gaps(classifications, extractions, document_types_present)
        
        # Conflict analysis
        conflicts = self._analyze_conflicts(extractions)
        
        # Cross-reference analysis
        cross_refs = self._analyze_cross_references(extractions)
        
        # Consolidate information
        consolidated = self._consolidate_information(extractions)
        
        # Calculate coverage and readiness
        coverage_score = self._calculate_coverage_score(
            document_types_present,
            extractions,
            gaps
        )
        
        readiness = self._determine_readiness(coverage_score, gaps, conflicts)
        
        # Generate critical questions for client
        critical_questions = self._generate_critical_questions(
            gaps,
            conflicts,
            document_types_missing
        )
        
        # Calculate overall confidence
        confidence_score = self._calculate_confidence_score(
            coverage_score,
            classifications,
            extractions,
            conflicts
        )
        
        report = DocumentAnalysisReport(
            total_documents=len(classifications),
            document_types_present=document_types_present,
            document_types_missing=document_types_missing,
            coverage_score=coverage_score,
            readiness_for_planning=readiness,
            gaps=gaps,
            conflicts=conflicts,
            common_requirements=cross_refs["common_requirements"],
            common_technologies=cross_refs["common_technologies"],
            common_stakeholders=cross_refs["common_stakeholders"],
            all_risks=consolidated["all_risks"],
            all_assumptions=consolidated["all_assumptions"],
            all_dependencies=consolidated["all_dependencies"],
            all_constraints=consolidated["all_constraints"],
            confidence_score=confidence_score,
            critical_questions=critical_questions,
            analysis_notes=[]
        )
        
        print(f"   ✓ Coverage Score: {coverage_score:.2f}")
        print(f"   ✓ Planning Readiness: {readiness}")
        print(f"   ✓ Confidence Score: {confidence_score:.2f}")
        
        return report
    
    def _analyze_gaps(
        self,
        classifications: List[DocumentClassification],
        extractions: List[ExtractedContent],
        document_types_present: List[str]
    ) -> DocumentGapAnalysis:
        """Identify gaps in documentation."""
        
        missing_types = [
            dt for dt in self.EXPECTED_DOCUMENT_TYPES
            if dt not in document_types_present
        ]
        
        # Check for missing critical information
        missing_critical_info = []
        low_coverage_areas = []
        
        # Check functional requirements coverage
        has_functional_reqs = any(
            len(e.requirements) > 0 or len(e.features) > 0
            for e in extractions
        )
        if not has_functional_reqs:
            missing_critical_info.append("functional_requirements")
            low_coverage_areas.append({
                "area": "Functional Requirements",
                "severity": "high",
                "impact": "Cannot define project scope accurately"
            })
        
        # Check technical specifications
        has_technical_specs = any(
            isinstance(e.technical_details, dict) and 
            (e.technical_details.get("architecture") or e.technical_details.get("technology_stack"))
            for e in extractions
        )
        if not has_technical_specs:
            missing_critical_info.append("technical_architecture")
            low_coverage_areas.append({
                "area": "Technical Architecture",
                "severity": "high",
                "impact": "Cannot design system architecture"
            })
        
        # Check testing strategy
        has_testing = any(len(e.test_cases) > 0 for e in extractions)
        if not has_testing and "test_plan" not in document_types_present:
            missing_critical_info.append("testing_strategy")
            low_coverage_areas.append({
                "area": "Testing Strategy",
                "severity": "medium",
                "impact": "Need to propose testing approach"
            })
        
        # Check user workflows
        has_workflows = any(len(e.use_cases) > 0 for e in extractions)
        if not has_workflows and "use_case" not in document_types_present:
            missing_critical_info.append("user_workflows")
            low_coverage_areas.append({
                "area": "User Workflows",
                "severity": "medium",
                "impact": "Need to infer user journeys"
            })
        
        # Generate recommendations
        recommendations = self._generate_gap_recommendations(
            missing_types,
            missing_critical_info
        )
        
        return DocumentGapAnalysis(
            missing_document_types=missing_types,
            missing_critical_info=missing_critical_info,
            low_coverage_areas=low_coverage_areas,
            recommendations=recommendations
        )
    
    def _generate_gap_recommendations(
        self,
        missing_types: List[str],
        missing_info: List[str]
    ) -> List[str]:
        """Generate recommendations for addressing gaps."""
        
        recommendations = []
        
        if "requirements_document" in missing_types:
            recommendations.append(
                "Request a requirements document to clarify functional and non-functional requirements"
            )
        
        if "technical_specification" in missing_types:
            recommendations.append(
                "Request technical specifications to understand architecture and technology choices"
            )
        
        if "test_plan" in missing_types:
            recommendations.append(
                "Propose a testing strategy based on industry best practices"
            )
        
        if "functional_requirements" in missing_info:
            recommendations.append(
                "Make assumptions about core features based on available documents"
            )
        
        if "technical_architecture" in missing_info:
            recommendations.append(
                "Propose architecture options based on project requirements"
            )
        
        return recommendations
    
    def _analyze_conflicts(
        self,
        extractions: List[ExtractedContent]
    ) -> DocumentConflictAnalysis:
        """Identify conflicts and inconsistencies between documents."""
        
        conflicts = []
        inconsistencies = []
        
        # Check for conflicting technologies
        tech_by_doc = {
            e.filename: set(e.technologies)
            for e in extractions
            if e.technologies
        }
        
        if len(tech_by_doc) > 1:
            all_techs = [tech for techs in tech_by_doc.values() for tech in techs]
            # Look for contradictions (e.g., React and Angular both mentioned)
            conflicting_pairs = [
                ("React", "Angular"),
                ("Vue", "Angular"),
                ("React", "Vue"),
                ("MySQL", "PostgreSQL"),
                ("MongoDB", "PostgreSQL")
            ]
            
            for tech1, tech2 in conflicting_pairs:
                if tech1 in all_techs and tech2 in all_techs:
                    conflicts.append({
                        "type": "technology_conflict",
                        "severity": "high",
                        "description": f"Both {tech1} and {tech2} mentioned across documents",
                        "affected_documents": [
                            doc for doc, techs in tech_by_doc.items()
                            if tech1 in techs or tech2 in techs
                        ]
                    })
        
        # Check for conflicting requirements priorities
        req_conflicts = self._check_requirement_conflicts(extractions)
        
        # Debug: validate req_conflicts structure
        if req_conflicts and not all(isinstance(c, dict) for c in req_conflicts):
            print(f"WARNING: _check_requirement_conflicts returned non-dict items: {type(req_conflicts)}")
            print(f"First few items: {req_conflicts[:3] if len(req_conflicts) > 3 else req_conflicts}")
        
        conflicts.extend(req_conflicts)
        
        # Count by severity
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for conflict in conflicts + inconsistencies:
            # Defensive check: ensure conflict is a dict before calling .get()
            if isinstance(conflict, dict):
                severity = conflict.get("severity", "low")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            else:
                print(f"WARNING: Unexpected conflict type: {type(conflict)} - {conflict}")
                severity_counts["low"] += 1
        
        return DocumentConflictAnalysis(
            conflicts=conflicts,
            inconsistencies=inconsistencies,
            severity_high=severity_counts["high"],
            severity_medium=severity_counts["medium"],
            severity_low=severity_counts["low"]
        )
    
    def _check_requirement_conflicts(
        self,
        extractions: List[ExtractedContent]
    ) -> List[Dict[str, Any]]:
        """Check for conflicting requirements across documents."""
        
        conflicts = []
        
        # Collect all requirements with their sources
        all_requirements = []
        for extraction in extractions:
            for req in extraction.requirements:
                # Defensive check: ensure req is a dict, not a list or other type
                if not isinstance(req, dict):
                    print(f"WARNING: Skipping non-dict requirement from {extraction.filename}: {type(req)} - {req}")
                    continue
                    
                all_requirements.append({
                    "source": extraction.filename,
                    "req": req
                })
        
        # Look for similar requirements with different priorities
        # (Simple heuristic - in production, use more sophisticated matching)
        for i, req1 in enumerate(all_requirements):
            for req2 in all_requirements[i+1:]:
                if (req1["source"] != req2["source"] and
                    req1["req"].get("priority") != req2["req"].get("priority")):
                    
                    desc1 = req1["req"].get("description", "").lower()
                    desc2 = req2["req"].get("description", "").lower()
                    
                    # Simple keyword overlap check
                    words1 = set(desc1.split())
                    words2 = set(desc2.split())
                    overlap = len(words1 & words2) / max(len(words1), len(words2), 1)
                    
                    if overlap > 0.5:  # 50% word overlap suggests similar requirements
                        conflicts.append({
                            "type": "priority_conflict",
                            "severity": "medium",
                            "description": f"Similar requirements have different priorities",
                            "affected_documents": [req1["source"], req2["source"]],
                            "details": {
                                "req1": req1["req"],
                                "req2": req2["req"]
                            }
                        })
        
        return conflicts
    
    def _analyze_cross_references(
        self,
        extractions: List[ExtractedContent]
    ) -> Dict[str, Any]:
        """Find common elements across documents."""
        
        # Technologies mentioned in multiple documents
        tech_counter = {}
        for extraction in extractions:
            for tech in extraction.technologies:
                tech_counter[tech] = tech_counter.get(tech, 0) + 1
        
        common_technologies = [
            tech for tech, count in tech_counter.items()
            if count > 1
        ]
        
        # Stakeholders mentioned in multiple documents
        stakeholder_counter = {}
        for extraction in extractions:
            for stakeholder in extraction.stakeholders:
                stakeholder_counter[stakeholder] = stakeholder_counter.get(stakeholder, 0) + 1
        
        common_stakeholders = [
            stakeholder for stakeholder, count in stakeholder_counter.items()
            if count > 1
        ]
        
        # Requirements that appear in multiple documents
        common_requirements = []
        # (Simplified - in production, use better matching)
        
        return {
            "common_technologies": common_technologies,
            "common_stakeholders": common_stakeholders,
            "common_requirements": common_requirements
        }
    
    def _consolidate_information(
        self,
        extractions: List[ExtractedContent]
    ) -> Dict[str, List[Dict[str, str]]]:
        """Consolidate information from all documents."""
        
        all_risks = []
        all_assumptions = []
        all_dependencies = []
        all_constraints = []
        
        for extraction in extractions:
            for risk in extraction.risks:
                all_risks.append({
                    "source": extraction.filename,
                    "risk": risk
                })
            
            for assumption in extraction.assumptions:
                all_assumptions.append({
                    "source": extraction.filename,
                    "assumption": assumption
                })
            
            for dependency in extraction.dependencies:
                all_dependencies.append({
                    "source": extraction.filename,
                    "dependency": dependency
                })
            
            for constraint in extraction.constraints:
                all_constraints.append({
                    "source": extraction.filename,
                    "constraint": constraint
                })
        
        return {
            "all_risks": all_risks,
            "all_assumptions": all_assumptions,
            "all_dependencies": all_dependencies,
            "all_constraints": all_constraints
        }
    
    def _calculate_coverage_score(
        self,
        document_types_present: List[str],
        extractions: List[ExtractedContent],
        gaps: DocumentGapAnalysis
    ) -> float:
        """Calculate documentation coverage score (0.0 to 1.0)."""
        
        score = 0.0
        
        # Document type coverage (40% weight)
        type_coverage = len(document_types_present) / len(self.EXPECTED_DOCUMENT_TYPES)
        score += type_coverage * 0.4
        
        # Critical information coverage (40% weight)
        missing_critical = len(gaps.missing_critical_info)
        total_critical = len(self.CRITICAL_INFO_CATEGORIES)
        critical_coverage = 1.0 - (missing_critical / total_critical)
        score += critical_coverage * 0.4
        
        # Extraction quality (20% weight)
        avg_extraction_confidence = sum(
            e.extraction_confidence for e in extractions
        ) / max(len(extractions), 1)
        score += avg_extraction_confidence * 0.2
        
        return min(1.0, max(0.0, score))
    
    def _determine_readiness(
        self,
        coverage_score: float,
        gaps: DocumentGapAnalysis,
        conflicts: DocumentConflictAnalysis
    ) -> str:
        """Determine planning readiness level."""
        
        if coverage_score >= 0.8 and conflicts.severity_high == 0:
            return "high"
        elif coverage_score >= 0.5 and conflicts.severity_high <= 1:
            return "medium"
        else:
            return "low"
    
    def _generate_critical_questions(
        self,
        gaps: DocumentGapAnalysis,
        conflicts: DocumentConflictAnalysis,
        missing_types: List[str]
    ) -> List[str]:
        """Generate questions that need client clarification."""
        
        questions = []
        
        # Questions about missing documents
        if "technical_specification" in missing_types:
            questions.append(
                "What is the intended technology stack and architecture for this project?"
            )
        
        if "requirements_document" in missing_types:
            questions.append(
                "Can you provide a detailed list of functional and non-functional requirements?"
            )
        
        # Questions about gaps
        for gap in gaps.low_coverage_areas:
            if gap["severity"] == "high":
                questions.append(
                    f"Critical information missing: {gap['area']}. {gap['impact']}. Can you provide more details?"
                )
        
        # Questions about conflicts
        for conflict in conflicts.conflicts:
            if conflict["severity"] == "high":
                questions.append(
                    f"Conflict found: {conflict['description']}. Which approach should be followed?"
                )
        
        return questions
    
    def _calculate_confidence_score(
        self,
        coverage_score: float,
        classifications: List[DocumentClassification],
        extractions: List[ExtractedContent],
        conflicts: DocumentConflictAnalysis
    ) -> float:
        """Calculate overall confidence score for planning."""
        
        # Average classification confidence
        avg_classification_conf = sum(
            c.confidence for c in classifications
        ) / max(len(classifications), 1)
        
        # Average extraction confidence
        avg_extraction_conf = sum(
            e.extraction_confidence for e in extractions
        ) / max(len(extractions), 1)
        
        # Penalty for conflicts
        conflict_penalty = min(
            0.3,
            (conflicts.severity_high * 0.1 + conflicts.severity_medium * 0.05)
        )
        
        # Weighted average
        confidence = (
            coverage_score * 0.4 +
            avg_classification_conf * 0.2 +
            avg_extraction_conf * 0.2 +
            (1.0 - conflict_penalty) * 0.2
        )
        
        return min(1.0, max(0.0, confidence))
    
    def export_report_to_json(
        self,
        report: DocumentAnalysisReport,
        output_path: str
    ):
        """Export analysis report to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
    
    def export_report_to_markdown(
        self,
        report: DocumentAnalysisReport,
        output_path: str
    ):
        """Export analysis report to Markdown file."""
        
        md_lines = [
            "# Document Analysis Report\n\n",
            "## 📊 Summary\n\n",
            f"- **Total Documents**: {report.total_documents}\n",
            f"- **Coverage Score**: {report.coverage_score:.2%}\n",
            f"- **Planning Readiness**: {report.readiness_for_planning.upper()}\n",
            f"- **Confidence Score**: {report.confidence_score:.2%}\n\n",
            "---\n\n",
            "## 📁 Document Types Present\n\n"
        ]
        
        for doc_type in report.document_types_present:
            md_lines.append(f"- ✅ {doc_type}\n")
        
        if report.document_types_missing:
            md_lines.append("\n### Missing Document Types\n\n")
            for doc_type in report.document_types_missing:
                md_lines.append(f"- ❌ {doc_type}\n")
        
        md_lines.append("\n---\n\n## 🔍 Gap Analysis\n\n")
        
        if report.gaps.missing_critical_info:
            md_lines.append("### Missing Critical Information\n\n")
            for info in report.gaps.missing_critical_info:
                md_lines.append(f"- {info}\n")
            md_lines.append("\n")
        
        if report.gaps.low_coverage_areas:
            md_lines.append("### Low Coverage Areas\n\n")
            for area in report.gaps.low_coverage_areas:
                md_lines.append(f"- **{area['area']}** (Severity: {area['severity']})\n")
                md_lines.append(f"  - Impact: {area['impact']}\n")
            md_lines.append("\n")
        
        if report.gaps.recommendations:
            md_lines.append("### Recommendations\n\n")
            for rec in report.gaps.recommendations:
                md_lines.append(f"- {rec}\n")
            md_lines.append("\n")
        
        md_lines.append("---\n\n## ⚠️ Conflicts and Inconsistencies\n\n")
        md_lines.append(f"- **High Severity**: {report.conflicts.severity_high}\n")
        md_lines.append(f"- **Medium Severity**: {report.conflicts.severity_medium}\n")
        md_lines.append(f"- **Low Severity**: {report.conflicts.severity_low}\n\n")
        
        if report.conflicts.conflicts:
            md_lines.append("### Detected Conflicts\n\n")
            for conflict in report.conflicts.conflicts:
                md_lines.append(f"- **{conflict['type']}** (Severity: {conflict['severity']})\n")
                md_lines.append(f"  - {conflict['description']}\n")
                md_lines.append(f"  - Affected: {', '.join(conflict['affected_documents'])}\n")
            md_lines.append("\n")
        
        md_lines.append("---\n\n## 🔗 Cross-References\n\n")
        
        if report.common_technologies:
            md_lines.append("### Common Technologies\n\n")
            md_lines.append(", ".join(report.common_technologies) + "\n\n")
        
        if report.common_stakeholders:
            md_lines.append("### Common Stakeholders\n\n")
            md_lines.append(", ".join(report.common_stakeholders) + "\n\n")
        
        md_lines.append("---\n\n## 📋 Consolidated Information\n\n")
        
        if report.all_risks:
            md_lines.append("### Risks\n\n")
            for risk in report.all_risks:
                md_lines.append(f"- **[{risk['source']}]** {risk['risk']}\n")
            md_lines.append("\n")
        
        if report.all_dependencies:
            md_lines.append("### Dependencies\n\n")
            for dep in report.all_dependencies:
                md_lines.append(f"- **[{dep['source']}]** {dep['dependency']}\n")
            md_lines.append("\n")
        
        if report.all_constraints:
            md_lines.append("### Constraints\n\n")
            for con in report.all_constraints:
                md_lines.append(f"- **[{con['source']}]** {con['constraint']}\n")
            md_lines.append("\n")
        
        if report.critical_questions:
            md_lines.append("---\n\n## ❓ Critical Questions for Client\n\n")
            for i, question in enumerate(report.critical_questions, 1):
                md_lines.append(f"{i}. {question}\n")
            md_lines.append("\n")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(md_lines)
