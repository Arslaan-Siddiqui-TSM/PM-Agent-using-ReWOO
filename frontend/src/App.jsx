import "./App.css";
import { WORKFLOW_STEPS } from "./constants";
import { useProjectWorkflow } from "./hooks";
import { Header, Footer } from "./components/layout";
import { ProgressBar } from "./components/ui";
import {
  UploadStep,
  DevelopmentProcessStep,
  FeasibilityStep,
  ReviewStep,
  PlanStep,
} from "./components/steps";
import { useEffect } from "react";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

function App() {
  const {
    step,
    sessionId,
    loading,
    error,
    successMessage,
    feasibilityReport,
    feasibilityFilePath,
    developmentContextJsonPath,
    finalPlan,
    planFilePath,
    handleUpload,
    handleDevelopmentProcessSubmit,
    handleCheckFeasibility,
    handleGeneratePlan,
    handleReset,
    setError,
    setSuccessMessage,
  } = useProjectWorkflow();

<<<<<<< Updated upstream
  // Show error toasts
  useEffect(() => {
    if (error) {
      toast.error(error);
      setError(null);
=======
  // Step 1: Upload
  const [files, setFiles] = useState([]);
  const [useDefaultFiles, setUseDefaultFiles] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  
  // Processing status tracking (no polling - synchronous upload)
  const [processingStatus, setProcessingStatus] = useState(null); // pending, processing, completed, failed
  const [processingMessage, setProcessingMessage] = useState("");

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

  // No polling needed - processing is synchronous
  // When upload completes, processing is done and we can advance

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
        setProcessingStatus(data.status);
        setProcessingMessage(data.message || "");
        
        // Processing is synchronous - if we got here, it's complete!
        if (data.status === "completed") {
          // Show success briefly then auto-advance
          setTimeout(() => {
            setStep(2);
          }, 1500);
        } else if (data.status === "failed") {
          setError(data.message || "Processing failed");
        }
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
        setProcessingStatus(data.status);
        setProcessingMessage(data.message || "");
        
        // Processing is synchronous - if we got here, it's complete!
        if (data.status === "completed") {
          // Show success briefly then auto-advance
          setTimeout(() => {
            setStep(2);
          }, 1500);
        } else if (data.status === "failed") {
          setError(data.message || "Processing failed");
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
>>>>>>> Stashed changes
    }
  }, [error, setError]);

  // Show success toasts
  useEffect(() => {
    if (successMessage) {
      toast.success(successMessage);
      setSuccessMessage(null);
    }
<<<<<<< Updated upstream
  }, [successMessage, setSuccessMessage]);
=======
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
        // Check if it's the "too early" error
        if (response.status === 425) {
          throw new Error("Document processing is still in progress. Please wait a moment and try again.");
        }
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
    setProcessingStatus(null);
    setProcessingMessage("");
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
>>>>>>> Stashed changes

  return (
    <div className="app">
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />

      <Header />

      <ProgressBar currentStep={step} />

      <main className="main-content">
        {step === WORKFLOW_STEPS.UPLOAD && (
          <UploadStep loading={loading} onUpload={handleUpload} />
        )}

<<<<<<< Updated upstream
        {step === WORKFLOW_STEPS.DEVELOPMENT_PROCESS && (
          <DevelopmentProcessStep
            onSubmit={handleDevelopmentProcessSubmit}
            onError={setError}
          />
=======
        {/* Step 1: Upload Documents & Processing */}
        {step === 1 && (
          <div className="step-container">
            <h2>Step 1: Upload & Process Documents</h2>
            <p>
              Upload your project documents or use the default sample files.
              Processing includes parsing, JSON conversion, and embedding.
            </p>

            {/* Show upload form only if not processing */}
            {!processingStatus && (
              <>
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
                  {loading ? "Processing (3-5 min)..." : "Upload & Process Documents"}
                </button>
              </>
            )}

            {/* Show uploaded files */}
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

            {/* Processing Status Indicator */}
            {processingStatus && processingStatus !== "completed" && (
              <div className={`processing-status ${processingStatus}`}>
                <div className="status-indicator">
                  {processingStatus === "processing" && (
                    <>
                      <div className="spinner"></div>
                      <div className="status-text">
                        <strong>⏳ Processing Documents...</strong>
                        <p>
                          Step 1: Parsing PDFs to Markdown<br/>
                          Step 2: Converting Markdown to JSON (LLM-based)<br/>
                          Step 3: Creating embeddings in Qdrant
                        </p>
                        <p style={{marginTop: "1rem"}}>
                          This typically takes 3-5 minutes. Please wait...
                        </p>
                      </div>
                    </>
                  )}
                  {processingStatus === "pending" && (
                    <>
                      <div className="spinner"></div>
                      <div className="status-text">
                        <strong>⏳ Preparing to process documents...</strong>
                      </div>
                    </>
                  )}
                  {processingStatus === "failed" && (
                    <div className="status-text error">
                      <strong>❌ Processing Failed</strong>
                      <p>{processingMessage || "An error occurred during document processing."}</p>
                      <button onClick={handleReset} className="btn btn-secondary" style={{marginTop: "1rem"}}>
                        Try Again
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Success indicator - shows briefly before auto-advancing */}
            {processingStatus === "completed" && (
              <div className="processing-status completed">
                <div className="status-indicator">
                  <div className="status-text success">
                    <strong>✅ Processing Complete!</strong>
                    <p>{processingMessage || "All documents have been parsed, converted, and embedded."}</p>
                    <p style={{marginTop: "0.5rem"}}>Advancing to development process questions...</p>
                  </div>
                </div>
              </div>
            )}
          </div>
>>>>>>> Stashed changes
        )}

        {step === WORKFLOW_STEPS.FEASIBILITY && (
          <FeasibilityStep
            loading={loading}
            onCheckFeasibility={handleCheckFeasibility}
          />
        )}

        {step === WORKFLOW_STEPS.REVIEW && (
          <ReviewStep
            loading={loading}
            feasibilityReport={feasibilityReport}
            feasibilityFilePath={feasibilityFilePath}
            developmentContextJsonPath={developmentContextJsonPath}
            onGeneratePlan={handleGeneratePlan}
          />
        )}

        {step === WORKFLOW_STEPS.PLAN && (
          <PlanStep
            finalPlan={finalPlan}
            planFilePath={planFilePath}
            onReset={handleReset}
          />
        )}
      </main>

      <Footer sessionId={sessionId} />
    </div>
  );
}

export default App;
