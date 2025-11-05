import { useState } from "react";
import PropTypes from "prop-types";
import {
  ScopeSection,
  TimelineSection,
  BudgetSection,
  ResourceSection,
  RiskSection,
  QualitySection,
  StakeholderSection,
  ChangeSection,
} from "./";
import "./ProjectSpecForm.css";

const INITIAL_SPEC = {
  // Scope Section
  mustHave: "",
  niceToHave: "",
  doNot: "",

  // Timeline Section
  optimizationPriority: "timeline",
  startDate: "",
  endDate: "",
  numberOfResources: "",

  // Budget Section
  budgetType: "fixBid",
  budgetDescription: "",
  costBreakdown: "",
  totalBudget: "",

  // Resource Section
  resourceFlexibility: "flexible",
  resourceComposition: "",
  resourceSkills: "",

  // Risk Management Section
  riskTolerance: "conservative",
  techUncertainty: "",
  vendorDependency: "",

  // Quality Section
  qualityPriority: "quality",
  protocolsCompliance: "",

  // Stakeholder Section
  stakeholders: "",

  // Change / Adaptation Section
  upskillingNeeds: "",
};

const SAMPLE_SPEC_DATA = {
  // Scope Section
  mustHave:
    "- User authentication and authorization system\n- Product catalog with search and filtering\n- Shopping cart functionality\n- Secure payment gateway integration\n- Order management system\n- Admin dashboard for inventory management\n- Mobile-responsive design",
  niceToHave:
    "- AI-powered product recommendations\n- Real-time inventory updates\n- Multi-language support\n- Customer reviews and ratings system\n- Wishlist functionality\n- Social media integration",
  doNot:
    "- Avoid using deprecated payment APIs\n- No direct database access from frontend\n- Don't implement custom authentication (use OAuth 2.0)\n- Avoid storing sensitive payment information\n- No synchronous blocking operations in checkout flow",

  // Timeline Section
  optimizationPriority: "timeline",
  startDate: "2025-11-15",
  endDate: "2026-05-15",
  numberOfResources: "8",

  // Budget Section
  budgetType: "fixBid",
  budgetDescription:
    "Fixed budget for complete e-commerce platform development including design, development, testing, and deployment. Budget includes cloud infrastructure costs for the first year.",
  costBreakdown:
    "- Development: $300,000\n- Cloud Infrastructure (Year 1): $50,000\n- Third-party licenses (Payment gateway, etc.): $30,000\n- QA and Testing: $70,000\n- Design and UX: $50,000\n- Contingency (10%): $50,000",
  totalBudget: "$550,000",

  // Resource Section
  resourceFlexibility: "flexible",
  resourceComposition:
    "- 3 Full-stack developers (React + Node.js)\n- 2 Backend developers (API development)\n- 1 UI/UX designer\n- 1 QA engineer\n- 1 DevOps engineer\n- 1 Project manager",
  resourceSkills:
    "Required: React, Node.js, PostgreSQL, AWS, RESTful APIs, Git\nPreferred: TypeScript, Docker, CI/CD, Payment gateway integration, Security best practices",

  // Risk Management Section
  riskTolerance: "conservative",
  techUncertainty:
    "Main uncertainties include payment gateway integration complexity and third-party API stability. Mitigation: Early POCs, multiple payment provider options, comprehensive API testing.",
  vendorDependency:
    "Dependencies: Stripe/PayPal for payments, AWS for hosting, SendGrid for emails. Mitigation: Abstraction layers for easy provider switching, SLA monitoring, backup provider identification.",

  // Quality Section
  qualityPriority: "quality",
  protocolsCompliance:
    "- PCI DSS compliance for payment processing\n- GDPR compliance for user data\n- WCAG 2.1 Level AA for accessibility\n- 90%+ code coverage\n- Security audit before launch\n- Performance: <2s page load time\n- 99.9% uptime SLA",

  // Stakeholder Section
  stakeholders:
    "Primary: CEO (final approvals), CTO (technical decisions)\nSecondary: Marketing Director (features), Operations Manager (inventory)\nChannels: Weekly sprint reviews, daily standups, Slack for quick comms, Jira for tracking",

  // Change / Adaptation Section
  upskillingNeeds:
    "- Payment gateway integration training (2 days)\n- AWS security best practices workshop (1 week)\n- React 18 advanced features (3 days)\n- Accessibility testing and compliance (2 days)",
};

export const ProjectSpecForm = ({ onSpecChange }) => {
  const [projectSpec, setProjectSpec] = useState(INITIAL_SPEC);
  const [useTestData, setUseTestData] = useState(false);

  const updateProjectSpec = (field, value) => {
    const updatedSpec = {
      ...projectSpec,
      [field]: value,
    };
    setProjectSpec(updatedSpec);

    // Notify parent component of changes
    if (onSpecChange) {
      onSpecChange(updatedSpec);
    }
  };

  const toggleTestData = () => {
    if (useTestData) {
      // Clear data
      setProjectSpec(INITIAL_SPEC);
      setUseTestData(false);
      if (onSpecChange) {
        onSpecChange(INITIAL_SPEC);
      }
    } else {
      // Fill with sample data
      setProjectSpec(SAMPLE_SPEC_DATA);
      setUseTestData(true);
      if (onSpecChange) {
        onSpecChange(SAMPLE_SPEC_DATA);
      }
    }
  };

  return (
    <div className="project-spec-form">
      <div className="spec-form-header">
        <div className="spec-form-title">
          <h3>Project Specification Form</h3>
          <p className="form-description">
            Define your project requirements, constraints, and priorities to
            generate a tailored project plan.
          </p>
        </div>
        <button
          type="button"
          onClick={toggleTestData}
          className={`test-data-toggle ${useTestData ? "active" : ""}`}
        >
          {useTestData ? "Clear Sample Data" : "Fill Sample Data"}
        </button>
      </div>

      <ScopeSection values={projectSpec} onChange={updateProjectSpec} />
      <TimelineSection values={projectSpec} onChange={updateProjectSpec} />
      <BudgetSection values={projectSpec} onChange={updateProjectSpec} />
      <ResourceSection values={projectSpec} onChange={updateProjectSpec} />
      <RiskSection values={projectSpec} onChange={updateProjectSpec} />
      <QualitySection values={projectSpec} onChange={updateProjectSpec} />
      <StakeholderSection values={projectSpec} onChange={updateProjectSpec} />
      <ChangeSection values={projectSpec} onChange={updateProjectSpec} />
    </div>
  );
};

ProjectSpecForm.propTypes = {
  onSpecChange: PropTypes.func,
};
