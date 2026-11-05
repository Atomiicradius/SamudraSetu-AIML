/**
 * generateBrief.js
 * Produces a professional executive brief from the existing pipeline result.
 * Uses the browser's native Print-to-PDF flow via a styled hidden document —
 * no external library required.
 */

/** Format a number as USD with commas. */
function usd(val, dp = 2) {
  if (val == null || isNaN(val)) return '—';
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
  if (val >= 1_000)     return `$${(val / 1_000).toFixed(0)}K`;
  return `$${Number(val).toFixed(dp)}`;
}

/** Format a number as a percentage. */
function pct(val) {
  if (val == null) return '—';
  return `${(val * 100).toFixed(1)}%`;
}

/** Sanitise a string for safe HTML insertion. */
function esc(str) {
  return String(str ?? '—')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** Derive the "why" decision drivers the same way DecisionSection does. */
function buildDrivers(result) {
  const { forecast, risk, feasibility, recommendation } = result;
  const { formatFeasibilityStatus } = { formatFeasibilityStatus: (s) => {
    const t = String(s ?? '').toLowerCase();
    if (t === 'pass') return { summaryText: 'Compatible (Pass)', status: 'pass' };
    if (t === 'fail') return { summaryText: 'Limits Exceeded (Fail)', status: 'fail' };
    return { summaryText: 'Conditional Review', status: 'conditional' };
  }};

  const drivers = [];
  if (forecast?.expected_pct_change != null) {
    const p = forecast.expected_pct_change;
    drivers.push({
      label: 'Forward rate trend',
      value: `${p >= 0 ? '+' : ''}${p.toFixed(1)}% vs current (${forecast.horizon_days}d horizon)`,
      direction: p > 0 ? '↑ urges charter' : '↓ allows wait',
    });
  }
  if (forecast?.probability_increase != null) {
    const prob = Math.round(forecast.probability_increase * 100);
    drivers.push({
      label: 'Rate upside probability',
      value: `${prob}% chance rates rise`,
      direction: prob > 55 ? '↑ urges charter' : prob < 45 ? '↓ allows wait' : '• neutral',
    });
  }
  if (risk?.level) {
    drivers.push({
      label: 'Port operational risk',
      value: `${risk.level} (${risk.total_score ?? '—'}/${risk.max_score ?? 6})`,
      direction: risk.level === 'High' ? '↑ urges charter' : risk.level === 'Low' ? '↓ allows wait' : '• neutral',
    });
  }
  const feasStatus = recommendation?.selected_feasibility || feasibility?.selected?.overall;
  const fi = formatFeasibilityStatus(feasStatus);
  drivers.push({
    label: 'Vessel-port compatibility',
    value: fi.summaryText,
    direction: fi.status === 'fail' ? '⊘ infeasible' : fi.status === 'pass' ? '✓ compatible' : '? conditional',
  });
  return drivers;
}

/** Build the full HTML for the brief. */
function buildHtml(result) {
  const { request, forecast, risk, feasibility, recommendation } = result;
  const portPrediction = risk?.port_model_prediction;
  const feasInfo = (() => {
    const s = String(recommendation?.selected_feasibility || feasibility?.selected?.overall || '').toLowerCase();
    if (s === 'pass') return { label: 'Feasible (Pass)', cls: 'pass' };
    if (s === 'fail') return { label: 'Limits Exceeded (Fail)', cls: 'fail' };
    return { label: 'Conditional Review', cls: 'warn' };
  })();
  const isNonFeasible = feasInfo.cls === 'fail';
  const drivers = buildDrivers(result);
  const reasons = (recommendation?.reasons || []).map((r) => r.replaceAll('\\$', '$'));
  const costOptions = recommendation?.cost_options || [];
  const model = forecast?.model || {};

  // Failed feasibility constraints for selected vessel
  const candidates = feasibility?.candidates || [];
  const selectedVessel = feasibility?.selected?.vessel_class || request?.vessel_class;
  const selectedCandidate = candidates.find((c) => c.vessel_class === selectedVessel);
  const failedChecks = isNonFeasible ? (selectedCandidate?.checks || []).filter((c) => c.status === 'fail') : [];

  const ts = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'long', timeStyle: 'short' });

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>SamudraSetu — Chartering Brief</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 11pt;
    color: #1e293b;
    background: #fff;
    line-height: 1.5;
  }
  .page { max-width: 820px; margin: 0 auto; padding: 36px 40px; }
  /* Header */
  .brand-header {
    display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 2.5px solid #0f172a; padding-bottom: 14px; margin-bottom: 20px;
  }
  .brand-title { font-size: 17pt; font-weight: 800; color: #0f172a; letter-spacing: -0.03em; }
  .brand-sub   { font-size: 8pt; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px; }
  .gen-ts      { font-size: 8.5pt; color: #64748b; text-align: right; line-height: 1.6; }
  /* Section titles */
  h2 { font-size: 10pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;
       color: #0284c7; margin: 22px 0 10px; padding-bottom: 4px; border-bottom: 1px solid #e2e8f0; }
  /* Two-column grid */
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 28px; margin-bottom: 4px; }
  .kv { display: flex; flex-direction: column; margin-bottom: 6px; }
  .kv-label { font-size: 8pt; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
  .kv-value { font-size: 11pt; font-weight: 600; color: #0f172a; }
  /* Verdict block */
  .verdict-block {
    padding: 16px 20px; border-radius: 8px; margin-bottom: 14px;
    border-left: 5px solid #0284c7; background: #f0f9ff;
  }
  .verdict-block.charter { border-left-color: #16a34a; background: #f0fdf4; }
  .verdict-block.wait    { border-left-color: #d97706; background: #fffbeb; }
  .verdict-block.fail    { border-left-color: #dc2626; background: #fee2e2; }
  .verdict-label { font-size: 8pt; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; }
  .verdict-decision { font-size: 18pt; font-weight: 800; margin: 4px 0; color: #0f172a; }
  .verdict-strategy { font-size: 10pt; color: #334155; }
  /* Table */
  table { width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 10pt; }
  th { background: #f1f5f9; text-align: left; padding: 7px 10px;
       font-size: 8pt; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }
  td { padding: 7px 10px; border-bottom: 1px solid #e2e8f0; }
  tr:last-child td { border-bottom: none; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 8pt; font-weight: 700; text-transform: uppercase; }
  .badge-pass { background: #dcfce7; color: #16a34a; }
  .badge-fail { background: #fee2e2; color: #dc2626; }
  .badge-warn { background: #fef3c7; color: #d97706; }
  .badge-unknown { background: #e2e8f0; color: #64748b; }
  /* Drivers */
  .driver-row { display: flex; justify-content: space-between; align-items: flex-start;
                padding: 7px 10px; border-bottom: 1px solid #e2e8f0; }
  .driver-row:last-child { border-bottom: none; }
  .driver-label { font-size: 9pt; color: #334155; font-weight: 600; min-width: 160px; }
  .driver-value { font-size: 9.5pt; color: #0f172a; flex: 1; padding: 0 12px; }
  .driver-dir   { font-size: 8.5pt; color: #64748b; white-space: nowrap; }
  /* Reasons */
  .reason-item { padding: 6px 10px; border-left: 3px solid #e2e8f0; margin-bottom: 6px; font-size: 10pt; color: #334155; }
  /* Infeasible */
  .infeas-block { background: #fee2e2; border: 1px solid #fca5a5; border-left: 4px solid #dc2626;
                  border-radius: 6px; padding: 14px 18px; margin-bottom: 14px; }
  .infeas-block h3 { font-size: 11pt; color: #991b1b; margin-bottom: 6px; }
  .infeas-block p { font-size: 10pt; color: #7f1d1d; margin-bottom: 4px; }
  .infeas-block ul { margin: 6px 0 0 18px; color: #991b1b; font-size: 10pt; }
  /* Caveats */
  .caveats { font-size: 8.5pt; color: #64748b; margin-top: 24px; padding-top: 14px; border-top: 1px solid #e2e8f0; }
  .caveats li { margin-bottom: 4px; }
  /* Footer */
  .footer { margin-top: 28px; padding-top: 12px; border-top: 2px solid #0f172a;
            display: flex; justify-content: space-between; font-size: 8pt; color: #94a3b8; }
  @media print {
    body { font-size: 10pt; }
    .page { padding: 24px 28px; }
  }
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div class="brand-header">
    <div>
      <div class="brand-title">SamudraSetu</div>
      <div class="brand-sub">Maritime Freight Intelligence &amp; Procurement Decision Support</div>
    </div>
    <div class="gen-ts">
      <strong>Chartering Brief</strong><br/>
      Generated: ${esc(ts)}
    </div>
  </div>

  <!-- 1. Scenario -->
  <h2>1. Scenario</h2>
  <div class="grid2">
    <div class="kv"><span class="kv-label">Origin</span><span class="kv-value">${esc(request?.origin)}</span></div>
    <div class="kv"><span class="kv-label">Destination Port</span><span class="kv-value">${esc(request?.destination)}</span></div>
    <div class="kv"><span class="kv-label">Vessel Class</span><span class="kv-value">${esc(request?.vessel_class)}</span></div>
    <div class="kv"><span class="kv-label">Cargo Quantity</span><span class="kv-value">${Number(request?.cargo_quantity_mt || 0).toLocaleString()} MT</span></div>
    <div class="kv"><span class="kv-label">Forecast Horizon</span><span class="kv-value">${esc(request?.horizon_days)} days</span></div>
    <div class="kv"><span class="kv-label">Cargo Type</span><span class="kv-value">${esc(request?.cargo_type)}</span></div>
    <div class="kv"><span class="kv-label">Port Congestion Assumption</span><span class="kv-value">${esc(request?.congestion_level)}</span></div>
    <div class="kv"><span class="kv-label">Vessel Availability</span><span class="kv-value">${esc(request?.availability_level)}</span></div>
  </div>

  <!-- 2. Recommendation -->
  <h2>2. Chartering Recommendation</h2>
  ${isNonFeasible ? `
  <div class="infeas-block">
    <h3>⊘ No Viable Charter — Physical Limits Exceeded</h3>
    <p>The selected <strong>${esc(request?.vessel_class)}</strong> vessel exceeds one or more berth constraints at <strong>${esc(request?.destination)}</strong>. A standard Spot, TC, or COA cannot be recommended on this configuration.</p>
    ${failedChecks.length > 0 ? `<ul>${failedChecks.map((fc) => `<li><strong>${esc(fc.constraint)}:</strong> vessel ${esc(fc.vessel_value)}${fc.constraint === 'DWT' ? ' DWT' : ' m'} &gt; port limit ${fc.port_limit != null ? `${esc(fc.port_limit)}${fc.constraint === 'DWT' ? ' DWT' : ' m'}` : 'not published'}</li>`).join('')}</ul>` : ''}
  </div>
  ` : `
  <div class="verdict-block ${recommendation?.decision === 'Charter Now' ? 'charter' : 'wait'}">
    <div class="verdict-label">Recommended Action</div>
    <div class="verdict-decision">${esc(recommendation?.decision || 'Review Scenario')}</div>
    <div class="verdict-strategy">Target Execution Structure: <strong>${esc(recommendation?.contract_strategy)}</strong> &nbsp;&nbsp; Risk Level: <strong>${esc(recommendation?.risk_level)}</strong> &nbsp;&nbsp; Port Fit: <strong>${esc(feasInfo.label)}</strong></div>
  </div>
  `}

  <!-- 3. Forecast -->
  <h2>3. Freight Outlook (${esc(forecast?.horizon_days)}d Horizon)</h2>
  <div class="grid2">
    <div class="kv"><span class="kv-label">Current Spot Rate</span><span class="kv-value">${usd(forecast?.current_rate_usd_per_mt)}/MT</span></div>
    <div class="kv"><span class="kv-label">P50 Forward Median</span><span class="kv-value">${usd(forecast?.p50_usd_per_mt)}/MT</span></div>
    <div class="kv"><span class="kv-label">P10 Low Case</span><span class="kv-value">${usd(forecast?.p10_usd_per_mt)}/MT</span></div>
    <div class="kv"><span class="kv-label">P90 High Case</span><span class="kv-value">${usd(forecast?.p90_usd_per_mt)}/MT</span></div>
    <div class="kv"><span class="kv-label">Expected Change</span><span class="kv-value">${forecast?.expected_pct_change != null ? `${forecast.expected_pct_change >= 0 ? '+' : ''}${forecast.expected_pct_change.toFixed(1)}%` : '—'}</span></div>
    <div class="kv"><span class="kv-label">Rate Upside Probability</span><span class="kv-value">${pct(forecast?.probability_increase)}</span></div>
  </div>

  <!-- 4. Port Risk -->
  <h2>4. Port Risk — ${esc(request?.destination)}</h2>
  <div class="grid2">
    <div class="kv"><span class="kv-label">Risk Level</span><span class="kv-value">${esc(risk?.level)}</span></div>
    <div class="kv"><span class="kv-label">Composite Score</span><span class="kv-value">${esc(risk?.total_score)} / ${esc(risk?.max_score)}</span></div>
    ${portPrediction ? `
    <div class="kv"><span class="kv-label">Congestion Index (ML)</span><span class="kv-value">${portPrediction.congestion_index_0_100.toFixed(0)} / 100</span></div>
    <div class="kv"><span class="kv-label">Estimated Wait (ML)</span><span class="kv-value">${portPrediction.wait_hours.toFixed(1)} hrs</span></div>
    ` : `
    <div class="kv"><span class="kv-label">Congestion Assumption</span><span class="kv-value">${esc(request?.congestion_level)}</span></div>
    <div class="kv"><span class="kv-label">Port Model</span><span class="kv-value">No ML model for this port</span></div>
    `}
  </div>
  <table>
    <thead><tr><th>Risk Factor</th><th>Value</th><th>Score</th><th>Max</th></tr></thead>
    <tbody>
    ${(risk?.factors || []).map((f) => `
    <tr>
      <td>${esc(f.name.replace(' (illustrative, user-set)', '').replace(' (CoV, recent window)', ''))}</td>
      <td>${esc(f.value)}</td>
      <td>${esc(f.score ?? f.value)}</td>
      <td>${esc(f.max ?? 2)}</td>
    </tr>`).join('')}
    </tbody>
  </table>

  <!-- 5. Feasibility -->
  <h2>5. Port Physical Fit — ${esc(feasibility?.port)}</h2>
  <table>
    <thead><tr><th>Vessel Class</th><th>Constraint</th><th>Vessel Spec</th><th>Port Limit</th><th>Status</th></tr></thead>
    <tbody>
    ${(feasibility?.candidates || []).flatMap((cand) =>
      cand.checks.map((chk, idx) => `
      <tr ${cand.vessel_class === selectedVessel ? 'style="background:#f0f9ff"' : ''}>
        ${idx === 0 ? `<td rowspan="${cand.checks.length}" style="font-weight:600">${esc(cand.vessel_class)}${cand.vessel_class === selectedVessel ? ' ★' : ''}</td>` : ''}
        <td>${esc(chk.constraint)}</td>
        <td>${esc(chk.vessel_value)} ${chk.constraint === 'DWT' ? 'DWT' : 'm'}</td>
        <td>${chk.port_limit != null ? `${esc(chk.port_limit)} ${chk.constraint === 'DWT' ? 'DWT' : 'm'}` : 'Not Published'}</td>
        <td><span class="badge badge-${chk.status === 'pass' ? 'pass' : chk.status === 'fail' ? 'fail' : 'unknown'}">${chk.status.toUpperCase()}</span></td>
      </tr>`)
    ).join('')}
    </tbody>
  </table>

  <!-- 6. Commercial Comparison -->
  ${!isNonFeasible && costOptions.length > 0 ? `
  <h2>6. Procurement Cost Comparison</h2>
  <table>
    <thead><tr><th>Charter Structure</th><th>Rate ($/MT)</th><th>Total Contract Cost</th><th>Note</th></tr></thead>
    <tbody>
    ${costOptions.map((o) => `
    <tr ${o.is_lowest_modeled_cost ? 'style="background:#f0fdf4;font-weight:600"' : ''}>
      <td>${esc(o.name)}</td>
      <td>${usd(o.rate_usd_per_mt)}</td>
      <td>${usd(o.total_cost_usd, 0)}</td>
      <td>${o.is_lowest_modeled_cost ? '✓ Lowest modelled cost' : ''}</td>
    </tr>`).join('')}
    </tbody>
  </table>
  ` : ''}

  <!-- 7. Decision Drivers -->
  <h2>${isNonFeasible ? '6' : '7'}. Decision Drivers</h2>
  <div style="border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;margin-bottom:8px">
    ${drivers.map((d) => `
    <div class="driver-row">
      <span class="driver-label">${esc(d.label)}</span>
      <span class="driver-value">${esc(d.value)}</span>
      <span class="driver-dir">${esc(d.direction)}</span>
    </div>`).join('')}
  </div>
  ${reasons.length > 0 ? `
  <p style="font-size:9pt;color:#64748b;margin-bottom:6px;font-weight:600">Pipeline Rationale:</p>
  ${reasons.map((r) => `<div class="reason-item">${esc(r)}</div>`).join('')}
  ` : ''}

  <!-- 8. Model Provenance -->
  <h2>${isNonFeasible ? '7' : '8'}. Model Provenance &amp; Data Source</h2>
  <div class="grid2">
    <div class="kv"><span class="kv-label">Forecast Model</span><span class="kv-value">${esc(model.name || '—')}</span></div>
    <div class="kv"><span class="kv-label">Model Kind</span><span class="kv-value">${esc(model.fallback_used ? 'Statistical Fallback (Holt)' : 'Trained ML Artifact')}</span></div>
    <div class="kv"><span class="kv-label">Data Cutoff</span><span class="kv-value">${esc(model.data_cutoff)}</span></div>
    <div class="kv"><span class="kv-label">Data Source</span><span class="kv-value">${esc(model.data_source)}</span></div>
    <div class="kv"><span class="kv-label">Port Model</span><span class="kv-value">${portPrediction ? 'Trained XGBoost Regressor' : 'Rule-based composite'}</span></div>
    <div class="kv"><span class="kv-label">Interval Method</span><span class="kv-value">${esc(model.interval_method)}</span></div>
  </div>

  <!-- Caveats -->
  <div class="caveats">
    <strong>Caveats &amp; Limitations:</strong>
    <ul style="margin:6px 0 0 16px">
      <li>All model outputs are indicative decision-support projections; not financial guarantees or live market quotes.</li>
      ${(model.known_limitations || []).map((l) => `<li>${esc(l)}</li>`).join('')}
      <li>Port physical limit data is illustrative and may not reflect surveyed port particulars.</li>
      <li>Contract cost comparisons use illustrative premium constants, not live market contract terms.</li>
    </ul>
  </div>

  <!-- Footer -->
  <div class="footer">
    <span>SamudraSetu — Maritime Decision Support</span>
    <span>Bulk Procurement Intelligence Platform</span>
    <span>${esc(ts)}</span>
  </div>

</div>
</body>
</html>`;
}

/**
 * Export the brief as a printable page.
 * Opens a new window with the brief and triggers the browser print dialog.
 *
 * @param {object} result - The full pipeline result from the API.
 * @returns {Promise<void>}
 */
export async function exportBrief(result) {
  const html = buildHtml(result);

  const win = window.open('', '_blank', 'width=900,height=800,scrollbars=yes');
  if (!win) {
    throw new Error('Pop-up was blocked. Please allow pop-ups for this site and try again.');
  }

  win.document.write(html);
  win.document.close();

  // Give fonts and styles a moment to render, then trigger print
  await new Promise((resolve) => setTimeout(resolve, 800));
  win.focus();
  win.print();
}
