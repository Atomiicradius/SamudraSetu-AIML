import { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';

function CustomForecastTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  const dataPoint = payload[0]?.payload || {};
  const isHistorical = dataPoint.historicalRate != null;
  const isForecast = dataPoint.p50 != null;

  return (
    <div className="forecast-chart-tooltip">
      <div className="tooltip-date-header">{label}</div>
      {isHistorical && (
        <div className="tooltip-data-row">
          <span className="tooltip-color-indicator dot-historical" />
          <span className="tooltip-metric-name">Observed Rate:</span>
          <strong className="tooltip-metric-value">
            ${Number(dataPoint.historicalRate).toFixed(2)}/mt
          </strong>
        </div>
      )}
      {isForecast && (
        <>
          <div className="tooltip-data-row">
            <span className="tooltip-color-indicator dot-p50" />
            <span className="tooltip-metric-name">P50 Projection:</span>
            <strong className="tooltip-metric-value">
              ${Number(dataPoint.p50).toFixed(2)}/mt
            </strong>
          </div>
          <div className="tooltip-data-row">
            <span className="tooltip-color-indicator dot-band" />
            <span className="tooltip-metric-name">P10 – P90 Uncertainty:</span>
            <span className="tooltip-metric-value">
              ${Number(dataPoint.p10).toFixed(2)} &ndash; ${Number(dataPoint.p90).toFixed(2)}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

export default function ForecastSection({ forecast }) {
  const [showMetrics, setShowMetrics] = useState(false);

  const history = useMemo(() => (forecast?.historical || []).slice(-60), [forecast?.historical]);
  const futureSeries = useMemo(() => forecast?.series || [], [forecast?.series]);

  // Construct chart data array bridging historical to forecast
  const chartData = useMemo(() => {
    if (!forecast) return [];
    const historicalPoints = history.map((pt) => ({
      date: pt.date,
      historicalRate: pt.value,
      p50: null,
      p10: null,
      p90: null,
      confidenceBand: null,
      type: 'historical',
    }));

    const lastHistorical = history[history.length - 1];
    const bridgeDate = lastHistorical ? lastHistorical.date : 'Today';

    // Transition bridge anchor point
    const bridgePoint = {
      date: bridgeDate,
      historicalRate: forecast.current_rate_usd_per_mt,
      p50: forecast.current_rate_usd_per_mt,
      p10: forecast.current_rate_usd_per_mt,
      p90: forecast.current_rate_usd_per_mt,
      confidenceBand: [forecast.current_rate_usd_per_mt, forecast.current_rate_usd_per_mt],
      type: 'bridge',
    };

    const forecastPoints = futureSeries.map((item) => ({
      date: item.date,
      historicalRate: null,
      p50: item.p50,
      p10: item.p10,
      p90: item.p90,
      confidenceBand: [item.p10, item.p90],
      type: 'forecast',
    }));

    return [...historicalPoints, bridgePoint, ...forecastPoints];
  }, [history, futureSeries, forecast]);

  const allValues = useMemo(() => {
    if (!forecast) return [];
    const vals = [
      ...history.map((pt) => pt.value),
      forecast.current_rate_usd_per_mt,
      forecast.p10_usd_per_mt,
      forecast.p90_usd_per_mt,
      forecast.p50_usd_per_mt,
    ].filter((v) => typeof v === 'number' && !isNaN(v));
    return vals;
  }, [history, forecast]);

  if (!forecast) return null;

  const yMin = Math.max(0, Math.floor(Math.min(...allValues) * 0.95));
  const yMax = Math.ceil(Math.max(...allValues) * 1.05);

  const isUp = (forecast.expected_pct_change || 0) >= 0;
  const isFallback = Boolean(forecast.model?.fallback_used);
  const cutoffDate = history.length > 0 ? history[history.length - 1].date : '';

  return (
    <section className="forecast-section-wrapper" id="forecast">
      <div className="section-title-bar" data-section-reveal>
        <div>
          <span className="section-eyebrow-tag">Market Trajectory</span>
          <h2 className="section-heading-primary">
            Freight Forecast &middot; {forecast.horizon_days}-Day Projection
          </h2>
        </div>
        <div className="forecast-provenance-tag">
          <span className={`pill-status-dot ${isFallback ? 'dot-stat' : 'dot-ml'}`} />
          <span>{forecast.model?.name || 'Trained Model'}</span>
          <span className="provenance-sub">({isFallback ? 'Statistical Baseline' : 'Trained ML Artifact'})</span>
        </div>
      </div>

      <div className="forecast-main-layout">
        {/* Left: Interactive Recharts Graph */}
        <div className="forecast-chart-card" data-card-reveal>
          <div className="chart-card-topbar">
            <div>
              <h3 className="chart-card-heading">Historical Trajectory &amp; Forward Cone</h3>
              <p className="chart-card-caption">
                Daily rates in USD/MT. Cutoff marks the boundary between verified historical inputs and forward prediction.
              </p>
            </div>
            <div className="chart-legend-elements">
              <span className="legend-item">
                <span className="legend-swatch swatch-history" /> Historical Input
              </span>
              <span className="legend-item">
                <span className="legend-swatch swatch-p50" /> P50 Median Forecast
              </span>
              <span className="legend-item">
                <span className="legend-swatch swatch-band" /> P10–P90 Confidence Band
              </span>
            </div>
          </div>

          <div className="chart-canvas-container">
            <ResponsiveContainer width="100%" height={340}>
              <ComposedChart
                data={chartData}
                margin={{ top: 15, right: 20, left: 10, bottom: 5 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e2e8f0"
                  vertical={false}
                />
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={{ stroke: '#cbd5e1' }}
                  tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'monospace' }}
                  interval="preserveStartEnd"
                  tickFormatter={(val) => (val ? val.slice(5) : '')}
                />
                <YAxis
                  domain={[yMin, yMax]}
                  tickLine={false}
                  axisLine={{ stroke: '#cbd5e1' }}
                  tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'monospace' }}
                  tickFormatter={(val) => `$${val}`}
                  width={55}
                />
                {/* Vertical hover cursor */}
                <Tooltip
                  content={<CustomForecastTooltip />}
                  cursor={{ stroke: '#64748b', strokeWidth: 1.5, strokeDasharray: '3 3' }}
                />

                {/* Transition Divider at cutoff date */}
                {cutoffDate && (
                  <ReferenceLine
                    x={cutoffDate}
                    stroke="#94a3b8"
                    strokeDasharray="4 4"
                    label={{
                      value: 'Data Cutoff',
                      position: 'top',
                      fill: '#475569',
                      fontSize: 10,
                      fontWeight: 600,
                    }}
                  />
                )}

                {/* Confidence Interval Area */}
                <Area
                  dataKey="confidenceBand"
                  fill="#bae6fd"
                  fillOpacity={0.4}
                  stroke="#7dd3fc"
                  strokeWidth={1}
                  strokeDasharray="2 2"
                  connectNulls
                  isAnimationActive={false}
                />

                {/* Historical Observed Rate */}
                <Line
                  dataKey="historicalRate"
                  stroke="#334155"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 5, fill: '#0f172a' }}
                  connectNulls
                />

                {/* Forecast P50 Projection */}
                <Line
                  dataKey="p50"
                  stroke="#0284c7"
                  strokeWidth={2.5}
                  strokeDasharray={isFallback ? '6 4' : undefined}
                  dot={false}
                  activeDot={{ r: 5, fill: '#0284c7' }}
                  connectNulls
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Analytical Insight Panel */}
        <div className="forecast-insight-panel">
          {/* Target Metric Card */}
          <div className="insight-stat-card primary-insight" data-card-reveal>
            <div className="insight-label">Day {forecast.horizon_days} Median Rate</div>
            <div className="insight-highlight-val">
              ${forecast.p50_usd_per_mt?.toFixed(2)}
              <span className="insight-unit">/MT</span>
            </div>
            <div className={`insight-delta-chip ${isUp ? 'chip-positive' : 'chip-negative'}`}>
              <span>{isUp ? '▲' : '▼'} {Math.abs(forecast.expected_pct_change || 0).toFixed(1)}%</span>
              <span className="chip-sub">from ${forecast.current_rate_usd_per_mt?.toFixed(2)}</span>
            </div>
          </div>

          {/* Uncertainty Range */}
          <div className="insight-stat-card" data-card-reveal>
            <div className="insight-label">P10 – P90 Uncertainty Range</div>
            <div className="uncertainty-range-grid">
              <div className="range-point-box">
                <span className="point-caption">P10 Low Case</span>
                <strong className="point-val">${forecast.p10_usd_per_mt?.toFixed(2)}</strong>
              </div>
              <div className="range-point-box">
                <span className="point-caption">P90 High Case</span>
                <strong className="point-val">${forecast.p90_usd_per_mt?.toFixed(2)}</strong>
              </div>
            </div>

            <div className="probability-bar-row">
              <div className="prob-label-row">
                <span>Probability of Rate Increase:</span>
                <strong>{Math.round((forecast.probability_increase || 0) * 100)}%</strong>
              </div>
              <div className="prob-track">
                <div
                  className="prob-fill"
                  style={{ width: `${Math.round((forecast.probability_increase || 0) * 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Model Provenance & Verification Card */}
          <div className="insight-stat-card model-meta-card" data-card-reveal>
            <div className="insight-label">Model Verification &amp; Scope</div>
            <div className="meta-info-list">
              <div className="meta-info-item">
                <span className="meta-key">Architecture:</span>
                <span className="meta-val">{forecast.model?.name}</span>
              </div>
              <div className="meta-info-item">
                <span className="meta-key">Data Cutoff:</span>
                <span className="meta-val">{forecast.model?.data_cutoff || 'Current'}</span>
              </div>
              <div className="meta-info-item">
                <span className="meta-key">Interval Method:</span>
                <span className="meta-val">{forecast.model?.interval_method}</span>
              </div>
              <div className="meta-info-item">
                <span className="meta-key">Calibration:</span>
                <span className="meta-val">
                  {forecast.model?.interval_calibrated ? 'Calibrated' : 'Indicative (Uncalibrated)'}
                </span>
              </div>
            </div>

            {/* Toggle validation metrics */}
            {forecast.metrics && (
              <div className="metrics-toggle-area">
                <button
                  type="button"
                  className="btn-toggle-metrics"
                  onClick={() => setShowMetrics((prev) => !prev)}
                >
                  {showMetrics ? 'Hide Validation Errors' : 'Inspect Holdout Validation Errors'}
                </button>

                {showMetrics && (
                  <div className="holdout-metrics-drawer">
                    {Object.entries(forecast.metrics).map(([key, val]) => (
                      <div key={key} className="metric-row">
                        <span className="metric-name">{key.toUpperCase()}:</span>
                        <strong className="metric-score">
                          {typeof val === 'number' ? val.toFixed(2) : val}
                        </strong>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
