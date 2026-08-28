import { useState } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";

function App() {
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [jdFile, setJdFile] = useState(null);

  const [analysis, setAnalysis] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showResults, setShowResults] = useState(false);

  const handleAnalyze = async () => {
    if (!resume) {
      setError("Please upload your resume first.");
      return;
    }

    setError("");
    setLoading(true);

    const formData = new FormData();

    formData.append("file", resume);

    if (jobDescription.trim() !== "") {
      formData.append("job_description", jobDescription);
    }

    if (jdFile) {
      formData.append("job_description_file", jdFile);
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/upload-resume",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Analysis request failed.");
      }

      const data = await response.json();

      console.log("Analysis result:", data);

      setAnalysis(data.analysis);
      setShowResults(true);

    } catch (error) {
      console.error(error);

      setError(
        "Could not connect to the backend. Please make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };


  const handleBack = () => {
    setShowResults(false);
  };


  // Results page
  if (showResults) {
    return (
      <div className="app">

        <header className="header">
          <div className="brand">
            <div className="brand-icon">▧</div>
            <span>AI-Powered Resume Analyzer</span>
          </div>
        </header>


        <main className="results-page">

          <button
            className="back-button"
            onClick={handleBack}
          >
            ← Analyze another resume
          </button>


          <section className="results-intro">

            <p className="results-label">
              ✦ ANALYSIS COMPLETE
            </p>

            <h1>Resume Analysis</h1>

            <p>
              Here is the AI-generated feedback for your resume.
            </p>

          </section>


          <section className="analysis-card">

            <div className="analysis-header">

              <h2>AI Analysis</h2>

              <span>
                Qwen3 · Ollama
              </span>

            </div>


            <div className="analysis-content">
               <ReactMarkdown>
                 {analysis}
               </ReactMarkdown>
            </div>

          </section>

        </main>

      </div>
    );
  }


  // Upload page
  return (
    <div className="app">

      <header className="header">

        <div className="brand">

          <div className="brand-icon">
            ▧
          </div>

          <span>
            AI-Powered Resume Analyzer
          </span>

        </div>

      </header>


      <main className="main">

        <section className="intro">

          <h1>
            AI-Powered Resume Analyzer
          </h1>

          <p>
            Analyze your resume and get useful feedback using AI.
          </p>

        </section>


        <section className="analyzer-card">


          {/* Resume upload */}

          <div className="section">

            <h2>
              <span className="icon">▧</span>
              Upload Resume
            </h2>

            <p className="hint">
              Upload your resume in PDF format.
            </p>


            <div className="upload-box">

              <div className="upload-icon">
                ↑
              </div>

              <p className="upload-title">
                Choose your resume
              </p>

              <p className="upload-subtitle">
                PDF files only
              </p>

              <input
                type="file"
                accept=".pdf"
                onChange={(e) =>
                  setResume(e.target.files[0])
                }
              />


              {resume && (
                <p className="file-name">
                  ✓ {resume.name}
                </p>
              )}

            </div>

          </div>


          <div className="divider">
            <span>Optional</span>
          </div>


          {/* Job description */}

          <div className="section">

            <h2>
              <span className="icon">▣</span>
              Job Description
              <span className="optional">
                (Optional)
              </span>
            </h2>

            <p className="hint">
              Add a job description to see how well your resume matches the role.
            </p>


            <textarea
              placeholder="Paste the job description here..."
              value={jobDescription}
              onChange={(e) =>
                setJobDescription(e.target.value)
              }
            />


            <div className="or-divider">
              <span>OR</span>
            </div>


            <div className="jd-upload">

              <div className="jd-upload-text">

                <span className="pdf-icon">
                  📄
                </span>

                <div>

                  <strong>
                    Upload Job Description
                  </strong>

                  <p>
                    PDF file
                  </p>

                </div>

              </div>


              <input
                type="file"
                accept=".pdf"
                onChange={(e) =>
                  setJdFile(e.target.files[0])
                }
              />

            </div>

          </div>


          {error && (
            <div className="error-message">
              {error}
            </div>
          )}


          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading
              ? "Analyzing..."
              : "✦  Analyze Resume"}
          </button>


        </section>

      </main>

    </div>
  );
}

export default App;