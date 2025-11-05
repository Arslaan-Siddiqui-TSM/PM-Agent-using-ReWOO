import PropTypes from "prop-types";

export const TimelineSection = ({ values, onChange }) => {
  return (
    <div className="spec-section">
      <h4 className="section-title">Timeline</h4>

      <div className="form-group">
        <label>
          Optimization Priority <span className="required">*</span>
        </label>
        <div className="radio-group">
          <label className="radio-label">
            <input
              type="radio"
              name="optimizationPriority"
              value="timeline"
              checked={values.optimizationPriority === "timeline"}
              onChange={(e) => onChange("optimizationPriority", e.target.value)}
              required
            />
            <span>Timeline optimized</span>
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="optimizationPriority"
              value="quality"
              checked={values.optimizationPriority === "quality"}
              onChange={(e) => onChange("optimizationPriority", e.target.value)}
            />
            <span>Quality optimized</span>
          </label>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="startDate">
            Start Date <span className="required">*</span>
          </label>
          <input
            type="date"
            id="startDate"
            value={values.startDate}
            onChange={(e) => onChange("startDate", e.target.value)}
            className="form-input"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="endDate">
            End Date <span className="required">*</span>
          </label>
          <input
            type="date"
            id="endDate"
            value={values.endDate}
            onChange={(e) => onChange("endDate", e.target.value)}
            className="form-input"
            required
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="numberOfResources">
          Number of Resources <span className="required">*</span>
        </label>
        <input
          type="number"
          id="numberOfResources"
          value={values.numberOfResources}
          onChange={(e) => onChange("numberOfResources", e.target.value)}
          placeholder="e.g., 5"
          className="form-input"
          min="1"
          required
        />
      </div>
    </div>
  );
};

TimelineSection.propTypes = {
  values: PropTypes.shape({
    optimizationPriority: PropTypes.string.isRequired,
    startDate: PropTypes.string.isRequired,
    endDate: PropTypes.string.isRequired,
    numberOfResources: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};
