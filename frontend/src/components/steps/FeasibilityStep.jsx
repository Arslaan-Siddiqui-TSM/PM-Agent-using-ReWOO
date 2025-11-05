import PropTypes from "prop-types";
import { Button } from "../ui";
import "./FeasibilityStep.css";

export const FeasibilityStep = ({ loading, onCheckFeasibility }) => {
  return (
    <div className="step-container">
      <h2>Step 3: Generate Feasibility Assessment</h2>
      <p>
        Analyze project feasibility based on uploaded documents and development
        process information.
      </p>

      <Button onClick={onCheckFeasibility} disabled={loading}>
        {loading ? "Analyzing Feasibility..." : "Check Feasibility"}
      </Button>
    </div>
  );
};

FeasibilityStep.propTypes = {
  loading: PropTypes.bool.isRequired,
  onCheckFeasibility: PropTypes.func.isRequired,
};
