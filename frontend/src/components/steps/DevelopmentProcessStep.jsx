import { useState } from "react";
import PropTypes from "prop-types";
import { Button } from "../ui";
import "./DevelopmentProcessStep.css";

const INITIAL_ANSWERS = {
  methodology: "",
  teamSize: "",
  timeline: "",
  budget: "",
  techStack: "",
  constraints: "",
};

export const DevelopmentProcessStep = ({ onSubmit, onError }) => {
  const [devProcessAnswers, setDevProcessAnswers] = useState(INITIAL_ANSWERS);

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

  return (
    <div className="step-container">
      <h2>Step 2: Development Process Information</h2>
      <p>
        Provide information about your software development process. This will
        help in assessing project feasibility.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="static-questions-form">
          <div className="form-group">
            <label htmlFor="methodology">
              Development Methodology{" "}
              <span className="optional">(e.g., Agile, Waterfall, Scrum)</span>
            </label>
            <input
              id="methodology"
              type="text"
              name="methodology"
              value={devProcessAnswers.methodology}
              onChange={(e) => updateAnswer("methodology", e.target.value)}
              placeholder="What development methodology will you use?"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="teamSize">
              Team Size{" "}
              <span className="optional">
                (Number of developers, designers, testers, etc.)
              </span>
            </label>
            <input
              id="teamSize"
              type="text"
              name="teamSize"
              value={devProcessAnswers.teamSize}
              onChange={(e) => updateAnswer("teamSize", e.target.value)}
              placeholder="How many people will be on the team?"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="timeline">
              Project Timeline{" "}
              <span className="optional">(Expected duration)</span>
            </label>
            <input
              id="timeline"
              type="text"
              name="timeline"
              value={devProcessAnswers.timeline}
              onChange={(e) => updateAnswer("timeline", e.target.value)}
              placeholder="What is the expected project duration?"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="budget">
              Budget Constraints{" "}
              <span className="optional">
                (Approximate budget or constraints)
              </span>
            </label>
            <input
              id="budget"
              type="text"
              name="budget"
              value={devProcessAnswers.budget}
              onChange={(e) => updateAnswer("budget", e.target.value)}
              placeholder="What is the estimated budget or budget constraints?"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="techStack">
              Technology Stack{" "}
              <span className="optional">
                (Languages, frameworks, databases)
              </span>
            </label>
            <textarea
              id="techStack"
              name="techStack"
              value={devProcessAnswers.techStack}
              onChange={(e) => updateAnswer("techStack", e.target.value)}
              placeholder="What technologies, languages, and frameworks will be used?"
              className="form-textarea"
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="constraints">
              Key Constraints or Risks{" "}
              <span className="optional">
                (Technical, business, or resource constraints)
              </span>
            </label>
            <textarea
              id="constraints"
              name="constraints"
              value={devProcessAnswers.constraints}
              onChange={(e) => updateAnswer("constraints", e.target.value)}
              placeholder="Are there any known constraints or risks to the project?"
              className="form-textarea"
              rows={3}
            />
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
