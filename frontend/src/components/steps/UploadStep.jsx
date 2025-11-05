import { useState } from "react";
import PropTypes from "prop-types";
import { Button } from "../ui";
import "./UploadStep.css";

export const UploadStep = ({ loading, onUpload }) => {
  const [files, setFiles] = useState([]);
  const [useDefaultFiles, setUseDefaultFiles] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleUpload = async () => {
    const result = await onUpload(files, useDefaultFiles);
    if (result?.uploadedFiles) {
      setUploadedFiles(result.uploadedFiles);
    }
  };

  return (
    <div className="step-container">
      <h2>Step 1: Upload Project Documents</h2>
      <p>Upload your project documents or use the default sample files.</p>

      <div className="upload-options">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={useDefaultFiles}
            onChange={(e) => setUseDefaultFiles(e.target.checked)}
          />
          Use default sample files
        </label>
      </div>

      {!useDefaultFiles && (
        <div className="file-input-container">
          <input
            type="file"
            accept=".pdf"
            multiple
            onChange={(e) => setFiles(Array.from(e.target.files))}
            className="file-input"
          />
          {files.length > 0 && (
            <p className="file-count">{files.length} file(s) selected</p>
          )}
        </div>
      )}

      <Button
        onClick={handleUpload}
        disabled={loading || (!useDefaultFiles && files.length === 0)}
      >
        {loading ? "Uploading..." : "Upload & Continue"}
      </Button>

      {uploadedFiles.length > 0 && (
        <div className="uploaded-files">
          <h3>Uploaded Files:</h3>
          <ul>
            {uploadedFiles.map((file, idx) => (
              <li key={idx}>{file}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

UploadStep.propTypes = {
  loading: PropTypes.bool.isRequired,
  onUpload: PropTypes.func.isRequired,
};
