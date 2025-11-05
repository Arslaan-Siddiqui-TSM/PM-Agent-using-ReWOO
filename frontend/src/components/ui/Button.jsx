import PropTypes from "prop-types";
import "./Button.css";

export const Button = ({
  children,
  onClick,
  disabled = false,
  variant = "primary",
  type = "button",
  className = "",
}) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant} ${className}`}
    >
      {children}
    </button>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  disabled: PropTypes.bool,
  variant: PropTypes.oneOf(["primary", "secondary"]),
  type: PropTypes.oneOf(["button", "submit", "reset"]),
  className: PropTypes.string,
};
