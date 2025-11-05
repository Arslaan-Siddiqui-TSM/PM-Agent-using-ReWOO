import PropTypes from "prop-types";
import { Button, MarkdownRenderer } from "../ui";
import "./PlanStep.css";

export const PlanStep = ({ finalPlan, planFilePath, onReset }) => {
  return (
    <div className="step-container">
      <h2>Step 5: Project Plan Generated ✨</h2>

      <div className="success-message">
        <p>🎉 Your project plan has been successfully generated!</p>
        {planFilePath && (
          <p className="file-path">
            Saved to: <code>{planFilePath}</code>
          </p>
        )}
      </div>

      <div className="plan-preview">
        <MarkdownRenderer content={finalPlan} title="Project Plan" />
      </div>

      <div className="action-buttons">
        <Button onClick={onReset} variant="secondary">
          Start New Project
        </Button>
      </div>
    </div>
  );
};

PlanStep.propTypes = {
  finalPlan: PropTypes.string.isRequired,
  planFilePath: PropTypes.string,
  onReset: PropTypes.func.isRequired,
};
