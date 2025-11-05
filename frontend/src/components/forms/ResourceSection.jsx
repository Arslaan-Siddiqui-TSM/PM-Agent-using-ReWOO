import PropTypes from "prop-types";

export const ResourceSection = ({ values, onChange }) => {
  return (
    <div className="spec-section">
      <h4 className="section-title">Resource</h4>

      <div className="form-group">
        <label>
          Resource Flexibility <span className="required">*</span>
        </label>
        <div className="radio-group">
          <label className="radio-label">
            <input
              type="radio"
              name="resourceFlexibility"
              value="flexible"
              checked={values.resourceFlexibility === "flexible"}
              onChange={(e) => onChange("resourceFlexibility", e.target.value)}
              required
            />
            <span>Resource flexible</span>
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="resourceFlexibility"
              value="constrained"
              checked={values.resourceFlexibility === "constrained"}
              onChange={(e) => onChange("resourceFlexibility", e.target.value)}
            />
            <span>Resource constrained</span>
          </label>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="resourceComposition">Describe about composition</label>
        <textarea
          id="resourceComposition"
          value={values.resourceComposition}
          onChange={(e) => onChange("resourceComposition", e.target.value)}
          placeholder="Describe the team composition (e.g., developers, designers, testers)..."
          className="form-textarea"
          rows={3}
        />
      </div>

      <div className="form-group">
        <label htmlFor="resourceSkills">Describe about skills</label>
        <textarea
          id="resourceSkills"
          value={values.resourceSkills}
          onChange={(e) => onChange("resourceSkills", e.target.value)}
          placeholder="Describe required skills and expertise..."
          className="form-textarea"
          rows={3}
        />
      </div>
    </div>
  );
};

ResourceSection.propTypes = {
  values: PropTypes.shape({
    resourceFlexibility: PropTypes.string.isRequired,
    resourceComposition: PropTypes.string.isRequired,
    resourceSkills: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};
