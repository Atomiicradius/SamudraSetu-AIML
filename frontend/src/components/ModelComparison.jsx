import { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

// Read-only view of a static evaluation file (public/course_eval_results.json).
// Shape: { n_test_windows, horizons: { "7-Day": { <model key>: { mae, rmse,
// mape_pct, directional_accuracy_pct, p10_p90_coverage_pct? } } } }
const RESULTS_URL = `${import.meta.env.BASE_URL}course_eval_results.json`;
const HORIZONS = [7, 14, 30, 60];

// Display order and labels; keys match the JSON exactly.
const MODELS = [
  { key: 'persistence', label: 'Persistence (baseline)', color: 'var(--text-faint)' },
  { key: 'holt', label: 'Holt', color: 'var(--border-strong)' },
  { key: 'lstm (old)', label: 'Original LSTM', color: 'var(--state-warn)' },
  { key: 'lstm_v2', label: 'LSTM v2 (leak-free)', color: 'var(--navy-slate)' },
  { key: 'timesfm', label: 'TimesFM (zero-shot)', color: 'var(--teal-primary)' },
  { key: 'persistence+drift', label: 'Persistence + drift', color: 'var(--text-muted)' },
];

const isNum = (value) => typeof value === 'number' && Number.isFinite(value);
const fmt = (value, digits) => (isNum(value) ? value.toFixed(digits) : '-');

function isValid(payload) {
  return Boolean(payload && typeof payload === 'object' && payload.horizons
    && typeof payload.horizons === 'object');
}

export default function ModelComparison() {
  const [data, setData] = useState(null);
  const [failed, setFailed] = useState(false);
  const [horizon, setHorizon] = useState(30);
  const [hideLstm, setHideLstm] = useState(false);

  useEffect(() => {
    let active = true;
    fetch(RESULTS_URL)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((payload) => {
        if (!active) return;
        if (isValid(payload)) setData(payload);
        else setFailed(true);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const rows = useMemo(() => {
    const block = data?.horizons?.[`${horizon}-Day`];
    if (!block) return [];
    const baselineMae = block.persistence?.mae;
    return MODELS.filter((model) => block[model.key]).map((model) => {
      const metrics = block[model.key];
      return {
        ...model,
        mae: metrics.mae,
        rmse: metrics.rmse,
        mape: metrics.mape_pct,
        direction: metrics.directional_accuracy_pct,
        coverage: metrics.p10_p90_coverage_pct,
        multiple: isNum(baselineMae) && baselineMae > 0 ? metrics.mae / baselineMae : null,
        isBaseline: model.key === 'persistence',
      };
    });
  }, [data, horizon]);

  const baselineMae = rows.find((row) => row.isBaseline)?.mae;

  // Chart-only filter: the table below always lists every model.
  const chartRows = useMemo(
    () => (hideLstm ? rows.filter((row) => row.key !== 'lstm (old)') : rows),
    [rows, hideLstm],
  );
  // Axis max comes from the plotted data (with 10% headroom), so hiding a
  // tall bar rescales the axis to what is left.
  const yMax = useMemo(() => {
    const peak = Math.max(0, ...chartRows.map((row) => row.mae).filter(isNum), baselineMae ?? 0);
    return peak > 0 ? Math.ceil(peak * 1.1 * 10) / 10 : 1;
  }, [chartRows, baselineMae]);

  return (
    <div className="workspace-section-boundary">
      <div className="constrained-section-inner">
        <section className="cmp-section" id="model-comparison">
          <div className="cmp-header">
            <div>
              <span className="section-eyebrow-tag">Model Evaluation</span>
              <h2 className="section-heading-primary">Model comparison: LSTM vs TimesFM vs baselines</h2>
              <p className="cmp-lede">
                Every model forecasts the same held-out test windows
                {isNum(data?.n_test_windows) ? ` (${data.n_test_windows})` : ''}; error is measured in
                USD per tonne against the rate that actually occurred {horizon} rows ahead.
              </p>
            </div>
            <div className="cmp-horizons" role="group" aria-label="Forecast horizon">
              {HORIZONS.map((h) => (
                <button
                  key={h}
                  type="button"
                  className={`cmp-horizon-btn${h === horizon ? ' cmp-horizon-active' : ''}`}
                  aria-pressed={h === horizon}
                  onClick={() => setHorizon(h)}
                >
                  {h}d
                </button>
              ))}
            </div>
          </div>

          <div className="cmp-notice" role="note">
            Freight series is simulated (random-walk proxy). A model is useful only if it beats persistence.
          </div>

          {failed && (
            <p className="cmp-message" role="status">
              Model comparison data could not be loaded.
            </p>
          )}
          {!failed && !data && <p className="cmp-message" role="status">Loading model comparison…</p>}
          {!failed && data && rows.length === 0 && (
            <p className="cmp-message" role="status">No results are available for a {horizon}-day horizon.</p>
          )}

          {rows.length > 0 && (
            <>
              <div className="cmp-chart-card">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div className="cmp-chart-title">Mean absolute error (USD per tonne), {horizon}-day horizon</div>
                  <label
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 8, fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', cursor: 'pointer' }}
                  >
                    <input
                      type="checkbox"
                      checked={hideLstm}
                      onChange={(event) => setHideLstm(event.target.checked)}
                    />
                    Hide original LSTM
                  </label>
                </div>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={chartRows} margin={{ top: 12, right: 16, bottom: 8, left: 0 }}>
                    <CartesianGrid stroke="var(--border-subtle)" vertical={false} />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                      interval={0}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                      tickLine={false}
                      axisLine={false}
                      width={44}
                      domain={[0, yMax]}
                      tickFormatter={(value) => `$${value}`}
                    />
                    <Tooltip
                      formatter={(value) => [`$${Number(value).toFixed(3)} / t`, 'MAE']}
                      cursor={{ fill: 'var(--bg-subtle)' }}
                    />
                    {isNum(baselineMae) && (
                      <ReferenceLine
                        y={baselineMae}
                        stroke="var(--text-secondary)"
                        strokeDasharray="4 4"
                        label={{ value: 'persistence', position: 'insideTopLeft', fontSize: 10, fill: 'var(--text-secondary)' }}
                      />
                    )}
                    <Bar dataKey="mae" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                      {rows.map((row) => (
                        <Cell key={row.key} fill={row.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="cmp-table-wrap">
                <table className="cmp-table">
                  <thead>
                    <tr>
                      <th scope="col">Model</th>
                      <th scope="col">MAE ($/t)</th>
                      <th scope="col">RMSE ($/t)</th>
                      <th scope="col">MAPE (%)</th>
                      <th scope="col">Direction (%)</th>
                      <th scope="col">Error vs persistence</th>
                      <th scope="col">P10-P90 coverage (%)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.key} className={row.isBaseline ? 'cmp-row-baseline' : undefined}>
                        <th scope="row">
                          <span className="cmp-swatch" style={{ background: row.color }} aria-hidden="true" />
                          {row.label}
                        </th>
                        <td>{fmt(row.mae, 3)}</td>
                        <td>{fmt(row.rmse, 3)}</td>
                        <td>{fmt(row.mape, 2)}</td>
                        <td>{fmt(row.direction, 1)}</td>
                        <td className={isNum(row.multiple) && row.multiple < 1 ? 'cmp-better' : undefined}>
                          {isNum(row.multiple) ? `${row.multiple.toFixed(2)}×` : '-'}
                        </td>
                        <td>{fmt(row.coverage, 1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="cmp-footnote">
                TimesFM&apos;s margin over persistence is small and has not been tested for statistical significance.
              </p>
              <p className="cmp-footnote">
                Error vs persistence is MAE divided by persistence MAE; below 1.00× means the model beat
                persistence on that measure. Persistence never predicts a direction, so it has none.
              </p>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
