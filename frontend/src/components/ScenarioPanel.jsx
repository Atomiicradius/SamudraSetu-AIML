import { useState, useId } from 'react';
import RouteMap from './RouteMap';

export default function ScenarioPanel({
  config,
  requirement,
  loading,
  error,
  onRun,
  onRequirementChange,
  validationMessage,
  hasValidationError,
}) {
  const [form, setForm] = useState(requirement);
  const cargoInputId = useId();

  const origins = config?.available_origins || [
    'Australia',
    'United States',
    'Mozambique',
    'Russia',
    'Indonesia',
  ];

  const destinations = config?.available_destinations || [
    'Paradip',
    'Visakhapatnam',
    'Gangavaram',
    'Gopalpur',
    'Dhamra',
    'Sagar/Sandheads',
    'Haldia',
  ];

  const vesselClasses = config?.available_vessels || [
    'Capesize',
    'Panamax',
    'Supramax',
    'Handysize',
  ];

  // Model provenance detection
  const isLSTM =
    form.origin === 'Australia' &&
    form.destination === 'Paradip' &&
    form.vessel_class === 'Capesize';

  const isXGBFreight =
    form.origin === 'Australia' &&
    form.destination === 'Paradip' &&
    form.vessel_class === 'Supramax' &&
    form.horizon_days === 1;

  const isTrainedModel = isLSTM || isXGBFreight;

  // Horizon options based on route
  const availableHorizons =
    form.origin === 'Australia' &&
    form.destination === 'Paradip' &&
    form.vessel_class === 'Supramax'
      ? [1, 7, 14, 30, 60]
      : [7, 14, 30, 60];

  const update = (key, value) => {
    const next = { ...form, [key]: value };
    setForm(next);
    // Notify parent immediately so stale detection can compare
    if (onRequirementChange) onRequirementChange(next);
  };

  const handlePortSelectFromMap = (portName) => {
    update('destination', portName);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onRun(form);
  };

  // Vessel nominal DWT ratings for contextual reference
  const vesselDwtRef = {
    Capesize: '180,000 DWT nominal capacity',
    Panamax: '80,000 DWT nominal capacity',
    Supramax: '60,000 DWT nominal capacity',
    Handysize: '40,000 DWT nominal capacity',
  };

  return (
    <section className="scenario-workspace-section" id="scenario">
      <div className="section-title-bar" data-section-reveal>
        <div>
          <span className="section-eyebrow-tag">Operational Parameters</span>
          <h2 className="section-heading-primary">Scenario Setup &amp; Spatial Routing</h2>
        </div>
        <div className="status-indicator-badge">
          <span className="status-beacon-live" />
          <span>Backend Connected &middot; {config?.service_status?.toUpperCase() || 'READY'}</span>
        </div>
      </div>

      <div className="scenario-split-grid">
        {/* Left: Interactive Maritime Map */}
        <div className="scenario-map-column" data-card-reveal>
          <RouteMap
            origin={form.origin}
            destination={form.destination}
            isTrainedModel={isTrainedModel}
            onSelectPort={handlePortSelectFromMap}
          />
        </div>

        {/* Right: Procurement Parameters Form */}
        <div className="scenario-form-column" data-card-reveal>
          <form className="scenario-config-form" onSubmit={handleSubmit}>
            <div className="form-section-header">
              <h3 className="form-block-title">Procurement Brief</h3>
              <p className="form-block-subtitle">
                Configure origin, destination port, vessel specs, and cargo quantity.
              </p>
            </div>

            {/* Model Provenance Banner */}
            <div className={`model-provenance-banner ${isTrainedModel ? 'banner-ml' : 'banner-stat'}`}>
              <div className="banner-icon-col">
                <span className="provenance-dot" />
              </div>
              <div className="banner-text-col">
                <strong className="provenance-title">
                  {isLSTM
                    ? 'PyTorch 2-Layer LSTM (Trained Deep Learning Model)'
                    : isXGBFreight
                    ? 'XGBoost Regressor (Trained ML Model)'
                    : 'Holt Exponential Smoothing (Damped Trend Baseline)'}
                </strong>
                <span className="provenance-caption">
                  {isTrainedModel
                    ? 'Historical daily macro + freight feature dataset with holdout validation.'
                    : 'Statistical forecast using deterministic synthetic benchmark series; no trained ML artifact for this specific corridor.'}
                </span>
              </div>
            </div>

            <div className="form-fields-grid">
              {/* Origin */}
              <div className="form-group">
                <label className="form-label" htmlFor="origin-select">
                  Origin Country / Hub
                </label>
                <div className="select-container">
                  <select
                    id="origin-select"
                    className="form-select-control"
                    value={form.origin}
                    onChange={(e) => update('origin', e.target.value)}
                  >
                    {origins.map((orig) => (
                      <option key={orig} value={orig}>
                        {orig}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Destination */}
              <div className="form-group">
                <label className="form-label" htmlFor="destination-select">
                  Destination Indian Port
                </label>
                <div className="select-container">
                  <select
                    id="destination-select"
                    className="form-select-control"
                    value={form.destination}
                    onChange={(e) => update('destination', e.target.value)}
                  >
                    {destinations.map((dest) => (
                      <option key={dest} value={dest}>
                        {dest}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Vessel Class */}
              <div className="form-group">
                <label className="form-label" htmlFor="vessel-select">
                  Vessel Class
                </label>
                <div className="select-container">
                  <select
                    id="vessel-select"
                    className="form-select-control"
                    value={form.vessel_class}
                    onChange={(e) => update('vessel_class', e.target.value)}
                  >
                    {vesselClasses.map((vc) => (
                      <option key={vc} value={vc}>
                        {vc}
                      </option>
                    ))}
                  </select>
                </div>
                <span className="field-hint-text">
                  {vesselDwtRef[form.vessel_class] || ''}
                </span>
              </div>

              {/* Cargo Quantity */}
              <div className="form-group">
                <label className="form-label" htmlFor={cargoInputId}>
                  Cargo Quantity (Metric Tonnes)
                </label>
                <div className="input-affix-wrapper">
                  <input
                    id={cargoInputId}
                    type="number"
                    className="form-input-control"
                    min={1000}
                    max={250000}
                    step={1000}
                    value={form.cargo_quantity_mt}
                    onChange={(e) =>
                      update('cargo_quantity_mt', Math.max(1, Number(e.target.value)))
                    }
                  />
                  <span className="input-suffix-label">MT</span>
                </div>
                <span className="field-hint-text">
                  Formatted:{' '}
                  <strong>{Number(form.cargo_quantity_mt).toLocaleString('en-US')} mt</strong>
                </span>
              </div>

              {/* Forecast Horizon */}
              <div className="form-group form-group-full">
                <label className="form-label">
                  Forecast Horizon ({form.horizon_days} Days Ahead)
                </label>
                <div className="horizon-pill-selector">
                  {availableHorizons.map((h) => (
                    <button
                      key={h}
                      type="button"
                      className={`horizon-pill-btn ${form.horizon_days === h ? 'is-selected' : ''}`}
                      onClick={() => update('horizon_days', h)}
                    >
                      <span className="horizon-days-number">{h}</span>
                      <span className="horizon-days-unit">{h === 1 ? 'Day' : 'Days'}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Operational Assumptions */}
              <div className="form-group">
                <label className="form-label" htmlFor="congestion-select">
                  Port Congestion Assumption
                </label>
                <div className="select-container">
                  <select
                    id="congestion-select"
                    className="form-select-control"
                    value={form.congestion_level}
                    onChange={(e) => update('congestion_level', e.target.value)}
                  >
                    <option value="Low">Low Congestion</option>
                    <option value="Medium">Medium Congestion</option>
                    <option value="High">High Congestion</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="availability-select">
                  Vessel Market Availability
                </label>
                <div className="select-container">
                  <select
                    id="availability-select"
                    className="form-select-control"
                    value={form.availability_level}
                    onChange={(e) => update('availability_level', e.target.value)}
                  >
                    <option value="Low">Tight Supply (Low Availability)</option>
                    <option value="Medium">Balanced Supply (Medium)</option>
                    <option value="High">Ample Tonnage (High Availability)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Input validation error — shown before run is attempted */}
            {validationMessage && (
              <div className="form-validation-alert form-validation-warning" role="alert">
                <strong>⚠ Validation:</strong> {validationMessage}
              </div>
            )}

            {/* Execution error — shown after a failed run */}
            {error && !validationMessage && (
              <div className="form-validation-alert" role="alert">
                <strong>Execution Error:</strong> {error}
              </div>
            )}

            <div className="form-actions-row">
              <button
                type="submit"
                className="btn-execute-pipeline"
                disabled={loading || hasValidationError}
                aria-disabled={loading || hasValidationError}
                title={hasValidationError ? validationMessage : undefined}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner-ring" />
                    <span>Executing Decision Pipeline...</span>
                  </>
                ) : hasValidationError ? (
                  <span>Fix Validation Issues to Run</span>
                ) : (
                  <>
                    <span>Run Procurement Forecast &amp; Decision</span>
                    <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor" aria-hidden="true">
                      <path d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
