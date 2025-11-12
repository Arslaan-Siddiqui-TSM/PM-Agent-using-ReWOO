"""
Test script to generate feasibility report using latest prompt (v4) with markdown input.
Enables comparison with JSON-based report from session 487da904.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.app.feasibility_agent import generate_feasibility_questions


# Frontend's DEFAULT_TEST_VALUES from DevelopmentProcessStep.jsx
FRONTEND_TEST_DATA = {
    "technologies": "React 18, Node.js 20, PostgreSQL 15, AWS (EC2, S3, RDS). All technologies are readily available and currently used by the team.",
    "technicalExpertise": "Yes, the development team has strong expertise. 3 senior full-stack developers with 5+ years experience, 2 DevOps engineers, and 1 database specialist.",
    "talentAcquisition": "Not required currently, but we have budget to hire 1-2 mid-level developers if workload increases during peak development phases.",
    "systemIntegration": "Excellent integration potential. The system will use REST APIs to connect with existing Salesforce CRM, SAP ERP, and internal authentication service. All APIs are well-documented.",
    "scalability": "Yes, highly scalable. AWS auto-scaling groups configured, database supports horizontal scaling, and architecture follows microservices pattern. Tested to handle 1M+ concurrent users.",
    "technicalRisks": "Moderate risk: dependency on third-party payment gateway API stability, potential performance issues with legacy database migration, new team member onboarding time.",
    "projectCosts": "$650,000 total estimated cost: $400K development (team salaries), $120K cloud infrastructure (AWS), $60K third-party licenses, $40K training, $30K ongoing maintenance first year.",
    "businessBenefits": "Expected $2M annual revenue increase from new customer acquisition, 40% reduction in operational costs ($800K/year savings), 60% faster order processing leading to improved customer satisfaction.",
    "roiPayback": "Projected 180% ROI over 3 years, payback period of 14 months based on cost savings and revenue projections.",
    "budgetConstraints": "Yes, project fits within approved $700K budget for FY2025-2026. Contingency fund of $50K available for unexpected expenses.",
    "financialRisks": "Risk of cost overrun if timeline extends beyond 9 months. Market opportunity window may close if delayed past Q2 2026. Mitigation: phased delivery approach.",
    "dataCompliance": "Fully GDPR compliant with data encryption at rest and in transit, user consent management system, data retention policies, and right-to-delete functionality. CCPA compliant for California users.",
    "industryRegulations": "Must comply with PCI-DSS Level 1 for payment processing, SOC 2 Type II certification planned, and industry-standard security practices.",
    "thirdPartyLicenses": "Using Stripe API (licensed), AWS services (enterprise agreement), open-source libraries (MIT, Apache 2.0 licenses), all properly licensed and compliant. Legal team reviewed.",
    "intellectualProperty": "No known IP conflicts. Patent search completed, trademark clearance obtained, using original code and licensed components only.",
    "contractualIssues": "Data ownership clearly defined in customer agreements. Service Level Agreements (SLAs) established. Vendor contracts reviewed by legal team.",
    "businessAlignment": "Perfect alignment with digital transformation strategy. Directly addresses customer pain points identified in user research, streamlines order fulfillment workflow, and supports business growth goals.",
    "operationalImpact": "Positive impact: automates 70% of manual data entry tasks, reduces order processing time from 2 days to 2 hours, frees up 15 FTEs for higher-value work.",
    "userAdoption": "Very high adoption likelihood. Prototype testing showed 92% user satisfaction, users eager to adopt based on pain points solved. Change management plan in place.",
    "trainingSupportNeeds": "3-day comprehensive training program for all users, video tutorials, interactive documentation, dedicated support hotline, and on-site support team for first 2 weeks post-launch.",
    "internalResources": "Yes, dedicated 4-person operations team allocated: 1 product owner, 2 support specialists, 1 IT infrastructure manager. Budget approved for ongoing support.",
    "completionDate": "Target completion: December 15, 2025. Realistic given 6-month timeline, current team capacity, and well-defined scope. Aggressive but achievable with proper planning.",
    "externalDependencies": "Stripe payment gateway approval (3 weeks), AWS enterprise contract renewal (done), third-party API access credentials (2 weeks), security audit completion (1 month).",
    "timeToMarket": "Critical window: must launch before Q1 2026 to capture holiday shopping data and compete with market leaders. Delay beyond February 2026 risks losing first-mover advantage.",
    "delayImpact": "1-month delay: $150K revenue loss. 3-month delay: competitor launch, potential $500K revenue impact, customer commitment penalties of $100K.",
    "timelineFlexibility": "Limited flexibility. Hard deadline of December 31, 2025 due to fiscal year budget constraints. 2-week buffer built into schedule for unforeseen issues."
}


def load_markdown_files() -> str:
    """Load and concatenate all markdown files from hardcoded session directory."""
    md_dir = Path("data/hardcoded_session/markdown")
    
    if not md_dir.exists():
        raise FileNotFoundError(f"Markdown directory not found: {md_dir}")
    
    md_files = sorted(md_dir.glob("*.md"))
    
    if not md_files:
        raise ValueError(f"No markdown files found in {md_dir}")
    
    print(f"Found {len(md_files)} markdown files:")
    for md_file in md_files:
        print(f"  - {md_file.name}")
    
    # Concatenate all markdown files
    md_content = "\n\n".join([f.read_text(encoding='utf-8') for f in md_files])
    
    print(f"\nTotal markdown content length: {len(md_content)} characters")
    
    return md_content


def main():
    print("=" * 80)
    print("FEASIBILITY REPORT TEST: Latest Prompt (v4) + Markdown Input")
    print("=" * 80)
    print()
    
    # Generate session ID with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"md_test_{timestamp}"
    
    print(f"Session ID: {session_id}")
    print(f"Using frontend default test data for development context")
    print()
    
    # Load markdown files
    print("Loading markdown files...")
    try:
        md_content = load_markdown_files()
        print("[OK] Markdown files loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load markdown files: {e}")
        return 1
    
    print()
    print("-" * 80)
    print("Generating feasibility report...")
    print("  Stage 1 Prompt: thinking_summary.txt")
    print("  Stage 2 Prompt: feasibility_report.txt")
    print("  Input: Markdown text content")
    print("  Development Context: Frontend default values")
    print("-" * 80)
    print()
    
    try:
        # Generate feasibility report with two-stage prompts + markdown input
        result = generate_feasibility_questions(
            document_text=md_content,
            development_context=FRONTEND_TEST_DATA,
            session_id=session_id,
            use_v3=True,  # Use latest two-stage prompt system
            md_file_paths=None  # Force markdown fallback instead of JSON
        )
        
        print()
        print("[OK] Feasibility report generated successfully")
        print()
        
        # Create output directory
        output_dir = Path(f"output/test_md_input_{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save thinking summary
        thinking_path = output_dir / f"thinking_summary_{session_id}.md"
        thinking_path.write_text(result["thinking_summary"], encoding='utf-8')
        print(f"[OK] Thinking summary saved: {thinking_path}")
        
        # Save feasibility report
        report_path = output_dir / f"feasibility_report_{session_id}.md"
        report_path.write_text(result["feasibility_report"], encoding='utf-8')
        print(f"[OK] Feasibility report saved: {report_path}")
        
        print()
        print("=" * 80)
        print("COMPARISON INSTRUCTIONS")
        print("=" * 80)
        print()
        print("Compare the following reports:")
        print()
        print(f"  TEST (Markdown Input):")
        print(f"    {report_path}")
        print()
        print(f"  ORIGINAL (JSON Input):")
        print(f"    output/session_487da904/reports/feasibility_report_487da904_20251107_184101.md")
        print()
        print("Both reports use:")
        print("  - Two-stage prompts (thinking_summary.txt + feasibility_report.txt)")
        print("  - Same development context (frontend defaults)")
        print("  - Same source documents")
        print()
        print("The ONLY difference is the document input format:")
        print("  - TEST: Markdown text content")
        print("  - ORIGINAL: Structured JSON documents")
        print()
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print()
        print(f"[ERROR] Failed to generate feasibility report: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

