import PropTypes from "prop-types";
import ReactMarkdown from "react-markdown";
import "./MarkdownRenderer.css";

export const MarkdownRenderer = ({ content, title }) => {
  if (!content) return null;

  return (
    <div className="markdown-content">
      {title && <h3>{title}</h3>}
      <div className="markdown-wrapper">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
};

MarkdownRenderer.propTypes = {
  content: PropTypes.string,
  title: PropTypes.string,
};
