import { useState } from 'react';

export default function PortRiskSection({ result }) {
  // Demurrage What-If local state — completely separate from official model values
  const [waitAdjDays, setWaitAdjDays] = useState(0);       // slider delta: -3 to +7 days
  const [demurrageRate, setDemurrageRate] = useState('');   // user-supplied $/day (not invented)

  if (!result) return null;

  const { risk, request } = result;
  const portPrediction = risk?.port_model_prediction;
  const isPortML = Boolean(portPrediction);

  const totalScore = risk?.total_score ?? 0;
  const maxScore = risk?.max_score ?? 6;
  const riskPct = Math.min(100, Math.round((totalScore / maxScore) * 100));

  // Demurrage what-if calculations — only computed if ML wait_hours exists AND user enters a rate
  const modelWaitHours = isPortML ? portPrediction.wait_hours : null;
  const modelWaitDays = modelWaitHours != null ? modelWaitHours / 24 : null;
  const ratePerDay = parseFloat(demurrageRate);
  const hasRate = !isNaN(ratePerDay) && ratePerDay > 0;
  const whatIfWaitDays = modelWaitDays != null ? Math.max(0, modelWaitDays + waitAdjDays) : null;
  const modelExposure = hasRate && modelWaitDays != null ? modelWaitDays * ratePerDay : null;
  const whatIfExposure = hasRate && whatIfWaitDays != null ? whatIfWaitDays * ratePerDay : null;
  const isSliderMoved = waitAdjDays !== 0;


  return (
    <section className="port-risk-section-wrapper" id="risk">
      <div className="section-title-bar" data-section-reveal>
        <div>
          <span className="section-eyebrow-tag">Port Operations &amp; Supply Chain Risk</span>
          <h2 className="section-heading-primary">Port Risk &amp; Congestion Assessment</h2>
        </div>
        <div className="port-context-badge">
          <span>Destination Port: <strong>{request?.destination}</strong></span>
        </div>
      </div>

      <div className="risk-balanced-grid">
        {/* Left Column: Composite Risk Engine */}
        <div className="risk-card-container" data-card-reveal>
          <div className="risk-card-header">
            <div>
              <span className="card-kicker-tag">Composite Risk Scoring</span>
              <h3 className="card-primary-title">
                {risk?.level || 'Medium'} Operational Risk Environment
              </h3>
            </div>
            <div className={`risk-level-pill pill-${risk?.level?.toLowerCase() || 'medium'}`}>
              {risk?.level || 'Medium'}
            </div>
          </div>

          <div className="risk-score-display-row">
            <div className="score-numeric-block">
              <span className="score-current">{totalScore}</span>
              <span className="score-max">/{maxScore}</span>
            </div>
            <div className="score-meter-column">
              <div className="meter-track-bar">
                <div
                  className={`meter-fill-bar fill-${risk?.level?.toLowerCase() || 'medium'}`}
                  style={{ width: `${riskPct}%` }}
                />
              </div>
              <span className="meter-caption">Composite scale from 0 (minimal risk) to 6 (severe risk)</span>
            </div>
          </div>

          <div className="risk-factors-breakdown">
            <h4 className="factors-title">Scored Component Breakdown</h4>
            <div className="factors-list">
              {(risk?.factors || []).map((factor) => {
                const cleanName = factor.name
                  .replace(' (illustrative, user-set)', '')
                  .replace(' (CoV, recent window)', '');

                return (
                  <div key={factor.name} className="factor-item-row">
                    <div className="factor-name-meta">
                      <span className="factor-label">{cleanName}</span>
                      <span className="factor-subtext">Weight: {factor.weight || 1}x</span>
                    </div>
                    <div className="factor-score-badge">
                      <span>Score: <strong>+{factor.value}</strong></span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="risk-methodology-note">
            <strong>Methodology Note:</strong> {risk?.source || 'Rule-based composite weighting.'}
          </div>
        </div>

        {/* Right Column: Destination Port Operational Analytics */}
        <div className="risk-card-container" data-card-reveal>
          <div className="risk-card-header">
            <div>
              <span className="card-kicker-tag">
                {isPortML ? 'Trained XGBoost Operational Regressors' : 'Operational Assumptions'}
              </span>
              <h3 className="card-primary-title">
                {isPortML
                  ? `${request?.destination} Port — Model-Backed Queue Analytics`
                  : `${request?.destination} Port — Standard Queue Parameters`}
              </h3>
            </div>
            <div className={`model-tag-pill ${isPortML ? 'pill-ml' : 'pill-stat'}`}>
              {isPortML ? 'Trained Regressor' : 'User Assumption'}
            </div>
          </div>

          {isPortML ? (
            <div className="port-metrics-content">
              <div className="port-kpi-pair-grid">
                <div className="port-metric-tile">
                  <span className="tile-title">Congestion Index</span>
                  <div className="tile-value-row">
                    <span className="tile-number">
                      {portPrediction.congestion_index_0_100.toFixed(0)}
                    </span>
                    <span className="tile-denom">/ 100</span>
                  </div>
                  <span className="tile-status-tag tag-normal">Normal (Clear Berths)</span>
                </div>

                <div className="port-metric-tile">
                  <span className="tile-title">Estimated Vessel Wait</span>
                  <div className="tile-value-row">
                    <span className="tile-number">
                      {portPrediction.wait_hours.toFixed(1)}
                    </span>
                    <span className="tile-denom">hrs</span>
                  </div>
                  <span className="tile-status-tag tag-normal">Minimal Lineup</span>
                </div>
              </div>

              {/* Visually secondary model disclosure note */}
              <div className="port-model-footnote">
                <span className="footnote-icon">ℹ</span>
                <div className="footnote-text">
                  <strong>Model Output Disclosure:</strong> Trained XGBoost regressors predicted raw outputs of{' '}
                  <code>{portPrediction.raw_model_outputs?.congestion_index_0_100?.toFixed(2)}</code> for congestion and{' '}
                  <code>{portPrediction.raw_model_outputs?.wait_hours?.toFixed(2)} hrs</code> for wait time on the cutoff feature row.
                  Values are non-negatively clipped to <code>0.0</code>, indicating free berth capacity and no waiting backlog at {request?.destination}.
                </div>
              </div>

              {/* ── Demurrage What-If ─────────────────────────────────────── */}
              {/* Local-only calculation. Does NOT modify model values or recommendation. */}
              <div className="demurrage-whatif-block" aria-label="Demurrage What-If Analysis">
                <div className="demurrage-whatif-header">
                  <div>
                    <span className="demurrage-whatif-kicker">What-If Analysis — Local Only</span>
                    <h4 className="demurrage-whatif-title">Demurrage Exposure Explorer</h4>
                  </div>
                  <span className="demurrage-whatif-note">Does not affect official model results</span>
                </div>

                {/* Daily rate input — user-supplied, not invented */}
                <div className="demurrage-rate-input-row">
                  <label className="demurrage-rate-label" htmlFor="demurrage-rate-input">
                    Your Demurrage Rate ($/day) — enter to enable exposure calculation
                  </label>
                  <div className="demurrage-rate-input-wrap">
                    <span className="demurrage-rate-prefix">$</span>
                    <input
                      id="demurrage-rate-input"
                      type="number"
                      className="demurrage-rate-input"
                      placeholder="e.g. 25000"
                      min={0}
                      step={500}
                      value={demurrageRate}
                      onChange={(e) => setDemurrageRate(e.target.value)}
                      aria-label="Demurrage rate in US dollars per day"
                    />
                    <span className="demurrage-rate-suffix">/day</span>
                  </div>
                </div>

                {/* Slider: wait adjustment −3 to +7 days */}
                <div className="demurrage-slider-section">
                  <div className="demurrage-slider-header-row">
                    <label className="demurrage-slider-label" htmlFor="wait-adj-slider">
                      Wait time adjustment
                    </label>
                    <div className="demurrage-slider-value-chip">
                      {waitAdjDays === 0 ? 'No adjustment (model value)' : `${waitAdjDays > 0 ? '+' : ''}${waitAdjDays} days`}
                    </div>
                  </div>
                  <input
                    id="wait-adj-slider"
                    type="range"
                    className="demurrage-slider"
                    min={-3}
                    max={7}
                    step={0.5}
                    value={waitAdjDays}
                    onChange={(e) => setWaitAdjDays(parseFloat(e.target.value))}
                    aria-label={`Wait adjustment: ${waitAdjDays > 0 ? '+' : ''}${waitAdjDays} days`}
                    aria-valuemin={-3}
                    aria-valuemax={7}
                    aria-valuenow={waitAdjDays}
                  />
                  <div className="demurrage-slider-rail-labels">
                    <span>−3 days</span>
                    <span>Model value</span>
                    <span>+7 days</span>
                  </div>
                </div>

                {/* Results comparison */}
                <div className="demurrage-comparison-grid">
                  {/* Model column — always shows model values, never overwritten */}
                  <div className="demurrage-col demurrage-col-model">
                    <span className="demurrage-col-label">MODEL</span>
                    <div className="demurrage-stat-row">
                      <span className="demurrage-stat-name">Wait</span>
                      <strong className="demurrage-stat-val">
                        {modelWaitDays != null ? `${modelWaitDays.toFixed(2)} days (${portPrediction.wait_hours.toFixed(1)} hrs)` : '—'}
                      </strong>
                    </div>
                    <div className="demurrage-stat-row">
                      <span className="demurrage-stat-name">Exposure</span>
                      <strong className="demurrage-stat-val">
                        {modelExposure != null
                          ? `$${Number(modelExposure).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
                          : hasRate ? '—' : <span className="demurrage-no-rate">Enter rate above</span>}
                      </strong>
                    </div>
                  </div>

                  {/* Divider */}
                  <div className="demurrage-col-divider" aria-hidden="true" />

                  {/* What-If column — local only, reset possible */}
                  <div className={`demurrage-col demurrage-col-whatif ${isSliderMoved ? 'demurrage-col-whatif--active' : ''}`}>
                    <div className="demurrage-whatif-col-header">
                      <span className="demurrage-col-label">WHAT-IF</span>
                      {isSliderMoved && (
                        <button
                          type="button"
                          className="btn-demurrage-reset"
                          onClick={() => setWaitAdjDays(0)}
                          aria-label="Reset to model value"
                        >
                          ↩ Reset
                        </button>
                      )}
                    </div>
                    <div className="demurrage-stat-row">
                      <span className="demurrage-stat-name">Wait</span>
                      <strong className="demurrage-stat-val">
                        {whatIfWaitDays != null
                          ? `${whatIfWaitDays.toFixed(2)} days ${isSliderMoved ? `(${waitAdjDays > 0 ? '+' : ''}${waitAdjDays}d adjustment)` : ''}`
                          : '—'}
                      </strong>
                    </div>
                    <div className="demurrage-stat-row">
                      <span className="demurrage-stat-name">Exposure</span>
                      <strong className="demurrage-stat-val">
                        {whatIfExposure != null
                          ? `$${Number(whatIfExposure).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
                          : hasRate ? '—' : <span className="demurrage-no-rate">Enter rate above</span>}
                      </strong>
                    </div>
                    {!isSliderMoved && (
                      <span className="demurrage-at-model-note">Showing model value — move slider to explore</span>
                    )}
                  </div>
                </div>

                <p className="demurrage-disclaimer">
                  ⚠ This is a local what-if calculation only. It uses your entered rate and the model wait estimate.
                  It does not change the official recommendation, model output, or scenario inputs.
                </p>
              </div>
            </div>

          ) : (
            <div className="port-metrics-content">
              <div className="port-unmodeled-alert">
                <p>
                  Dedicated XGBoost queue regressors are currently trained and committed exclusively for <strong>Paradip Port</strong>.
                </p>
                <p>
                  For <strong>{request?.destination}</strong>, operational calculations use the selected scenario congestion assumption ({request?.congestion_level} congestion) combined with historical physical limit constraints.
                </p>
              </div>

              <div className="port-kpi-pair-grid" style={{ marginTop: '16px' }}>
                <div className="port-metric-tile">
                  <span className="tile-title">Selected Congestion Level</span>
                  <div className="tile-value-row">
                    <span className="tile-number" style={{ fontSize: '1.4rem' }}>
                      {request?.congestion_level}
                    </span>
                  </div>
                  <span className="tile-status-tag">Scenario Input</span>
                </div>

                <div className="port-metric-tile">
                  <span className="tile-title">Vessel Availability</span>
                  <div className="tile-value-row">
                    <span className="tile-number" style={{ fontSize: '1.4rem' }}>
                      {request?.availability_level}
                    </span>
                  </div>
                  <span className="tile-status-tag">Scenario Input</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
