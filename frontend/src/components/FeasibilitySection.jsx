import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import { formatFeasibilityStatus } from '../utils/statusHelpers';

function CostBarTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const item = payload[0]?.payload || {};

  return (
    <div className="forecast-chart-tooltip">
      <div className="tooltip-date-header">{label}</div>
      <div className="tooltip-data-row">
        <span className="tooltip-metric-name">Modeled Rate:</span>
        <strong className="tooltip-metric-value">${Number(item.rate).toFixed(2)}/MT</strong>
      </div>
      <div className="tooltip-data-row">
        <span className="tooltip-metric-name">Total Contract Cost:</span>
        <strong className="tooltip-metric-value">
          ${Number(item.totalCost).toLocaleString('en-US', { maximumFractionDigits: 0 })}
        </strong>
      </div>
    </div>
  );
}

export default function FeasibilitySection({ result }) {
  if (!result) return null;

  const { feasibility, recommendation, backtest, request } = result;
  const candidates = feasibility?.candidates || [];
  const selectedVessel = feasibility?.selected?.vessel_class || request?.vessel_class;
  const costOptions = recommendation?.cost_options || [];

  const chartData = costOptions.map((opt) => ({
    name: opt.name,
    totalCost: opt.total_cost_usd,
    rate: opt.rate_usd_per_mt,
    isLowest: opt.is_lowest_modeled_cost,
  }));

  const formatCurrency = (val) => {
    if (!val && val !== 0) return '—';
    if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
    if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`;
    return `$${Number(val).toFixed(0)}`;
  };

  const selectedFeasibility = feasibility?.selected?.overall;
  const isSelectedFail = selectedFeasibility === 'fail';

  return (
    <section className="feasibility-section-wrapper" id="feasibility">
      <div className="section-title-bar" data-section-reveal>
        <div>
          <span className="section-eyebrow-tag">Navigational Constraints &amp; Economics</span>
          <h2 className="section-heading-primary">Port Physical Fit &amp; Contract Economics</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {isSelectedFail && (
            <span className="feas-fail-badge-large" role="status">
              <span aria-hidden="true">⊘</span> Physical Limits Exceeded
            </span>
          )}
          <div className="port-context-badge">
            <span>Destination Port: <strong>{feasibility?.port}</strong></span>
            <span>&middot;</span>
            <span>Requirement: <strong>{Number(request?.cargo_quantity_mt || 0).toLocaleString()} MT</strong></span>
          </div>
        </div>
      </div>

      {/* Infeasibility summary banner — surfaces the first failing constraint for the selected vessel */}
      {isSelectedFail && (() => {
        const selectedCandidate = candidates.find((c) => c.vessel_class === selectedVessel);
        const failedChecks = selectedCandidate?.checks.filter((c) => c.status === 'fail') || [];
        return failedChecks.length > 0 ? (
          <div className="feas-fail-summary-banner" role="alert" data-card-reveal>
            <strong>Berth constraint{failedChecks.length > 1 ? 's' : ''} exceeded — {request?.vessel_class} cannot discharge at {feasibility?.port}</strong>
            <ul className="feas-fail-list">
              {failedChecks.map((fc) => (
                <li key={fc.constraint}>
                  <strong>{fc.constraint}:</strong> vessel {fc.vessel_value}{fc.constraint === 'DWT' ? ' DWT' : ' m'} exceeds port limit of {fc.port_limit != null ? `${fc.port_limit}${fc.constraint === 'DWT' ? ' DWT' : ' m'}` : 'not published'}
                </li>
              ))}
            </ul>
          </div>
        ) : null;
      })()}

      <div className="feasibility-equal-grid">
        {/* Left Column: Physical Port Compatibility Table */}
        <div className="feasibility-card-panel" data-card-reveal>
          <div className="panel-inner-header">
            <div>
              <span className="card-kicker-tag">Berth &amp; Channel Limits</span>
              <h3 className="card-primary-title">
                {feasibility?.port} — Physical Limits vs. Vessel Classes
              </h3>
            </div>
          </div>

          <div className="table-responsive-container">
            <table className="physical-limits-table">
              <thead>
                <tr>
                  <th scope="col" style={{ width: '22%' }}>Vessel Class</th>
                  <th scope="col" style={{ width: '22%' }}>Constraint</th>
                  <th scope="col" style={{ width: '22%' }}>Vessel Spec</th>
                  <th scope="col" style={{ width: '22%' }}>Port Limit</th>
                  <th scope="col" style={{ width: '12%', textAlign: 'center' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((cand) => {
                  const isSelected = cand.vessel_class === selectedVessel;
                  const rowSpan = cand.checks.length;
                  const candFeas = formatFeasibilityStatus(cand.overall);

                  return cand.checks.map((check, idx) => {
                    const checkFeas = formatFeasibilityStatus(check.status);

                    return (
                      <tr
                        key={`${cand.vessel_class}-${check.constraint}`}
                        className={isSelected ? 'row-selected-vessel' : ''}
                      >
                        {idx === 0 && (
                          <td
                            rowSpan={rowSpan}
                            className="vessel-class-col-cell"
                          >
                            <div className="vessel-name-stack">
                              <strong className="vessel-class-label">{cand.vessel_class}</strong>
                              {isSelected && (
                                <span className="selected-vessel-pill">Selected</span>
                              )}
                              <span className="vessel-overall-tag">
                                Fit: {candFeas.label}
                              </span>
                            </div>
                          </td>
                        )}
                        <td className="constraint-name-cell">{check.constraint}</td>
                        <td className="numeric-spec-cell">
                          {check.vessel_value} {check.constraint === 'Draft' || check.constraint === 'LOA' || check.constraint === 'Beam' ? 'm' : check.constraint === 'DWT' ? 'DWT' : ''}
                        </td>
                        <td className="numeric-limit-cell">
                          {check.port_limit != null
                            ? `${check.port_limit} ${check.constraint === 'Draft' || check.constraint === 'LOA' || check.constraint === 'Beam' ? 'm' : check.constraint === 'DWT' ? 'DWT' : ''}`
                            : 'Not Published'}
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          <span className={`compliance-tag tag-${checkFeas.status}`}>
                            {checkFeas.status.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    );
                  });
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Comparative Contract Structures */}
        <div className="feasibility-card-panel" data-card-reveal>
          <div className="panel-inner-header">
            <div>
              <span className="card-kicker-tag">Contract Structuring</span>
              <h3 className="card-primary-title">
                Procurement Cost by Charter Mechanism
              </h3>
            </div>
            <div className="tonnage-badge">
              {Number(request?.cargo_quantity_mt || 0).toLocaleString()} MT Total
            </div>
          </div>

          <div className="chart-and-summary-container">
            <div className="cost-bar-chart-wrap">
              <ResponsiveContainer width="100%" height={170}>
                <BarChart
                  data={chartData}
                  layout="vertical"
                  margin={{ top: 10, right: 30, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                  <XAxis
                    type="number"
                    tickLine={false}
                    axisLine={{ stroke: '#cbd5e1' }}
                    tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'monospace' }}
                    tickFormatter={formatCurrency}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={150}
                    tickLine={false}
                    axisLine={{ stroke: '#cbd5e1' }}
                    tick={{ fill: '#1e293b', fontSize: 11, fontWeight: 500 }}
                  />
                  <Tooltip content={<CostBarTooltip />} />
                  <Bar dataKey="totalCost" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={entry.isLowest ? '#d97706' : '#0284c7'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Structured Cost Table */}
            <div className="cost-table-breakdown">
              {costOptions.map((opt) => (
                <div
                  key={opt.id}
                  className={`cost-option-line ${opt.is_lowest_modeled_cost ? 'line-recommended' : ''}`}
                >
                  <div className="option-name-side">
                    <strong className="option-title">{opt.name}</strong>
                    {opt.is_lowest_modeled_cost && (
                      <span className="lowest-cost-tag">Lowest Modeled Cost</span>
                    )}
                  </div>
                  <div className="option-cost-side">
                    <span className="rate-per-mt">${opt.rate_usd_per_mt?.toFixed(2)}/MT</span>
                    <strong className="total-contract-usd">
                      ${Number(opt.total_cost_usd).toLocaleString('en-US', { maximumFractionDigits: 0 })}
                    </strong>
                  </div>
                </div>
              ))}
            </div>

            {/* Backtest Walk-Forward Summary Block */}
            {backtest && (
              <div className="walk-forward-backtest-card">
                <div className="backtest-header-row">
                  <div className="backtest-indicator-dot" />
                  <strong className="backtest-title">Walk-Forward Decision Validation</strong>
                </div>
                <div className="backtest-metric-highlight">
                  <span className="backtest-savings-val">
                    {backtest.avg_savings_per_mt >= 0
                      ? `+$${backtest.avg_savings_per_mt.toFixed(2)}/MT Modeled Savings`
                      : `-$${Math.abs(backtest.avg_savings_per_mt).toFixed(2)}/MT Modeled Added Cost`}
                  </span>
                  <span className="backtest-points-count">
                    evaluated across {backtest.n_points} historical decision points
                  </span>
                </div>
                <p className="backtest-explanation-note">
                  {backtest.note}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
