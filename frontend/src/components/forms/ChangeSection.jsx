import PropTypes from "prop-types";

export const ChangeSection = ({ values, onChange }) => {
  return (
    <div className="spec-section">
      <h4 className="section-title">Change / Adaptation</h4>

      <div className="form-group">
        <label htmlFor="upskillingNeeds">Upskilling needs</label>
        <textarea
          id="upskillingNeeds"
          value={values.upskillingNeeds}
          onChange={(e) => onChange("upskillingNeeds", e.target.value)}
          placeholder="Describe training and upskilling requirements for the team..."
          className="form-textarea"
          rows={3}
        />
      </div>
    </div>
  );
};

ChangeSection.propTypes = {
  values: PropTypes.shape({
    upskillingNeeds: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};
