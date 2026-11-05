import { useState } from 'react';

export default function MethodologySection({ result }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!result) return null;

  const { forecast, risk } = result;
  const model = forecast?.model || {};
  const portPrediction = risk?.port_model_prediction;

  return (
    <section className="methodology-compact-section" id="methodology">
      <div className="methodology-card-compact">
        <div className="methodology-header-row">
          <div className="methodology-lead-col">
            <span className="section-eyebrow-tag">Audit &amp; Methodology</span>
            <h3 className="methodology-compact-title">Model Provenance &amp; Data Pipeline Integrity</h3>
            <p className="methodology-compact-desc">
              All forecasts, port risk ratings, and chartering decisions are generated deterministically with full provenance disclosure.
            </p>
          </div>
          <button
            type="button"
            className="btn-toggle-methodology"
            onClick={() => setIsOpen((prev) => !prev)}
          >
            {isOpen ? 'Collapse Technical Audit ▲' : 'Inspect Technical Audit & Limitations ▼'}
          </button>
        </div>

        {/* Provenance Pills Row Always Visible */}
        <div className="provenance-badges-strip">
          <div className="badge-item">
            <span className="badge-prefix">Freight Pipeline:</span>
            <strong className={`badge-pill ${model.fallback_used ? 'badge-stat' : 'badge-ml'}`}>
              {model.name} ({model.fallback_used ? 'Holt Statistical Baseline' : 'Trained PyTorch/XGBoost ML'})
            </strong>
          </div>
          <div className="badge-item">
            <span className="badge-prefix">Port Congestion:</span>
            <strong className={`badge-pill ${portPrediction ? 'badge-ml' : 'badge-rule'}`}>
              {portPrediction ? 'Trained XGBoost Regressor' : 'Rule-Based Operational Composite'}
            </strong>
          </div>
          <div className="badge-item">
            <span className="badge-prefix">Data Sourcing:</span>
            <strong className="badge-pill badge-synthetic">
              Macro Benchmark Data + GBM Simulated Freight Proxy
            </strong>
          </div>
        </div>

        {/* Expandable Technical Drawer */}
        {isOpen && (
          <div className="methodology-details-drawer">
            <div className="drawer-grid">
              {/* Technical Facts */}
              <div className="drawer-card">
                <h4 className="drawer-card-title">Model Scope &amp; Artifact Details</h4>
                <div className="drawer-facts-list">
                  <div className="drawer-fact-row">
                    <span className="fact-key">Execution Type:</span>
                    <span className="fact-val">{model.kind?.replaceAll('_', ' ')}</span>
                  </div>
                  <div className="drawer-fact-row">
                    <span className="fact-key">Committed Artifact:</span>
                    <span className="fact-val">{model.artifact || 'None (In-Memory Baseline)'}</span>
                  </div>
                  <div className="drawer-fact-row">
                    <span className="fact-key">Dataset Cutoff:</span>
                    <span className="fact-val">{model.data_cutoff || '2026-09-11'}</span>
                  </div>
                  <div className="drawer-fact-row">
                    <span className="fact-key">Interval Method:</span>
                    <span className="fact-val">{model.interval_method}</span>
                  </div>
                  <div className="drawer-fact-row">
                    <span className="fact-key">Calibrated Interval:</span>
                    <span className="fact-val">{model.interval_calibrated ? 'Yes' : 'No (Indicative Gaussian Approximation)'}</span>
                  </div>
                </div>
              </div>

              {/* Known Limitations */}
              <div className="drawer-card">
                <h4 className="drawer-card-title">Documented Model Limitations</h4>
                <ul className="drawer-limitations-list">
                  {(model.known_limitations || [
                    'Historical freight rates are GBM-generated synthetic proxies rather than live Baltic Exchange feeds.',
                    'Port operational rows are simulated benchmarks.',
                  ]).map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
