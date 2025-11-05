import PropTypes from "prop-types";

export const BudgetSection = ({ values, onChange }) => {
  return (
    <div className="spec-section">
      <h4 className="section-title">Budget</h4>

      <div className="form-group">
        <label>
          Budget Type <span className="required">*</span>
        </label>
        <div className="radio-group">
          <label className="radio-label">
            <input
              type="radio"
              name="budgetType"
              value="fixBid"
              checked={values.budgetType === "fixBid"}
              onChange={(e) => onChange("budgetType", e.target.value)}
              required
            />
            <span>Fix Bid</span>
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="budgetType"
              value="hourlyBid"
              checked={values.budgetType === "hourlyBid"}
              onChange={(e) => onChange("budgetType", e.target.value)}
            />
            <span>Hourly Bid</span>
          </label>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="budgetDescription">Description</label>
        <textarea
          id="budgetDescription"
          value={values.budgetDescription}
          onChange={(e) => onChange("budgetDescription", e.target.value)}
          placeholder="Describe the budget constraints and considerations..."
          className="form-textarea"
          rows={3}
        />
      </div>

      <div className="form-group">
        <label htmlFor="costBreakdown">Cost Breakdown</label>
        <textarea
          id="costBreakdown"
          value={values.costBreakdown}
          onChange={(e) => onChange("costBreakdown", e.target.value)}
          placeholder="Breakdown of costs (e.g., development, infrastructure, licenses)..."
          className="form-textarea"
          rows={3}
        />
      </div>

      <div className="form-group">
        <label htmlFor="totalBudget">
          Total Budget <span className="required">*</span>
        </label>
        <input
          type="text"
          id="totalBudget"
          value={values.totalBudget}
          onChange={(e) => onChange("totalBudget", e.target.value)}
          placeholder="e.g., $500,000"
          className="form-input"
          required
        />
      </div>
    </div>
  );
};

BudgetSection.propTypes = {
  values: PropTypes.shape({
    budgetType: PropTypes.string.isRequired,
    budgetDescription: PropTypes.string.isRequired,
    costBreakdown: PropTypes.string.isRequired,
    totalBudget: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};
