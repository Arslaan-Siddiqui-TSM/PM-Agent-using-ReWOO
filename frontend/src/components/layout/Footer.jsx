import PropTypes from "prop-types";
import "./Footer.css";

export const Footer = ({ sessionId }) => {
  return (
    <footer className="footer">
      <p>Powered by AI • Session ID: {sessionId || "N/A"}</p>
    </footer>
  );
};

Footer.propTypes = {
  sessionId: PropTypes.string,
};
