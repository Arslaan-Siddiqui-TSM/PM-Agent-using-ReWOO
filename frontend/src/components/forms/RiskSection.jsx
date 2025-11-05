import PropTypes from "prop-types";

export const RiskSection = ({ values, onChange }) => {
  return (
    <div className="spec-section">
      <h4 className="section-title">Risk Management</h4>

      <div className="form-group">
        <label>
          Risk Tolerance <span className="required">*</span>
        </label>
        <div className="radio-group">
          <label className="radio-label">
            <input
              type="radio"
              name="riskTolerance"
              value="aggressive"
              checked={values.riskTolerance === "aggressive"}
              onChange={(e) => onChange("riskTolerance", e.target.value)}
              required
            />
            <span>Aggressive risk tolerance</span>
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="riskTolerance"
              value="conservative"
              checked={values.riskTolerance === "conservative"}
              onChange={(e) => onChange("riskTolerance", e.target.value)}
            />
            <span>Conservative risk tolerance</span>
          </label>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="techUncertainty">Describe about tech uncertainty</label>
        <textarea
          id="techUncertainty"
          value={values.techUncertainty}
          onChange={(e) => onChange("techUncertainty", e.target.value)}
          placeholder="Describe technical uncertainties and how they'll be managed..."
          className="form-textarea"
          rows={3}
        />
      </div>

      <div className="form-group">
        <label htmlFor="vendorDependency">
          Describe about vendor dependency
        </label>
        <textarea
          id="vendorDependency"
          value={values.vendorDependency}
          onChange={(e) => onChange("vendorDependency", e.target.value)}
          placeholder="Describe dependencies on external vendors and mitigation strategies..."
          className="form-textarea"
          rows={3}
        />
      </div>
    </div>
  );
};

RiskSection.propTypes = {
  values: PropTypes.shape({
    riskTolerance: PropTypes.string.isRequired,
    techUncertainty: PropTypes.string.isRequired,
    vendorDependency: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};
