import PropTypes from "prop-types";

export const QualitySection = ({ values, onChange }) => {
  return (
    <div className="spec-section">
      <h4 className="section-title">Quality</h4>

      <div className="form-group">
        <label>
          Quality Priority <span className="required">*</span>
        </label>
        <div className="radio-group">
          <label className="radio-label">
            <input
              type="radio"
              name="qualityPriority"
              value="quality"
              checked={values.qualityPriority === "quality"}
              onChange={(e) => onChange("qualityPriority", e.target.value)}
              required
            />
            <span>Quality first (high cost, low speed)</span>
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="qualityPriority"
              value="speed"
              checked={values.qualityPriority === "speed"}
              onChange={(e) => onChange("qualityPriority", e.target.value)}
            />
            <span>Speed first (high/low cost, fast speed)</span>
          </label>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="protocolsCompliance">
          Describe protocols & compliance
        </label>
        <textarea
          id="protocolsCompliance"
          value={values.protocolsCompliance}
          onChange={(e) => onChange("protocolsCompliance", e.target.value)}
          placeholder="Describe quality protocols, standards, and compliance requirements..."
          className="form-textarea"
          rows={3}
        />
      </div>
    </div>
  );
};

QualitySection.propTypes = {
  values: PropTypes.shape({
    qualityPriority: PropTypes.string.isRequired,
    protocolsCompliance: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};
