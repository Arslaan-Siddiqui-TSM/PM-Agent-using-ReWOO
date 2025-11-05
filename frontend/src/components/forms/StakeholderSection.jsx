import PropTypes from "prop-types";

export const StakeholderSection = ({ values, onChange }) => {
  return (
    <div className="spec-section">
      <h4 className="section-title">Stakeholder</h4>

      <div className="form-group">
        <label htmlFor="stakeholders">Decision makers & comm channels</label>
        <textarea
          id="stakeholders"
          value={values.stakeholders}
          onChange={(e) => onChange("stakeholders", e.target.value)}
          placeholder="Identify key decision makers and communication channels..."
          className="form-textarea"
          rows={3}
        />
      </div>
    </div>
  );
};

StakeholderSection.propTypes = {
  values: PropTypes.shape({
    stakeholders: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};
