import { useState } from "react";
import PropTypes from "prop-types";
import { Button } from "../ui";
import "./DevelopmentProcessStep.css";

const INITIAL_ANSWERS = {
  // Technical Feasibility
  technologies: "",
  technicalExpertise: "",
  talentAcquisition: "",
  systemIntegration: "",
  scalability: "",
  technicalRisks: "",

  // Economic Feasibility
  projectCosts: "",
  businessBenefits: "",
  roiPayback: "",
  budgetConstraints: "",
  financialRisks: "",

  // Legal Feasibility
  dataCompliance: "",
  industryRegulations: "",
  thirdPartyLicenses: "",
  intellectualProperty: "",
  contractualIssues: "",

  // Operational Feasibility
  businessAlignment: "",
  operationalImpact: "",
  userAdoption: "",
  trainingSupportNeeds: "",
  internalResources: "",

  // Schedule Feasibility
  completionDate: "",
  externalDependencies: "",
  timeToMarket: "",
  delayImpact: "",
  timelineFlexibility: "",
};

const DEFAULT_TEST_VALUES = {
  // Technical Feasibility
  technologies:
    "React 18, Node.js 20, PostgreSQL 15, AWS (EC2, S3, RDS). All technologies are readily available and currently used by the team.",
  technicalExpertise:
    "Yes, the development team has strong expertise. 3 senior full-stack developers with 5+ years experience, 2 DevOps engineers, and 1 database specialist.",
  talentAcquisition:
    "Not required currently, but we have budget to hire 1-2 mid-level developers if workload increases during peak development phases.",
  systemIntegration:
    "Excellent integration potential. The system will use REST APIs to connect with existing Salesforce CRM, SAP ERP, and internal authentication service. All APIs are well-documented.",
  scalability:
    "Yes, highly scalable. AWS auto-scaling groups configured, database supports horizontal scaling, and architecture follows microservices pattern. Tested to handle 1M+ concurrent users.",
  technicalRisks:
    "Moderate risk: dependency on third-party payment gateway API stability, potential performance issues with legacy database migration, new team member onboarding time.",

  // Economic Feasibility
  projectCosts:
    "$650,000 total estimated cost: $400K development (team salaries), $120K cloud infrastructure (AWS), $60K third-party licenses, $40K training, $30K ongoing maintenance first year.",
  businessBenefits:
    "Expected $2M annual revenue increase from new customer acquisition, 40% reduction in operational costs ($800K/year savings), 60% faster order processing leading to improved customer satisfaction.",
  roiPayback:
    "Projected 180% ROI over 3 years, payback period of 14 months based on cost savings and revenue projections.",
  budgetConstraints:
    "Yes, project fits within approved $700K budget for FY2025-2026. Contingency fund of $50K available for unexpected expenses.",
  financialRisks:
    "Risk of cost overrun if timeline extends beyond 9 months. Market opportunity window may close if delayed past Q2 2026. Mitigation: phased delivery approach.",

  // Legal Feasibility
  dataCompliance:
    "Fully GDPR compliant with data encryption at rest and in transit, user consent management system, data retention policies, and right-to-delete functionality. CCPA compliant for California users.",
  industryRegulations:
    "Must comply with PCI-DSS Level 1 for payment processing, SOC 2 Type II certification planned, and industry-standard security practices.",
  thirdPartyLicenses:
    "Using Stripe API (licensed), AWS services (enterprise agreement), open-source libraries (MIT, Apache 2.0 licenses), all properly licensed and compliant. Legal team reviewed.",
  intellectualProperty:
    "No known IP conflicts. Patent search completed, trademark clearance obtained, using original code and licensed components only.",
  contractualIssues:
    "Data ownership clearly defined in customer agreements. Service Level Agreements (SLAs) established. Vendor contracts reviewed by legal team.",

  // Operational Feasibility
  businessAlignment:
    "Perfect alignment with digital transformation strategy. Directly addresses customer pain points identified in user research, streamlines order fulfillment workflow, and supports business growth goals.",
  operationalImpact:
    "Positive impact: automates 70% of manual data entry tasks, reduces order processing time from 2 days to 2 hours, frees up 15 FTEs for higher-value work.",
  userAdoption:
    "Very high adoption likelihood. Prototype testing showed 92% user satisfaction, users eager to adopt based on pain points solved. Change management plan in place.",
  trainingSupportNeeds:
    "3-day comprehensive training program for all users, video tutorials, interactive documentation, dedicated support hotline, and on-site support team for first 2 weeks post-launch.",
  internalResources:
    "Yes, dedicated 4-person operations team allocated: 1 product owner, 2 support specialists, 1 IT infrastructure manager. Budget approved for ongoing support.",

  // Schedule Feasibility
  completionDate:
    "Target completion: December 15, 2025. Realistic given 6-month timeline, current team capacity, and well-defined scope. Aggressive but achievable with proper planning.",
  externalDependencies:
    "Stripe payment gateway approval (3 weeks), AWS enterprise contract renewal (done), third-party API access credentials (2 weeks), security audit completion (1 month).",
  timeToMarket:
    "Critical window: must launch before Q1 2026 to capture holiday shopping data and compete with market leaders. Delay beyond February 2026 risks losing first-mover advantage.",
  delayImpact:
    "1-month delay: $150K revenue loss. 3-month delay: competitor launch, potential $500K revenue impact, customer commitment penalties of $100K.",
  timelineFlexibility:
    "Limited flexibility. Hard deadline of December 31, 2025 due to fiscal year budget constraints. 2-week buffer built into schedule for unforeseen issues.",
};

export const DevelopmentProcessStep = ({ onSubmit, onError }) => {
  const [devProcessAnswers, setDevProcessAnswers] = useState(INITIAL_ANSWERS);
  const [useTestData, setUseTestData] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();

    const hasAnswers = Object.values(devProcessAnswers).some(
      (val) => val.trim() !== ""
    );

    if (!hasAnswers) {
      onError("Please answer at least one question before continuing");
      return;
    }

    onError(null);
    onSubmit(devProcessAnswers);
  };

  const updateAnswer = (field, value) => {
    setDevProcessAnswers({
      ...devProcessAnswers,
      [field]: value,
    });
  };

  const toggleTestData = () => {
    if (!useTestData) {
      // Fill with test data
      setDevProcessAnswers(DEFAULT_TEST_VALUES);
      setUseTestData(true);
    } else {
      // Clear and reset to empty
      setDevProcessAnswers(INITIAL_ANSWERS);
      setUseTestData(false);
    }
  };

  return (
    <div className="step-container">
      <div className="step-header">
        <div>
          <h2>Step 2: Feasibility Assessment Questions</h2>
          <p>
            Answer these questions to help assess the project's feasibility
            across multiple dimensions.
            <span className="required-note"> * indicates required fields</span>
          </p>
        </div>
        <button
          type="button"
          onClick={toggleTestData}
          className={`test-data-toggle ${useTestData ? "active" : ""}`}
          title={
            useTestData ? "Clear test data" : "Fill with test data for demo"
          }
        >
          {useTestData ? "🗑️ Clear Test Data" : "⚡ Use Test Data"}
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="static-questions-form">
          {/* Technical Feasibility */}
          <div className="question-category">
            <h3 className="category-title">
              Technical Feasibility — "Can we build it?"
            </h3>

            <div className="form-group">
              <label htmlFor="technologies">
                What technologies (languages, frameworks, databases, hardware)
                are required, and are they readily available to the team?{" "}
                <span className="required">*</span>
              </label>
              <textarea
                id="technologies"
                name="technologies"
                value={devProcessAnswers.technologies}
                onChange={(e) => updateAnswer("technologies", e.target.value)}
                placeholder="E.g., React, Node.js, PostgreSQL, AWS - all available to team..."
                className="form-textarea"
                rows={3}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="technicalExpertise">
                Does the development team have the necessary technical expertise
                to implement and maintain the system?{" "}
                <span className="required">*</span>
              </label>
              <textarea
                id="technicalExpertise"
                name="technicalExpertise"
                value={devProcessAnswers.technicalExpertise}
                onChange={(e) =>
                  updateAnswer("technicalExpertise", e.target.value)
                }
                placeholder="E.g., Yes, team has 5+ years experience with required stack..."
                className="form-textarea"
                rows={2}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="talentAcquisition">
                If not, can we acquire or train the required talent within the
                project timeline and budget?{" "}
                <span className="optional">(Optional)</span>
              </label>
              <input
                id="talentAcquisition"
                type="text"
                name="talentAcquisition"
                value={devProcessAnswers.talentAcquisition}
                onChange={(e) =>
                  updateAnswer("talentAcquisition", e.target.value)
                }
                placeholder="E.g., Yes, we plan to hire 2 senior developers..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="systemIntegration">
                How well will the new system integrate with existing tools,
                applications, and infrastructure?{" "}
                <span className="required">*</span>
              </label>
              <textarea
                id="systemIntegration"
                name="systemIntegration"
                value={devProcessAnswers.systemIntegration}
                onChange={(e) =>
                  updateAnswer("systemIntegration", e.target.value)
                }
                placeholder="E.g., Seamless API integration with existing CRM and ERP systems..."
                className="form-textarea"
                rows={2}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="scalability">
                Is the proposed solution scalable to handle expected user growth
                and data volume over time? <span className="required">*</span>
              </label>
              <input
                id="scalability"
                type="text"
                name="scalability"
                value={devProcessAnswers.scalability}
                onChange={(e) => updateAnswer("scalability", e.target.value)}
                placeholder="E.g., Yes, cloud infrastructure can scale to 1M+ users..."
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="technicalRisks">
                Are there any significant technical risks or dependencies that
                could hinder development?{" "}
                <span className="optional">(Optional)</span>
              </label>
              <textarea
                id="technicalRisks"
                name="technicalRisks"
                value={devProcessAnswers.technicalRisks}
                onChange={(e) => updateAnswer("technicalRisks", e.target.value)}
                placeholder="E.g., Third-party API stability concerns, legacy system dependencies..."
                className="form-textarea"
                rows={2}
              />
            </div>
          </div>

          {/* Economic Feasibility */}
          <div className="question-category">
            <h3 className="category-title">
              Economic Feasibility — "Does it make financial sense?"
            </h3>

            <div className="form-group">
              <label htmlFor="projectCosts">
                What are the estimated total project costs (development,
                hardware, software, training, maintenance)?{" "}
                <span className="required">*</span>
              </label>
              <textarea
                id="projectCosts"
                name="projectCosts"
                value={devProcessAnswers.projectCosts}
                onChange={(e) => updateAnswer("projectCosts", e.target.value)}
                placeholder="E.g., $500K total: $300K development, $100K infrastructure, $50K training, $50K maintenance..."
                className="form-textarea"
                rows={2}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="businessBenefits">
                What measurable business benefits (cost savings, revenue
                increase, efficiency gains) will the project deliver?{" "}
                <span className="required">*</span>
              </label>
              <textarea
                id="businessBenefits"
                name="businessBenefits"
                value={devProcessAnswers.businessBenefits}
                onChange={(e) =>
                  updateAnswer("businessBenefits", e.target.value)
                }
                placeholder="E.g., 30% cost reduction, $1M annual revenue increase, 50% faster processing..."
                className="form-textarea"
                rows={2}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="roiPayback">
                What is the projected ROI and payback period?{" "}
                <span className="optional">(Optional)</span>
              </label>
              <input
                id="roiPayback"
                type="text"
                name="roiPayback"
                value={devProcessAnswers.roiPayback}
                onChange={(e) => updateAnswer("roiPayback", e.target.value)}
                placeholder="E.g., 25% ROI, 18-month payback..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="budgetConstraints">
                Does the project fit within the current budget and funding
                constraints? <span className="required">*</span>
              </label>
              <input
                id="budgetConstraints"
                type="text"
                name="budgetConstraints"
                value={devProcessAnswers.budgetConstraints}
                onChange={(e) =>
                  updateAnswer("budgetConstraints", e.target.value)
                }
                placeholder="E.g., Yes, fits within $500K approved budget for this fiscal year..."
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="financialRisks">
                What are the financial risks if the project overruns budget or
                schedule? <span className="optional">(Optional)</span>
              </label>
              <input
                id="financialRisks"
                type="text"
                name="financialRisks"
                value={devProcessAnswers.financialRisks}
                onChange={(e) => updateAnswer("financialRisks", e.target.value)}
                placeholder="E.g., Funding may be pulled, loss of market opportunity..."
                className="form-input"
              />
            </div>
          </div>

          {/* Legal Feasibility */}
          <div className="question-category">
            <h3 className="category-title">
              Legal Feasibility — "Is it legal and compliant?"
            </h3>

            <div className="form-group">
              <label htmlFor="dataCompliance">
                Does the project comply with relevant data protection and
                privacy laws (e.g., GDPR, HIPAA, CCPA)?{" "}
                <span className="required">*</span>
              </label>
              <textarea
                id="dataCompliance"
                name="dataCompliance"
                value={devProcessAnswers.dataCompliance}
                onChange={(e) => updateAnswer("dataCompliance", e.target.value)}
                placeholder="E.g., Yes, GDPR-compliant with data encryption, consent management, and right-to-delete..."
                className="form-textarea"
                rows={2}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="industryRegulations">
                Are there industry-specific regulations (e.g., finance,
                healthcare) that must be addressed?{" "}
                <span className="optional">(Optional)</span>
              </label>
              <input
                id="industryRegulations"
                type="text"
                name="industryRegulations"
                value={devProcessAnswers.industryRegulations}
                onChange={(e) =>
                  updateAnswer("industryRegulations", e.target.value)
                }
                placeholder="E.g., PCI-DSS for payments, HIPAA for healthcare data..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="thirdPartyLicenses">
                Will any third-party software, APIs, or data be used, and are
                proper licenses and permissions in place?{" "}
                <span className="required">*</span>
              </label>
              <input
                id="thirdPartyLicenses"
                type="text"
                name="thirdPartyLicenses"
                value={devProcessAnswers.thirdPartyLicenses}
                onChange={(e) =>
                  updateAnswer("thirdPartyLicenses", e.target.value)
                }
                placeholder="E.g., Using Stripe API (licensed), open-source libraries (MIT/Apache), all compliant..."
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="intellectualProperty">
                Could the project infringe on any existing patents, copyrights,
                or trademarks? <span className="optional">(Optional)</span>
              </label>
              <input
                id="intellectualProperty"
                type="text"
                name="intellectualProperty"
                value={devProcessAnswers.intellectualProperty}
                onChange={(e) =>
                  updateAnswer("intellectualProperty", e.target.value)
                }
                placeholder="E.g., No known IP conflicts, legal review pending..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="contractualIssues">
                Are there contractual or liability issues related to data
                ownership or system usage?{" "}
                <span className="optional">(Optional)</span>
              </label>
              <input
                id="contractualIssues"
                type="text"
                name="contractualIssues"
                value={devProcessAnswers.contractualIssues}
                onChange={(e) =>
                  updateAnswer("contractualIssues", e.target.value)
                }
                placeholder="E.g., Data ownership terms need clarification..."
                className="form-input"
              />
            </div>
          </div>

          {/* Operational Feasibility */}
          <div className="question-category">
            <h3 className="category-title">
              Operational Feasibility — "If we build it, will they use it?"
            </h3>

            <div className="form-group">
              <label htmlFor="businessAlignment">
                Does the proposed solution align with current business workflows
                and solve the identified problem effectively?{" "}
                <span className="required">*</span>
              </label>
              <textarea
                id="businessAlignment"
                name="businessAlignment"
                value={devProcessAnswers.businessAlignment}
                onChange={(e) =>
                  updateAnswer("businessAlignment", e.target.value)
                }
                placeholder="E.g., Yes, directly addresses workflow bottlenecks and integrates with current processes..."
                className="form-textarea"
                rows={2}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="operationalImpact">
                How will the project impact daily operations and employee
                workload? <span className="optional">(Optional)</span>
              </label>
              <input
                id="operationalImpact"
                type="text"
                name="operationalImpact"
                value={devProcessAnswers.operationalImpact}
                onChange={(e) =>
                  updateAnswer("operationalImpact", e.target.value)
                }
                placeholder="E.g., Streamline workflows, reduce manual tasks by 40%..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="userAdoption">
                Are the intended users willing and able to adopt the new system?{" "}
                <span className="required">*</span>
              </label>
              <input
                id="userAdoption"
                type="text"
                name="userAdoption"
                value={devProcessAnswers.userAdoption}
                onChange={(e) => updateAnswer("userAdoption", e.target.value)}
                placeholder="E.g., Yes, positive user feedback from prototype testing, eager to adopt..."
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="trainingSupportNeeds">
                What training and support will be needed for successful rollout
                and continued usage?{" "}
                <span className="optional">(Optional)</span>
              </label>
              <input
                id="trainingSupportNeeds"
                type="text"
                name="trainingSupportNeeds"
                value={devProcessAnswers.trainingSupportNeeds}
                onChange={(e) =>
                  updateAnswer("trainingSupportNeeds", e.target.value)
                }
                placeholder="E.g., 2-day training sessions, user documentation..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="internalResources">
                Are internal resources (staff, management, IT support) available
                to sustain operations post-launch?{" "}
                <span className="required">*</span>
              </label>
              <input
                id="internalResources"
                type="text"
                name="internalResources"
                value={devProcessAnswers.internalResources}
                onChange={(e) =>
                  updateAnswer("internalResources", e.target.value)
                }
                placeholder="E.g., Yes, dedicated 3-person support team allocated for ongoing maintenance..."
                className="form-input"
                required
              />
            </div>
          </div>

          {/* Schedule Feasibility */}
          <div className="question-category">
            <h3 className="category-title">
              Schedule Feasibility — "Can we build it in time?"
            </h3>

            <div className="form-group">
              <label htmlFor="completionDate">
                What is the required completion date, and is it realistic given
                the scope and resources? <span className="required">*</span>
              </label>
              <input
                id="completionDate"
                type="text"
                name="completionDate"
                value={devProcessAnswers.completionDate}
                onChange={(e) => updateAnswer("completionDate", e.target.value)}
                placeholder="E.g., December 31, 2025 - realistic with current team and 6-month timeline..."
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="externalDependencies">
                Are there external dependencies (vendors, approvals, third-party
                services) that could delay delivery?{" "}
                <span className="required">*</span>
              </label>
              <input
                id="externalDependencies"
                type="text"
                name="externalDependencies"
                value={devProcessAnswers.externalDependencies}
                onChange={(e) =>
                  updateAnswer("externalDependencies", e.target.value)
                }
                placeholder="E.g., Payment gateway approval (2 weeks), third-party API integration (1 month)..."
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="timeToMarket">
                What is the critical time-to-market or opportunity window for
                the product? <span className="optional">(Optional)</span>
              </label>
              <input
                id="timeToMarket"
                type="text"
                name="timeToMarket"
                value={devProcessAnswers.timeToMarket}
                onChange={(e) => updateAnswer("timeToMarket", e.target.value)}
                placeholder="E.g., Must launch before Q4 holiday season..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="delayImpact">
                How will delays impact business goals, customer commitments, or
                competitive advantage?{" "}
                <span className="optional">(Optional)</span>
              </label>
              <input
                id="delayImpact"
                type="text"
                name="delayImpact"
                value={devProcessAnswers.delayImpact}
                onChange={(e) => updateAnswer("delayImpact", e.target.value)}
                placeholder="E.g., Loss of first-mover advantage, customer penalties..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="timelineFlexibility">
                Is there flexibility in the timeline if unexpected challenges
                occur? <span className="optional">(Optional)</span>
              </label>
              <input
                id="timelineFlexibility"
                type="text"
                name="timelineFlexibility"
                value={devProcessAnswers.timelineFlexibility}
                onChange={(e) =>
                  updateAnswer("timelineFlexibility", e.target.value)
                }
                placeholder="E.g., 2-week buffer available, hard deadline..."
                className="form-input"
              />
            </div>
          </div>

          <Button type="submit">Continue to Feasibility Check</Button>
        </div>
      </form>
    </div>
  );
};

DevelopmentProcessStep.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onError: PropTypes.func.isRequired,
};
