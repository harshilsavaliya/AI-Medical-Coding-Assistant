import type { PredictionResponse } from "../lib/api";

interface ResultPanelProps {
  data: PredictionResponse | null;
  title: string;
  emptyMessage: string;
}

function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
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
        <span className="result-chip">
          {data.codes.length} {data.codes.length === 1 ? "code" : "codes"}
        </span>
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
    </section>
  );
}
