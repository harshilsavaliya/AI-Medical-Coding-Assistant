import { ChangeEvent, FormEvent, useState } from "react";

import { ResultPanel } from "./components/ResultPanel";
import { StatusBanner } from "./components/StatusBanner";
import {
  PredictionResponse,
  predictFromFile,
  predictFromText,
} from "./lib/api";

type InputMode = "text" | "file";
type SubmitState = "idle" | "loading" | "success" | "error";

const sampleText =
  "Patient presents with uncontrolled diabetes, hypertension, and chronic cough.";

export default function App() {
  const [activeTab, setActiveTab] = useState<InputMode>("text");
  const [textInput, setTextInput] = useState(sampleText);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<SubmitState>("idle");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<PredictionResponse | null>(null);

  async function handleTextSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedText = textInput.trim();

    if (!normalizedText) {
      setStatus("error");
      setMessage("Enter clinical text before submitting.");
      return;
    }

    setStatus("loading");
    setMessage("Analyzing the clinical note and preparing ICD-10 suggestions...");

    try {
      const response = await predictFromText(normalizedText);
      setResult(response);
      setStatus("success");
      setMessage("Results are ready.");
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Prediction failed.");
    }
  }

  async function handleFileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile) {
      setStatus("error");
      setMessage("Select a JPG or PNG image before submitting.");
      return;
    }

    setStatus("loading");
    setMessage("Uploading image, extracting text, and preparing ICD-10 suggestions...");

    try {
      const response = await predictFromFile(selectedFile);
      setResult(response);
      setStatus("success");
      setMessage("Results are ready.");
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
    setStatus("idle");
    setMessage("");
  }

  function switchTab(tab: InputMode) {
    setActiveTab(tab);
    setStatus("idle");
    setMessage("");
  }

  return (
    <div className="page-shell">
      <main className="workspace">
        <section className="intro-panel">
          <div className="eyebrow">AI Medical Coding Assistant</div>
          <h2>Submit clinical text or upload a document image to generate ICD-10 suggestions.</h2>
          <p>
            Choose the input format that matches the case you are reviewing. Both
            routes return the same coding output, confidence values, and explanation.
          </p>

          <div className="intro-grid">
            <div className="intro-card">
              <strong>Text input</strong>
              <span>Best for copied clinical notes, summaries, and typed diagnoses.</span>
            </div>
            <div className="intro-card">
              <strong>File upload</strong>
              <span>Best for JPG or PNG screenshots, scans, and image-based reports.</span>
            </div>
          </div>
        </section>

        <section className="tool-panel">
          <div className="tabs" role="tablist" aria-label="Prediction input options">
            <button
              className={`tab-button ${activeTab === "text" ? "tab-button--active" : ""}`}
              type="button"
              role="tab"
              aria-selected={activeTab === "text"}
              onClick={() => switchTab("text")}
            >
              Text Input
            </button>
            <button
              className={`tab-button ${activeTab === "file" ? "tab-button--active" : ""}`}
              type="button"
              role="tab"
              aria-selected={activeTab === "file"}
              onClick={() => switchTab("file")}
            >
              File Upload
            </button>
          </div>

          <div className="tool-layout">
            <section className="input-panel">
              {activeTab === "text" ? (
                <form className="input-form" onSubmit={handleTextSubmit}>
                  <div className="panel-label">Text Input</div>
                  <h2>Analyze clinical note text</h2>
                  <p className="panel-copy">
                    Paste a note, summary, or diagnosis narrative and send it directly to the
                    text prediction endpoint.
                  </p>

                  <label className="input-group">
                    <span>Clinical text</span>
                    <textarea
                      rows={11}
                      value={textInput}
                      onChange={(event) => setTextInput(event.target.value)}
                      placeholder="Enter clinical note text here..."
                    />
                  </label>

                  <div className="button-row">
                    <button className="button button--primary" type="submit">
                      Analyze Text
                    </button>
                    <button
                      className="button button--secondary"
                      type="button"
                      onClick={() => setTextInput(sampleText)}
                    >
                      Load Sample
                    </button>
                  </div>
                </form>
              ) : (
                <form className="input-form" onSubmit={handleFileSubmit}>
                  <div className="panel-label">File Upload</div>
                  <h2>Analyze an uploaded image</h2>
                  <p className="panel-copy">
                    Upload a JPG or PNG image. The backend will extract text with OCR and
                    run the same ICD-10 coding pipeline.
                  </p>

                  <label className="input-group">
                    <span>Image file</span>
                    <div className="upload-box">
                      <input type="file" accept=".jpg,.jpeg,.png,image/png,image/jpeg" onChange={handleFileChange} />
                      <div className="upload-box__meta">
                        <strong>{selectedFile ? selectedFile.name : "No file selected"}</strong>
                        <span>Supported formats: JPG, JPEG, PNG</span>
                      </div>
                    </div>
                  </label>

                  <div className="button-row">
                    <button className="button button--primary" type="submit">
                      Upload and Analyze
                    </button>
                    <button
                      className="button button--secondary"
                      type="button"
                      onClick={() => {
                        setSelectedFile(null);
                        setStatus("idle");
                        setMessage("");
                      }}
                    >
                      Clear File
                    </button>
                  </div>
                </form>
              )}

              <StatusBanner kind={status} message={message} />
            </section>

            <section className="results-panel-wrap">
              <ResultPanel
                data={result}
                title="Prediction Results"
                emptyMessage="Submit text or upload an image to see mapped ICD-10 suggestions here."
              />
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}
