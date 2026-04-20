import type { PredictionResponse } from "../lib/api";

interface ResultPanelProps {
  data: PredictionResponse | null;
  title: string;
  emptyMessage: string;
}

function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

function formatReviewStatus(reviewStatus: PredictionResponse["review_status"]): string {
  return reviewStatus === "auto_suggested" ? "Auto Suggested" : "Needs Review";
}

export function ResultPanel({ data, title, emptyMessage }: ResultPanelProps) {
  if (!data) {
    return (
      <section className="result-panel result-panel--empty">
        <div className="section-label">Results</div>
        <h3>{title}</h3>
        <p>{emptyMessage}</p>
      </section>
    );
  }

  return (
    <section className="result-panel">
      <div className="section-label">Results</div>
      <div className="result-panel__header">
        <h3>{title}</h3>
        <div className="result-panel__header-meta">
          <span className={`review-chip review-chip--${data.review_status}`}>
            {formatReviewStatus(data.review_status)}
          </span>
          <span className="result-chip">
            {data.codes.length} {data.codes.length === 1 ? "code" : "codes"}
          </span>
        </div>
      </div>

      <p className="result-explanation">{data.explanation}</p>

      <div className="result-grid">
        {data.codes.length > 0 ? (
          data.codes.map((code) => (
            <article key={code.code} className="code-card">
              <div className="code-card__top">
                <span className="code-card__code">{code.code}</span>
                <span className="code-card__confidence">
                  {formatConfidence(code.confidence)}
                </span>
              </div>
              <h4>{code.description}</h4>
            </article>
          ))
        ) : (
          <div className="no-match-card">
            <h4>No curated ICD-10 match found</h4>
            <p>The system did not find a mapped starter-dataset code for this submission.</p>
          </div>
        )}
      </div>

      {data.extracted_conditions.length > 0 ? (
        <section className="review-section">
          <div className="section-label">Extracted Conditions</div>
          <div className="review-list">
            {data.extracted_conditions.map((condition, index) => (
              <article
                key={`${condition.name}-${condition.evidence || "no-evidence"}-${index}`}
                className="review-card"
              >
                <div className="review-card__top">
                  <h4>{condition.name}</h4>
                  <span className="review-card__confidence">
                    {formatConfidence(condition.confidence)}
                  </span>
                </div>
                <p>{condition.evidence || "No evidence phrase returned from extraction."}</p>
                <div className="review-card__footer">
                  <span>
                    {condition.mapped_code
                      ? `Mapped to ${condition.mapped_code}`
                      : "No curated match"}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {data.unmatched_conditions.length > 0 ? (
        <section className="review-section">
          <div className="section-label">Needs Review</div>
          <div className="review-warning">
            <h4>Unmatched extracted conditions</h4>
            <p>{data.unmatched_conditions.join(", ")}</p>
          </div>
        </section>
      ) : null}
    </section>
  );
}
