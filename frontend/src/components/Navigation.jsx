import { useState } from 'react';

const STATUS_CONFIG = {
  idle:    { label: 'No Analysis', dotClass: 'status-dot-idle' },
  running: { label: 'Running…',    dotClass: 'status-dot-running' },
  current: { label: 'Current',     dotClass: 'status-dot-current' },
  stale:   { label: 'Stale',       dotClass: 'status-dot-stale' },
  failed:  { label: 'Failed',      dotClass: 'status-dot-failed' },
};

export default function Navigation({ onRunClick, loading, analysisStatus = 'idle' }) {
  const [open, setOpen] = useState(false);
  const closeMenu = () => setOpen(false);

  const status = STATUS_CONFIG[analysisStatus] || STATUS_CONFIG.idle;

  return (
    <header className="site-header-nav" id="top">
      <div className="nav-constrained-shell">
        <a className="nav-brand-anchor" href="#top" aria-label="SamudraSetu Platform" onClick={closeMenu}>
          <span className="brand-logo-mark" aria-hidden="true">
            <span className="logo-bar bar-1" />
            <span className="logo-bar bar-2" />
            <span className="logo-bar bar-3" />
          </span>
          <div className="brand-text-stack">
            <span className="brand-main-title">SamudraSetu</span>
            <span className="brand-sub-title">Maritime Decision Support</span>
          </div>
        </a>

        <nav className={`nav-links-cluster ${open ? 'mobile-menu-active' : ''}`} aria-label="Main Navigation">
          <a href="#scenario" onClick={closeMenu}>Scenario</a>
          <a href="#overview" onClick={closeMenu}>Overview</a>
          <a href="#forecast" onClick={closeMenu}>Forecast</a>
          <a href="#risk" onClick={closeMenu}>Port Risk</a>
          <a href="#feasibility" onClick={closeMenu}>Feasibility &amp; Cost</a>
          <a href="#decision" onClick={closeMenu}>Decision</a>
          <a href="#methodology" onClick={closeMenu}>Audit</a>

          {/* Analysis status indicator */}
          <div
            className={`nav-analysis-status status-${analysisStatus}`}
            aria-label={`Analysis status: ${status.label}`}
            title={`Analysis status: ${status.label}`}
          >
            <span className={`nav-status-dot ${status.dotClass}`} aria-hidden="true" />
            <span className="nav-status-label">{status.label}</span>
          </div>

          <button
            className="btn-header-action"
            type="button"
            onClick={() => {
              closeMenu();
              onRunClick();
            }}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="btn-spinner-icon" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <span>Configure Scenario</span>
                <svg viewBox="0 0 20 20" width="14" height="14" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </>
            )}
          </button>
        </nav>

        <button
          className={`hamburger-toggle ${open ? 'is-active' : ''}`}
          type="button"
          aria-label={open ? 'Close Navigation' : 'Open Navigation'}
          aria-expanded={open}
          onClick={() => setOpen((prev) => !prev)}
        >
          <span />
          <span />
          <span />
        </button>
      </div>
    </header>
  );
}
