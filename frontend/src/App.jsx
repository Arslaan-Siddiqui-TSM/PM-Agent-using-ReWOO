import { useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_BASE = "http://localhost:8000/api";

function App() {
  const [step, setStep] = useState(1);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Step 1: Upload
  const [files, setFiles] = useState([]);
  const [useDefaultFiles, setUseDefaultFiles] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  // Step 2: Static Development Process Questions
  const [devProcessAnswers, setDevProcessAnswers] = useState({
    methodology: "",
    teamSize: "",
    timeline: "",
    budget: "",
    techStack: "",
    constraints: "",
  });

  // Step 3: Feasibility assessment
  const [feasibilityReport, setFeasibilityReport] = useState("");
  const [feasibilityFilePath, setFeasibilityFilePath] = useState("");
  const [developmentContextJsonPath, setDevelopmentContextJsonPath] =
    useState("");

  // Step 4: Feedback
  const [feedback, setFeedback] = useState("");

  // Step 5: Final plan
  const [finalPlan, setFinalPlan] = useState("");
  const [planFilePath, setPlanFilePath] = useState("");

  // Handle file upload
  const handleUpload = async () => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();

      if (useDefaultFiles) {
        const response = await fetch(
          `${API_BASE}/upload?use_default_files=true`,
          {
            method: "POST",
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Upload failed");
        }

        const data = await response.json();
        setSessionId(data.session_id);
        setUploadedFiles(data.uploaded_files);
        setStep(2);
      } else {
        if (files.length === 0) {
          throw new Error("Please select at least one PDF file");
        }

        files.forEach((file) => {
          formData.append("files", file);
        });

        const response = await fetch(`${API_BASE}/upload`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Upload failed");
        }

        const data = await response.json();
        setSessionId(data.session_id);
        setUploadedFiles(data.uploaded_files);
        setStep(2);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle static questions submission - go directly to feasibility check
  const handleStaticQuestionsSubmit = (event) => {
    // Validate that at least some fields are filled
    event.preventDefault();
    const formData = Object.fromEntries(new FormData(event.target));
    console.log("Static questions submitted", formData);
    const hasAnswers = Object.values(devProcessAnswers).some(
      (val) => val.trim() !== ""
    );
    if (!hasAnswers) {
      setError("Please answer at least one question before continuing");
      return;
    }
    setError(null);
    setStep(3);
  };

  // Check feasibility
  const handleCheckFeasibility = async () => {
    setLoading(true);
    setError(null);

    try {
      // Prepare the context with user's development process answers
      const contextWithAnswers = {
        session_id: sessionId,
        use_intelligent_processing: true,
        development_context: devProcessAnswers,
      };

      const response = await fetch(`${API_BASE}/feasibility`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(contextWithAnswers),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Feasibility check failed");
      }

      const data = await response.json();

      // Store file paths
      if (data.file_path) {
        setFeasibilityFilePath(data.file_path);
      }
      if (data.development_context_json_path) {
        setDevelopmentContextJsonPath(data.development_context_json_path);
      }

      // Fetch the feasibility report content
      if (data.file_path) {
        // Read the actual file content
        try {
          const fileResponse = await fetch(
            `${API_BASE}/file-content?file_path=${encodeURIComponent(
              data.file_path
            )}`
          );
          if (fileResponse.ok) {
            const content = await fileResponse.text();
            setFeasibilityReport(content);
          } else {
            setFeasibilityReport(
              "Feasibility assessment generated successfully. Review the assessment before proceeding."
            );
          }
        } catch (err) {
          console.error("Error fetching file content:", err);
          setFeasibilityReport(
            "Feasibility assessment generated successfully. Review the assessment before proceeding."
          );
        }
      }

      setStep(4);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Generate final plan
  const handleGeneratePlan = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/generate-plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          use_intelligent_processing: true,
          max_iterations: 5,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Plan generation failed");
      }

      const data = await response.json();
      setFinalPlan(data.result);
      setPlanFilePath(data.file_path);
      setStep(5);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep(1);
    setSessionId(null);
    setFiles([]);
    setUploadedFiles([]);
    setDevProcessAnswers({
      methodology: "",
      teamSize: "",
      timeline: "",
      budget: "",
      techStack: "",
      constraints: "",
    });
    setFeasibilityReport("");
    setFeasibilityFilePath("");
    setDevelopmentContextJsonPath("");
    setFeedback("");
    setFinalPlan("");
    setPlanFilePath("");
    setError(null);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>📋 Project Planning Assistant</h1>
        <p className="subtitle">
          AI-powered feasibility analysis and project planning
        </p>
      </header>

      <div className="progress-bar">
        <div className={`progress-step ${step >= 1 ? "active" : ""}`}>
          1. Upload
        </div>
        <div className={`progress-step ${step >= 2 ? "active" : ""}`}>
          2. Process Info
        </div>
        <div className={`progress-step ${step >= 3 ? "active" : ""}`}>
          3. Feasibility
        </div>
        <div className={`progress-step ${step >= 4 ? "active" : ""}`}>
          4. Review
        </div>
        <div className={`progress-step ${step >= 5 ? "active" : ""}`}>
          5. Plan
        </div>
      </div>

      <main className="main-content">
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Step 1: Upload Documents */}
        {step === 1 && (
          <div className="step-container">
            <h2>Step 1: Upload Project Documents</h2>
            <p>
              Upload your project documents or use the default sample files.
            </p>

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

            <button
              onClick={handleUpload}
              disabled={loading || (!useDefaultFiles && files.length === 0)}
              className="btn btn-primary"
            >
              {loading ? "Uploading..." : "Upload & Continue"}
            </button>

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
        )}

        {/* Step 2: Static Development Process Questions */}
        {step === 2 && (
          <div className="step-container">
            <h2>Step 2: Development Process Information</h2>
            <p>
              Provide information about your software development process. This
              will help in assessing project feasibility.
            </p>

            <form onSubmit={handleStaticQuestionsSubmit}>
              <div className="static-questions-form">
                <div className="form-group">
                  <label htmlFor="methodology">
                    Development Methodology{" "}
                    <span className="optional">
                      (e.g., Agile, Waterfall, Scrum)
                    </span>
                  </label>
                  <input
                    id="methodology"
                    type="text"
                    name="methodology"
                    value={devProcessAnswers.methodology}
                    onChange={(e) =>
                      setDevProcessAnswers({
                        ...devProcessAnswers,
                        methodology: e.target.value,
                      })
                    }
                    placeholder="What development methodology will you use?"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="teamSize">
                    Team Size{" "}
                    <span className="optional">
                      (Number of developers, designers, testers, etc.)
                    </span>
                  </label>
                  <input
                    id="teamSize"
                    type="text"
                    name="teamSize"
                    value={devProcessAnswers.teamSize}
                    onChange={(e) =>
                      setDevProcessAnswers({
                        ...devProcessAnswers,
                        teamSize: e.target.value,
                      })
                    }
                    placeholder="How many people will be on the team?"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="timeline">
                    Project Timeline{" "}
                    <span className="optional">(Expected duration)</span>
                  </label>
                  <input
                    id="timeline"
                    type="text"
                    name="timeline"
                    value={devProcessAnswers.timeline}
                    onChange={(e) =>
                      setDevProcessAnswers({
                        ...devProcessAnswers,
                        timeline: e.target.value,
                      })
                    }
                    placeholder="What is the expected project duration?"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="budget">
                    Budget Constraints{" "}
                    <span className="optional">
                      (Approximate budget or constraints)
                    </span>
                  </label>
                  <input
                    id="budget"
                    type="text"
                    name="budget"
                    value={devProcessAnswers.budget}
                    onChange={(e) =>
                      setDevProcessAnswers({
                        ...devProcessAnswers,
                        budget: e.target.value,
                      })
                    }
                    placeholder="What is the estimated budget or budget constraints?"
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="techStack">
                    Technology Stack{" "}
                    <span className="optional">
                      (Languages, frameworks, databases)
                    </span>
                  </label>
                  <textarea
                    id="techStack"
                    name="techStack"
                    value={devProcessAnswers.techStack}
                    onChange={(e) =>
                      setDevProcessAnswers({
                        ...devProcessAnswers,
                        techStack: e.target.value,
                      })
                    }
                    placeholder="What technologies, languages, and frameworks will be used?"
                    className="form-textarea"
                    rows={3}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="constraints">
                    Key Constraints or Risks{" "}
                    <span className="optional">
                      (Technical, business, or resource constraints)
                    </span>
                  </label>
                  <textarea
                    id="constraints"
                    name="constraints"
                    value={devProcessAnswers.constraints}
                    onChange={(e) =>
                      setDevProcessAnswers({
                        ...devProcessAnswers,
                        constraints: e.target.value,
                      })
                    }
                    placeholder="Are there any known constraints or risks to the project?"
                    className="form-textarea"
                    rows={3}
                  />
                </div>

                <button type="submit" className="btn btn-primary">
                  Continue to Feasibility Check
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Step 3: Feasibility Check */}
        {step === 3 && (
          <div className="step-container">
            <h2>Step 3: Generate Feasibility Assessment</h2>
            <p>
              Analyze project feasibility based on uploaded documents and
              development process information.
            </p>

            <button
              onClick={handleCheckFeasibility}
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? "Analyzing Feasibility..." : "Check Feasibility"}
            </button>
          </div>
        )}

        {/* Step 4: Review Feasibility & Provide Feedback */}
        {step === 4 && (
          <div className="step-container">
            <h2>Step 4: Review Feasibility Assessment</h2>

            <div className="report-container">
              <div className="report-info">
                <p>✅ Feasibility assessment has been generated and saved.</p>
                {feasibilityFilePath && (
                  <p className="file-path">
                    Feasibility Report: <code>{feasibilityFilePath}</code>
                  </p>
                )}
                {developmentContextJsonPath && (
                  <p className="file-path">
                    Development Context JSON:{" "}
                    <code>{developmentContextJsonPath}</code>
                  </p>
                )}
              </div>

              {feasibilityReport && (
                <div className="markdown-content">
                  <h3>Feasibility Assessment Report</h3>
                  <div className="markdown-wrapper">
                    <ReactMarkdown>{feasibilityReport}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>

            <div className="feedback-section">
              <h3>Provide Feedback (Optional)</h3>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Add any comments or concerns about the feasibility assessment..."
                className="feedback-textarea"
                rows={4}
              />
            </div>

            <button
              onClick={handleGeneratePlan}
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? "Generating Plan..." : "Generate Project Plan"}
            </button>
          </div>
        )}

        {/* Step 5: Final Project Plan */}
        {step === 5 && (
          <div className="step-container">
            <h2>Step 5: Project Plan Generated ✨</h2>

            <div className="success-message">
              <p>🎉 Your project plan has been successfully generated!</p>
              {planFilePath && (
                <p className="file-path">
                  Saved to: <code>{planFilePath}</code>
                </p>
              )}
            </div>

            <div className="plan-preview">
              <h3>Project Plan</h3>
              <div className="markdown-content">
                <div className="markdown-wrapper">
                  <ReactMarkdown>{finalPlan}</ReactMarkdown>
                </div>
              </div>
            </div>

            <div className="action-buttons">
              <button onClick={handleReset} className="btn btn-secondary">
                Start New Project
              </button>
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Powered by AI • Session ID: {sessionId || "N/A"}</p>
      </footer>
    </div>
  );
}

export default App;
