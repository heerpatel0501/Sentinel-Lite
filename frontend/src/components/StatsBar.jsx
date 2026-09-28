import React from 'react';

function StatsBar({ health, onOpenSearch }) {
  if (!health) {
    return (
      <header className="sentinel-header sentinel-header-loading">
        <div className="sentinel-brand">
          <div className="sentinel-brand-mark">
            SL
          </div>

          <div>
            <div className="sentinel-brand-title">
              SENTINEL-LITE
            </div>

            <div className="sentinel-brand-subtitle">
              VEHICLE INTELLIGENCE NETWORK
            </div>
          </div>
        </div>

        <div className="sentinel-loading">
          INITIALIZING SYSTEM
        </div>
      </header>
    );
  }

  return (
    <header className="sentinel-header">

      {/* BRAND */}
      <div className="sentinel-brand">

        <div className="sentinel-brand-mark">
          SL
        </div>

        <div className="sentinel-brand-copy">
          <div className="sentinel-brand-title">
            SENTINEL-LITE
          </div>

          <div className="sentinel-brand-subtitle">
            VEHICLE INTELLIGENCE NETWORK
          </div>
        </div>

      </div>

      {/* SYSTEM STATUS */}
      <div className="sentinel-system-status">

        <div className="sentinel-status-indicator">
          <span className="sentinel-status-dot" />
          SYSTEM OPERATIONAL
        </div>

        <div className="sentinel-environment">
          GUJARAT CCTV SANDBOX
        </div>

      </div>

      {/* METRICS */}
      <div className="sentinel-metrics">

        <div className="sentinel-metric">
          <span className="sentinel-metric-label">
            CAMERAS
          </span>

          <span className="sentinel-metric-value">
            {health.total_cameras}
          </span>
        </div>

        <div className="sentinel-divider" />

        <div className="sentinel-metric">
          <span className="sentinel-metric-label">
            ONLINE
          </span>

          <span className="sentinel-metric-value sentinel-online">
            {health.online_percentage}%
          </span>
        </div>

        <div className="sentinel-divider" />

        <div className="sentinel-metric">
          <span className="sentinel-metric-label">
            DEPARTMENTS
          </span>

          <span className="sentinel-metric-value">
            {health.departments_connected}
          </span>
        </div>

      </div>

      {/* INVESTIGATOR */}
      <button
        type="button"
        onClick={() =>
          onOpenSearch && onOpenSearch('GJ01-AB-1234')
        }
        className="sentinel-investigator-button"
      >
        <span className="sentinel-investigator-icon">
          ⌕
        </span>

        <span>
          INVESTIGATOR
        </span>

        <span className="sentinel-command-key">
          / SEARCH
        </span>
      </button>

    </header>
  );
}

export default StatsBar;