import { useState } from 'react';
import { formatFeasibilityStatus } from '../utils/statusHelpers';
import { exportBrief } from '../utils/generateBrief';

// Scroll to a section by its id
function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

export default function DecisionSection({ result, onRunAgain, isStale }) {
  const [reasonIndex, setReasonIndex] = useState(0);
  const [whyOpen, setWhyOpen] = useState(false);
  const [exportState, setExportState] = useState('idle'); // idle | loading | success | error

  if (!result) return null;

  const { recommendation, forecast, risk, feasibility, request } = result;
  const reasons = (recommendation?.reasons || []).map((r) => r.replaceAll('\\$', '$'));

  const cleanIdx = reasons.length ? reasonIndex % reasons.length : 0;
  const isCharterNow = recommendation?.decision === 'Charter Now';

  const nextReason = () => {
    if (reasons.length) setReasonIndex((prev) => (prev + 1) % reasons.length);
  };

  const prevReason = () => {
    if (reasons.length) setReasonIndex((prev) => (prev - 1 + reasons.length) % reasons.length);
  };

  const feasInfo = formatFeasibilityStatus(
    recommendation?.selected_feasibility || feasibility?.selected?.overall
  );

  // Determine if the voyage is physically impossible
  const isNonFeasible = feasInfo.status === 'fail';

  // Build contextual "why" decision drivers from actual result data
  const decisionDrivers = [];
  if (forecast?.expected_pct_change != null) {
    const pct = forecast.expected_pct_change;
    decisionDrivers.push({
      label: 'Forward rate trend',
      value: `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}% vs current (${forecast.horizon_days}d horizon)`,
      sentiment: pct > 0 ? 'bearish' : 'bullish', // rate going up → charter now
      section: 'forecast',
    });
  }
  if (forecast?.probability_increase != null) {
    const prob = Math.round(forecast.probability_increase * 100);
    decisionDrivers.push({
      label: 'Rate upside probability',
      value: `${prob}% chance rates rise over the horizon`,
      sentiment: prob > 55 ? 'bearish' : prob < 45 ? 'bullish' : 'neutral',
      section: 'forecast',
    });
  }
  if (risk?.level) {
    decisionDrivers.push({
      label: 'Port operational risk',
      value: `${risk.level} risk environment (${risk.total_score ?? '—'}/${risk.max_score ?? 6} composite score)`,
      sentiment: risk.level === 'High' ? 'bearish' : risk.level === 'Low' ? 'bullish' : 'neutral',
      section: 'risk',
    });
  }
  if (feasInfo) {
    decisionDrivers.push({
      label: 'Vessel-port compatibility',
      value: feasInfo.summaryText,
      sentiment: feasInfo.status === 'fail' ? 'bearish' : feasInfo.status === 'pass' ? 'bullish' : 'neutral',
      section: 'feasibility',
    });
  }

  return (
    <section className="decision-section-wrapper" id="decision">
      <div className="section-title-bar" data-section-reveal>
        <div>
          <span className="section-eyebrow-tag">Procurement Action</span>
          <h2 className="section-heading-primary">Chartering Decision &amp; Rationale</h2>
        </div>
        <div className="scenario-summary-pill">
          <span>{request?.origin} &rarr; {request?.destination}</span>
          <span>&middot;</span>
          <span>{request?.vessel_class}</span>
          <span>&middot;</span>
          <span>{Number(request?.cargo_quantity_mt || 0).toLocaleString()} MT</span>
        </div>
      </div>

      {/* Non-feasible voyage alert — shown prominently when the vessel physically cannot dock */}
      {isNonFeasible && (
        <div className="infeasible-voyage-alert" role="alert" data-card-reveal>
          <div className="infeasible-alert-icon" aria-hidden="true">⊘</div>
          <div className="infeasible-alert-body">
            <strong className="infeasible-alert-heading">No viable charter for this vessel and port</strong>
            <p className="infeasible-alert-detail">
              The selected <strong>{request?.vessel_class}</strong> vessel fails one or more physical berth constraints
              at <strong>{request?.destination}</strong>. A standard Spot, Time Charter, or COA cannot be recommended
              on this configuration — the vessel cannot discharge a full cargo.
            </p>
            <p className="infeasible-alert-action">
              Review the Feasibility &amp; Cost section below for the specific failed constraint,
              then try a smaller vessel class or a deeper-draught destination port.
            </p>
            <div className="infeasible-cta-row">
              <button type="button" className="btn-infeasible-review" onClick={() => scrollToSection('feasibility')}>
                View Feasibility Detail
              </button>
              <button type="button" className="btn-infeasible-modify" onClick={onRunAgain}>
                Modify Scenario
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="decision-split-grid">
        {/* Left Column: Recommendation Verdict & Rationale */}
        <div className="decision-card-container highlight-verdict-card" data-card-reveal>
          <div className="verdict-banner-row">
            <span className="verdict-kicker">Recommended Action</span>
            {isNonFeasible ? (
              <div className="verdict-stamp stamp-infeasible">Physical Limits Exceeded</div>
            ) : (
              <div className={`verdict-stamp ${isCharterNow ? 'stamp-charter' : 'stamp-wait'}`}>
                {recommendation?.decision || 'Review Scenario'}
              </div>
            )}
          </div>

          {!isNonFeasible && (
            <div className="recommended-structure-box">
              <span className="structure-caption">Target Execution Structure:</span>
              <strong className="structure-value">{recommendation?.contract_strategy}</strong>
            </div>
          )}

          <div className="decision-badges-row">
            <div className="decision-badge-tile">
              <span className="badge-caption">Risk Assessment:</span>
              <strong className={`badge-state-text state-${recommendation?.risk_level?.toLowerCase() || 'medium'}`}>
                {recommendation?.risk_level || 'Medium'} Risk
              </strong>
            </div>
            <div className="decision-badge-tile">
              <span className="badge-caption">Vessel Port Fit:</span>
              <strong className={`badge-state-text ${feasInfo.stateTextClass}`}>
                {feasInfo.summaryText}
              </strong>
            </div>
          </div>

          {/* Rationale Carousel — only shown when voyage is viable */}
          {!isNonFeasible && reasons.length > 0 && (
            <div className="decision-rationale-box">
              <div className="rationale-top-row">
                <span className="rationale-heading">Driver Rationale ({cleanIdx + 1} of {reasons.length}):</span>
                <div className="rationale-nav-buttons">
                  <button
                    type="button"
                    className="btn-nav-reason"
                    onClick={prevReason}
                    aria-label="Previous reason"
                  >
                    &larr;
                  </button>
                  <button
                    type="button"
                    className="btn-nav-reason"
                    onClick={nextReason}
                    aria-label="Next reason"
                  >
                    &rarr;
                  </button>
                </div>
              </div>
              <p className="rationale-quote-text">
                &ldquo;{reasons[cleanIdx]}&rdquo;
              </p>
            </div>
          )}

          {/* Why This Recommendation — expandable */}
          {!isNonFeasible && decisionDrivers.length > 0 && (
            <div className="why-recommendation-section">
              <button
                type="button"
                className="btn-why-recommendation"
                aria-expanded={whyOpen}
                onClick={() => setWhyOpen((v) => !v)}
              >
                <span>{whyOpen ? 'Hide' : 'Why this recommendation?'}</span>
                <svg
                  viewBox="0 0 20 20" width="14" height="14" fill="currentColor" aria-hidden="true"
                  style={{ transform: whyOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
                >
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>

              {whyOpen && (
                <div className="why-drivers-list" role="region" aria-label="Decision drivers">
                  {decisionDrivers.map((driver) => (
                    <div key={driver.label} className="why-driver-row">
                      <div className="why-driver-meta">
                        <span className="why-driver-label">{driver.label}</span>
                        <span className={`why-driver-sentiment sentiment-${driver.sentiment}`}>
                          {driver.sentiment === 'bearish' ? '↑ urges charter' : driver.sentiment === 'bullish' ? '↓ allows wait' : '• neutral'}
                        </span>
                      </div>
                      <div className="why-driver-value-row">
                        <span className="why-driver-value">{driver.value}</span>
                        {driver.section && (
                          <button
                            type="button"
                            className="btn-why-section-link"
                            onClick={() => scrollToSection(driver.section)}
                            aria-label={`Go to ${driver.section} section`}
                          >
                            View ↗
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Scenario Synthesis & Actions */}
        <div className="decision-card-container" data-card-reveal>
          <div className="verdict-banner-row">
            <span className="verdict-kicker">Scenario Synthesis</span>
            <span className="parameters-caption">Validated Pipeline Metrics</span>
          </div>

          <div className="scenario-recap-grid">
            <div className="recap-tile">
              <span className="recap-label">Spot Rate Cutoff</span>
              <strong className="recap-val">${forecast?.current_rate_usd_per_mt?.toFixed(2)}/MT</strong>
            </div>
            <div className="recap-tile">
              <span className="recap-label">P50 Forward Median</span>
              <strong className="recap-val">${forecast?.p50_usd_per_mt?.toFixed(2)}/MT</strong>
            </div>
            <div className="recap-tile">
              <span className="recap-label">P10 Low Case</span>
              <strong className="recap-val">${forecast?.p10_usd_per_mt?.toFixed(2)}/MT</strong>
            </div>
            <div className="recap-tile">
              <span className="recap-label">P90 High Case</span>
              <strong className="recap-val">${forecast?.p90_usd_per_mt?.toFixed(2)}/MT</strong>
            </div>
            <div className="recap-tile">
              <span className="recap-label">Cargo Requirement</span>
              <strong className="recap-val">{Number(request?.cargo_quantity_mt || 0).toLocaleString()} MT</strong>
            </div>
            <div className="recap-tile">
              <span className="recap-label">Rate Upside Prob.</span>
              <strong className="recap-val">{Math.round((forecast?.probability_increase || 0) * 100)}%</strong>
            </div>
          </div>

          <div className="decision-action-box">
            <p className="action-hint-text">
              Adjust route parameters, vessel classes, or cargo tonnages to evaluate alternative chartering strategies.
            </p>
            <button
              type="button"
              className="btn-reconfigure-scenario"
              onClick={onRunAgain}
            >
              <span>Modify Route Scenario &amp; Rerun</span>
              <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
            </button>

            {/* Export Brief — disabled when results are stale */}
            <button
              type="button"
              className={`btn-export-brief ${isStale ? 'btn-export-brief--disabled' : ''}`}
              disabled={isStale || exportState === 'loading'}
              title={isStale ? 'Re-run analysis before exporting — current results are stale' : 'Export a PDF-ready chartering brief'}
              onClick={async () => {
                setExportState('loading');
                try {
                  await exportBrief(result);
                  setExportState('success');
                  setTimeout(() => setExportState('idle'), 3000);
                } catch (err) {
                  console.error('[SamudraSetu] Export failed:', err);
                  setExportState('error');
                  setTimeout(() => setExportState('idle'), 4000);
                }
              }}
            >
              {exportState === 'loading' && <span className="loading-spinner-ring" style={{ width: 14, height: 14, borderWidth: 2 }} />}
              {exportState === 'loading' && <span>Generating...</span>}
              {exportState === 'success' && <span>✓ Brief Opened</span>}
              {exportState === 'error' && <span>✗ Export Failed — allow pop-ups &amp; retry</span>}
              {exportState === 'idle' && (
                <>
                  <svg viewBox="0 0 20 20" width="14" height="14" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span>Export Brief{isStale ? ' (Stale)' : ''}</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
