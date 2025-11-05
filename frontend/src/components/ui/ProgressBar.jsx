import PropTypes from "prop-types";
import "./ProgressBar.css";

const STEPS = [
  { number: 1, label: "1. Upload" },
  { number: 2, label: "2. Process Info" },
  { number: 3, label: "3. Feasibility" },
  { number: 4, label: "4. Review" },
  { number: 5, label: "5. Plan" },
];

export const ProgressBar = ({ currentStep }) => {
  return (
    <div className="progress-bar">
      {STEPS.map((step) => (
        <div
          key={step.number}
          className={`progress-step ${
            currentStep >= step.number ? "active" : ""
          }`}
        >
          {step.label}
        </div>
      ))}
    </div>
  );
};

ProgressBar.propTypes = {
  currentStep: PropTypes.number.isRequired,
};
