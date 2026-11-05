import { useCallback, useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';

import Navigation from './components/Navigation';
import ScenarioPanel from './components/ScenarioPanel';
import ExecutiveStrip from './components/ExecutiveStrip';
import ForecastSection from './components/ForecastSection';
import PortRiskSection from './components/PortRiskSection';
import FeasibilitySection from './components/FeasibilitySection';
import DecisionSection from './components/DecisionSection';
import MethodologySection from './components/MethodologySection';
import { getPipelineConfig, runPipeline } from './api';

gsap.registerPlugin(useGSAP, ScrollTrigger);

const DEFAULT_SCENARIO = {
  origin: 'Australia',
  destination: 'Paradip',
  vessel_class: 'Capesize',
  cargo_type: 'Coal',
  cargo_quantity_mt: 150000,
  horizon_days: 7,
  congestion_level: 'Medium',
  availability_level: 'Medium',
};

// Deep equality check for scenario comparison
function scenariosEqual(a, b) {
  if (!a || !b) return false;
  const keys = [
    'origin', 'destination', 'vessel_class', 'cargo_type',
    'cargo_quantity_mt', 'horizon_days', 'congestion_level', 'availability_level',
  ];
  return keys.every((k) => String(a[k]) === String(b[k]));
}

// Vessel DWT capacity caps for validation
const VESSEL_MAX_DWT = {
  Handysize: 40000,
  Supramax: 60000,
  Panamax: 80000,
  Capesize: 180000,
};

// Analytical skeleton displayed while the initial pipeline run is pending
function AnalyticalResultsSkeleton() {
  return (
    <div className="skeleton-analytical-wrapper">
      <div className="workspace-section-boundary">
        <div className="constrained-section-inner">
          <div className="skeleton-status-indicator">
            <span className="loading-spinner-ring" style={{ width: 14, height: 14, borderWidth: 2 }} />
            <span>Calculating probabilistic forward rates, port risk &amp; charter economics...</span>
          </div>
          <div className="skeleton-card skeleton-metrics-strip" style={{ marginTop: 12 }} />
        </div>
      </div>
      <div className="workspace-section-boundary">
        <div className="constrained-section-inner">
          <div className="skeleton-grid-two-col">
            <div className="skeleton-card skeleton-chart-box" />
            <div className="skeleton-card skeleton-side-box" />
          </div>
        </div>
      </div>
    </div>
  );
}

// Pre-run empty state shown before any analysis is completed
function PreRunEmptyState({ onRunClick }) {
  return (
    <div className="workspace-section-boundary">
      <div className="constrained-section-inner">
        <div className="pre-run-empty-state" role="status">
          <div className="pre-run-icon" aria-hidden="true">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <h3 className="pre-run-heading">Run a scenario to see your analysis</h3>
          <p className="pre-run-body">
            Configure your origin, destination port, vessel class and cargo quantity above,
            then run the pipeline to see your freight forecast, port risk assessment,
            navigational feasibility and chartering recommendation.
          </p>
          <button type="button" className="btn-pre-run-action" onClick={onRunClick}>
            Configure &amp; Run Scenario
            <svg viewBox="0 0 20 20" width="14" height="14" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

// Stale results banner shown when inputs differ from the analysed scenario
function StaleResultsBanner({ resultScenario, onRerun, loading }) {
  return (
    <div className="stale-results-banner" role="alert" aria-live="polite">
      <div className="stale-banner-left">
        <span className="stale-icon" aria-hidden="true">⚠</span>
        <div>
          <strong className="stale-heading">Inputs changed — results shown are for the previous scenario.</strong>
          <span className="stale-scenario-recap">
            {resultScenario.origin} → {resultScenario.destination} · {resultScenario.vessel_class} · {Number(resultScenario.cargo_quantity_mt).toLocaleString()} MT · {resultScenario.horizon_days}d
          </span>
        </div>
      </div>
      <button
        type="button"
        className="btn-stale-rerun"
        onClick={onRerun}
        disabled={loading}
      >
        {loading ? <><span className="loading-spinner-ring" style={{ width: 14, height: 14, borderWidth: 2 }} /><span>Running...</span></> : 'Re-run Analysis'}
      </button>
    </div>
  );
}

export default function App() {
  const pageRef = useRef(null);
  const [config, setConfig] = useState(null);
  const [requirement, setRequirement] = useState(DEFAULT_SCENARIO);
  const [result, setResult] = useState(null);
  const [resultScenario, setResultScenario] = useState(null); // the scenario that produced the current result
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialRunPending, setInitialRunPending] = useState(true);

  // Derive analysis status
  const isStale = result !== null && resultScenario !== null && !scenariosEqual(requirement, resultScenario);

  // Input validation: cargo quantity vs vessel DWT
  const vesselMax = VESSEL_MAX_DWT[requirement.vessel_class] ?? 180000;
  const cargoOverCapacity = requirement.cargo_quantity_mt > vesselMax;
  const cargoInvalid = !requirement.cargo_quantity_mt || requirement.cargo_quantity_mt <= 0;
  const hasValidationError = cargoOverCapacity || cargoInvalid;
  const validationMessage = cargoInvalid
    ? 'Cargo quantity must be greater than zero.'
    : cargoOverCapacity
    ? `Cargo (${Number(requirement.cargo_quantity_mt).toLocaleString()} MT) exceeds the rated capacity of a ${requirement.vessel_class} (${Number(vesselMax).toLocaleString()} DWT). Choose a larger vessel or reduce cargo.`
    : null;

  const executePipeline = useCallback(async (nextRequirement) => {
    setRequirement(nextRequirement);
    setLoading(true);
    setError('');
    try {
      console.log('[SamudraSetu] Running pipeline for:', nextRequirement);
      const pipelineOutput = await runPipeline(nextRequirement);
      setResult(pipelineOutput);
      setResultScenario({ ...nextRequirement });
      // Smooth scroll to executive overview upon manual rerun
      setTimeout(() => {
        const overviewEl = document.querySelector('#overview');
        if (overviewEl) {
          overviewEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 150);
    } catch (err) {
      console.error('[SamudraSetu] Pipeline run error:', err);
      setError(err instanceof Error ? err.message : 'The decision pipeline encountered an error.');
    } finally {
      setLoading(false);
      setInitialRunPending(false);
    }
  }, []);

  // Re-run with the current form values (for stale banner)
  const rerunWithCurrentInputs = useCallback(() => {
    executePipeline(requirement);
  }, [executePipeline, requirement]);

  useEffect(() => {
    let active = true;

    async function initializeDashboard() {
      try {
        console.log('[SamudraSetu] Fetching pipeline configuration...');
        const cfg = await getPipelineConfig();
        if (!active) return;
        setConfig(cfg);

        const req = cfg.default_requirement || DEFAULT_SCENARIO;
        setRequirement(req);

        console.log('[SamudraSetu] Executing initial baseline pipeline for:', req.origin, '->', req.destination);
        const res = await runPipeline(req);
        if (!active) return;

        console.log('[SamudraSetu] Initial pipeline result received successfully.');
        setResult(res);
        setResultScenario({ ...req });
      } catch (err) {
        console.error('[SamudraSetu] Pipeline initialization error:', err);
        if (active) {
          setError(err instanceof Error ? err.message : 'Backend connection failed.');
        }
      } finally {
        if (active) {
          setInitialRunPending(false);
        }
      }
    }

    initializeDashboard();

    return () => {
      active = false;
    };
  }, []);

  // GSAP Animations: Hero reveal on mount
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add('(prefers-reduced-motion: no-preference)', () => {
      gsap.fromTo(
        '[data-hero-reveal]',
        { y: 16, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.6,
          stagger: 0.08,
          ease: 'power2.out',
        }
      );
    });
    return () => mm.revert();
  }, { scope: pageRef });

  // GSAP Animations: ScrollTrigger section & card reveals
  useGSAP(() => {
    if (!result) return;

    const mm = gsap.matchMedia();
    mm.add('(prefers-reduced-motion: no-preference)', () => {
      const timer = setTimeout(() => {
        ScrollTrigger.refresh();

        gsap.utils.toArray('[data-section-reveal]').forEach((el) => {
          gsap.fromTo(
            el,
            { y: 16, opacity: 0 },
            {
              y: 0,
              opacity: 1,
              duration: 0.5,
              ease: 'power2.out',
              scrollTrigger: {
                trigger: el,
                start: 'top 92%',
                once: true,
              },
            }
          );
        });

        gsap.utils.toArray('[data-card-reveal]').forEach((el) => {
          gsap.fromTo(
            el,
            { y: 14, opacity: 0 },
            {
              y: 0,
              opacity: 1,
              duration: 0.45,
              stagger: 0.05,
              ease: 'power2.out',
              scrollTrigger: {
                trigger: el,
                start: 'top 92%',
                once: true,
              },
            }
          );
        });
      }, 150);

      return () => clearTimeout(timer);
    });

    return () => mm.revert();
  }, { scope: pageRef, dependencies: [result] });

  const scrollToScenario = () => {
    const el = document.querySelector('#scenario');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Determine the overall analysis status label for the nav
  const analysisStatus = loading
    ? 'running'
    : error
    ? 'failed'
    : result && isStale
    ? 'stale'
    : result
    ? 'current'
    : 'idle';

  return (
    <div className="app-workspace-root" ref={pageRef}>
      <Navigation
        onRunClick={scrollToScenario}
        loading={loading}
        analysisStatus={analysisStatus}
      />

      <main className="main-content-flow">
        {/* Platform Hero Banner */}
        <section className="platform-hero-header">
          <div className="hero-constrained-container">
            <div className="hero-branding-tag" data-hero-reveal>
              <span className="tag-beacon-dot" />
              <span>Bulk Procurement Decision Intelligence</span>
            </div>
            <h1 className="hero-primary-headline" data-hero-reveal>
              Maritime Freight Forecasting &amp; Chartering Decision Support
            </h1>
            <p className="hero-body-lede" data-hero-reveal>
              Evaluate dry-bulk coal procurement requirements through probabilistic forward projections,
              real port physical berth compliance, and cost-optimized charter structuring.
            </p>

            <div className="hero-metrics-pill-cluster" data-hero-reveal>
              <div className="metric-pill-item">
                <strong>4 Committed ML Artifacts</strong>
                <span>PyTorch LSTM &amp; XGBoost</span>
              </div>
              <div className="metric-pill-divider" />
              <div className="metric-pill-item">
                <strong>7 Indian Coal Ports</strong>
                <span>Physical Limits Audited</span>
              </div>
              <div className="metric-pill-divider" />
              <div className="metric-pill-item">
                <strong>5-Stage Decision Pipeline</strong>
                <span>Deterministic &amp; Transparent</span>
              </div>
            </div>
          </div>
        </section>

        {/* 1. Scenario Setup & Spatial Route Map — Renders Immediately */}
        <div className="workspace-section-boundary">
          <div className="constrained-section-inner">
            <ScenarioPanel
              config={config || { service_status: 'ready' }}
              requirement={requirement}
              loading={loading}
              error={error}
              onRun={executePipeline}
              onRequirementChange={setRequirement}
              validationMessage={validationMessage}
              hasValidationError={hasValidationError}
            />
          </div>
        </div>

        {/* Results Pipeline Container */}
        {result ? (
          <div className="results-pipeline-container">
            {/* Stale Results Banner — shown when inputs have changed after a successful run */}
            {isStale && (
              <div className="workspace-section-boundary" style={{ paddingTop: 0, paddingBottom: 0 }}>
                <div className="constrained-section-inner">
                  <StaleResultsBanner
                    resultScenario={resultScenario}
                    onRerun={rerunWithCurrentInputs}
                    loading={loading}
                  />
                </div>
              </div>
            )}

            {/* 2. Executive Overview Strip */}
            <div className="workspace-section-boundary">
              <div className="constrained-section-inner">
                <ExecutiveStrip result={result} isStale={isStale} />
              </div>
            </div>

            {/* 3. Freight Outlook & Forward Trajectory */}
            <div className="workspace-section-boundary">
              <div className="constrained-section-inner">
                <ForecastSection forecast={result.forecast} />
              </div>
            </div>

            {/* 4. Port Operational Risk & Congestion */}
            <div className="workspace-section-boundary">
              <div className="constrained-section-inner">
                <PortRiskSection result={result} />
              </div>
            </div>

            {/* 5. Navigational Feasibility & Economics */}
            <div className="workspace-section-boundary">
              <div className="constrained-section-inner">
                <FeasibilitySection result={result} />
              </div>
            </div>

            {/* 6. Chartering Recommendation Verdict */}
            <div className="workspace-section-boundary">
              <div className="constrained-section-inner">
                <DecisionSection result={result} onRunAgain={scrollToScenario} isStale={isStale} />
              </div>
            </div>

            {/* 7. Methodology & Technical Provenance */}
            <div className="workspace-section-boundary">
              <div className="constrained-section-inner">
                <MethodologySection result={result} />
              </div>
            </div>
          </div>
        ) : initialRunPending ? (
          <AnalyticalResultsSkeleton />
        ) : error ? (
          <div className="workspace-section-boundary">
            <div className="constrained-section-inner">
              <div className="form-validation-alert" style={{ margin: '24px 0', padding: '18px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <strong>Analysis Pipeline Error:</strong> {error}
                </div>
                <button
                  type="button"
                  className="btn-header-action"
                  onClick={() => executePipeline(requirement)}
                >
                  Retry Analysis
                </button>
              </div>
            </div>
          </div>
        ) : (
          <PreRunEmptyState onRunClick={scrollToScenario} />
        )}
      </main>

      <footer className="site-platform-footer">
        <div className="footer-constrained-shell">
          <div className="footer-brand-info">
            <span className="footer-logo-title">SamudraSetu</span>
            <p className="footer-tagline">
              Maritime Freight Forecasting &amp; Chartering Optimization Platform
            </p>
          </div>
          <div className="footer-provenance-notes">
            <p>Model outputs are indicative decision support projections; not financial guarantees.</p>
            <p>Macro indicators sourced from FRED / EIA / RBI. Freight routes simulated via geometric Brownian motion proxy series.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
