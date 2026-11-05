import { formatFeasibilityStatus } from '../utils/statusHelpers';

export default function ExecutiveStrip({ result, isStale }) {
  if (!result) return null;

  const { forecast, feasibility, risk, request } = result;
  const portPrediction = risk?.port_model_prediction;

  const currentRate = forecast?.current_rate_usd_per_mt ?? 0;
  const p50 = forecast?.p50_usd_per_mt ?? 0;
  const pctChange = forecast?.expected_pct_change ?? 0;
  const probIncrease = forecast?.probability_increase ?? 0;
  const horizon = forecast?.horizon_days ?? 7;

  const isUp = pctChange >= 0;

  // Port Congestion display & explanation
  const isPortML = Boolean(portPrediction);
  const congestionIndex = isPortML
    ? portPrediction.congestion_index_0_100
    : risk?.requested_congestion_level || request?.congestion_level || 'Medium';

  const waitHours = isPortML
    ? portPrediction.wait_hours
    : null;

  const feasInfo = formatFeasibilityStatus(feasibility?.selected?.overall);

  return (
    <section className="executive-strip-container" id="overview">
      <div className="section-title-bar" data-section-reveal>
        <div>
          <span className="section-eyebrow-tag">Executive Summary</span>
          <h2 className="section-heading-primary">Key Operational &amp; Market Metrics</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {isStale && (
            <span className="stale-section-badge" aria-label="Results are stale — inputs have changed">
              <span aria-hidden="true">⚠</span> Stale Results
            </span>
          )}
          <div className="scenario-summary-pill">
            <span>{request?.origin} &rarr; {request?.destination}</span>
            <span>&middot;</span>
            <span>{request?.vessel_class}</span>
            <span>&middot;</span>
            <span>{Number(request?.cargo_quantity_mt || 0).toLocaleString()} MT</span>
          </div>
        </div>
      </div>


      <div className="metrics-strip-grid">
        {/* Metric 1: Current Rate */}
        <div className="metric-strip-card" data-card-reveal>
          <div className="metric-card-label">Current Spot Rate</div>
          <div className="metric-primary-value">
            ${currentRate.toFixed(2)}
            <span className="metric-unit-text">/mt</span>
          </div>
          <div className="metric-supporting-note">
            Coal freight benchmark cutoff
          </div>
        </div>

        {/* Metric 2: P50 Forecast */}
        <div className="metric-strip-card" data-card-reveal>
          <div className="metric-card-label">P50 Forecast ({horizon}d Horizon)</div>
          <div className="metric-primary-value">
            ${p50.toFixed(2)}
            <span className="metric-unit-text">/mt</span>
          </div>
          <div className={`metric-delta-tag ${isUp ? 'delta-positive' : 'delta-negative'}`}>
            <span>{isUp ? '▲' : '▼'} {Math.abs(pctChange).toFixed(1)}%</span>
            <span className="delta-basis">vs current rate</span>
          </div>
        </div>

        {/* Metric 3: Probability of Increase */}
        <div className="metric-strip-card" data-card-reveal>
          <div className="metric-card-label">Rate Upside Probability</div>
          <div className="metric-primary-value">
            {Math.round(probIncrease * 100)}%
          </div>
          <div className="metric-progress-track">
            <div
              className="metric-progress-fill"
              style={{ width: `${Math.round(probIncrease * 100)}%` }}
            />
          </div>
          <div className="metric-supporting-note">
            Probability rates will rise
          </div>
        </div>

        {/* Metric 4: Port Congestion */}
        <div className="metric-strip-card" data-card-reveal>
          <div className="metric-card-label">
            Port Congestion ({request?.destination})
          </div>
          <div className="metric-primary-value">
            {isPortML ? (
              <>
                {congestionIndex.toFixed(0)}
                <span className="metric-unit-text">/ 100</span>
              </>
            ) : (
              <span className="metric-text-badge">{congestionIndex}</span>
            )}
          </div>
          <div className="metric-supporting-note">
            {isPortML ? (
              <span title={`Raw model output: ${portPrediction.raw_model_outputs?.congestion_index_0_100?.toFixed(2) || '0'}`}>
                Trained XGBoost regressor (Minimal queue)
              </span>
            ) : (
              'User operational assumption'
            )}
          </div>
        </div>

        {/* Metric 5: Vessel Wait Time */}
        <div className="metric-strip-card" data-card-reveal>
          <div className="metric-card-label">Estimated Vessel Wait</div>
          <div className="metric-primary-value">
            {isPortML ? (
              <>
                {waitHours.toFixed(1)}
                <span className="metric-unit-text">hrs</span>
              </>
            ) : (
              <span className="metric-text-badge">N/A</span>
            )}
          </div>
          <div className="metric-supporting-note">
            {isPortML ? (
              <span title={`Raw model output: ${portPrediction.raw_model_outputs?.wait_hours?.toFixed(2) || '0'} hrs`}>
                Trained regressor (Free berth)
              </span>
            ) : (
              'No port ML model for this port'
            )}
          </div>
        </div>

        {/* Metric 6: Composite Risk */}
        <div className="metric-strip-card" data-card-reveal>
          <div className="metric-card-label">Composite Risk Index</div>
          <div className="metric-primary-value">
            {risk?.total_score ?? '—'}
            <span className="metric-unit-text">/{risk?.max_score ?? 6}</span>
          </div>
          <div className={`risk-level-badge risk-${risk?.level?.toLowerCase() || 'medium'}`}>
            {risk?.level || 'Medium'} Risk
          </div>
        </div>

        {/* Metric 7: Port Feasibility */}
        <div className="metric-strip-card" data-card-reveal>
          <div className="metric-card-label">Port Fit ({request?.vessel_class})</div>
          <div className="metric-primary-value" style={{ fontSize: '1.25rem' }}>
            {request?.destination}
          </div>
          <div className={`feasibility-badge ${feasInfo.badgeClass}`}>
            {feasInfo.label}
          </div>
        </div>
      </div>
    </section>
  );
}
