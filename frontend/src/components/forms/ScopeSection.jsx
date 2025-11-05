import PropTypes from "prop-types";

export const ScopeSection = ({ values, onChange }) => {
  return (
    <div className="spec-section">
      <h4 className="section-title">Scope</h4>

      <div className="form-group">
        <label htmlFor="mustHave">
          Must Have <span className="required">*</span>
        </label>
        <textarea
          id="mustHave"
          value={values.mustHave}
          onChange={(e) => onChange("mustHave", e.target.value)}
          placeholder="List the essential features and requirements that must be included..."
          className="form-textarea"
          rows={4}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="niceToHave">Nice to Have</label>
        <textarea
          id="niceToHave"
          value={values.niceToHave}
          onChange={(e) => onChange("niceToHave", e.target.value)}
          placeholder="List features that would be beneficial but are not critical..."
          className="form-textarea"
          rows={3}
        />
      </div>

      <div className="form-group">
        <label htmlFor="doNot">Should Not Have</label>
        <textarea
          id="doNot"
          value={values.doNot}
          onChange={(e) => onChange("doNot", e.target.value)}
          placeholder="List features or approaches that should be avoided..."
          className="form-textarea"
          rows={3}
        />
      </div>
    </div>
  );
};

ScopeSection.propTypes = {
  values: PropTypes.shape({
    mustHave: PropTypes.string.isRequired,
    niceToHave: PropTypes.string.isRequired,
    doNot: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};
