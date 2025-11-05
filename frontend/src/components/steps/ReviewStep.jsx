import { useState } from "react";
import PropTypes from "prop-types";
import { Button, MarkdownRenderer } from "../ui";
import "./ReviewStep.css";

export const ReviewStep = ({
  loading,
  feasibilityReport,
  feasibilityFilePath,
  developmentContextJsonPath,
  onGeneratePlan,
}) => {
  const [feedback, setFeedback] = useState("");

  return (
    <div className="step-container">
      <h2>Step 4: Review Feasibility Assessment</h2>

      <div className="report-container">
        <div className="report-info">
          <p>✅ Feasibility assessment has been generated and saved.</p>
          {feasibilityFilePath && (
            <p className="file-path">
              Feasibility Report: <code>{feasibilityFilePath}</code>
            </p>
          )}
          {developmentContextJsonPath && (
            <p className="file-path">
              Development Context JSON:{" "}
              <code>{developmentContextJsonPath}</code>
            </p>
          )}
        </div>

        {feasibilityReport && (
          <MarkdownRenderer
            content={feasibilityReport}
            title="Feasibility Assessment Report"
          />
        )}
      </div>

      <div className="feedback-section">
        <h3>Provide Feedback (Optional)</h3>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Add any comments or concerns about the feasibility assessment..."
          className="feedback-textarea"
          rows={4}
        />
      </div>

      <Button onClick={onGeneratePlan} disabled={loading}>
        {loading ? "Generating Plan..." : "Generate Project Plan"}
      </Button>
    </div>
  );
};

ReviewStep.propTypes = {
  loading: PropTypes.bool.isRequired,
  feasibilityReport: PropTypes.string,
  feasibilityFilePath: PropTypes.string,
  developmentContextJsonPath: PropTypes.string,
  onGeneratePlan: PropTypes.func.isRequired,
};
