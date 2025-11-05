import PropTypes from "prop-types";
import "./ErrorMessage.css";

export const ErrorMessage = ({ message }) => {
  if (!message) return null;

  return (
    <div className="error-message">
      <strong>Error:</strong> {message}
    </div>
  );
};

ErrorMessage.propTypes = {
  message: PropTypes.string,
};
