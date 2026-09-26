import React, { useState } from 'react';

function StatsBar({ health, currentRole, onRoleChange, onOpenSearch }) {
  const [searchInput, setSearchInput] = useState('');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onOpenSearch && onOpenSearch(searchInput.trim());
    } else {
      onOpenSearch && onOpenSearch('GJ01-AB-1234');
    }
  };

  const getRoleBadgeStyle = (role) => {
    switch (role) {
      case 'admin':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', border: '#ef4444' };
      case 'analyst':
        return { bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa', border: '#3b82f6' };
      case 'viewer':
      default:
        return { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af', border: '#6b7280' };
    }
  };

  const roleStyle = getRoleBadgeStyle(currentRole);

  return (
    <div style={styles.bar}>
      {/* Brand & State Badge */}
      <div style={styles.brandGroup}>
        <h2 style={styles.title}>🛡️ Sentinel-Lite</h2>
        <span style={styles.stateBadge}>Gujarat Command Center</span>
      </div>

      {/* Telemetry Stats */}
      {health ? (
        <div style={styles.telemetryGroup}>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>CAMERAS</span>
            <span style={styles.statValue}>{health.total_cameras}</span>
          </div>
          <div style={styles.statDivider} />
          <div style={styles.statItem}>
            <span style={styles.statLabel}>UPTIME</span>
            <span style={{ ...styles.statValue, color: '#10b981' }}>{health.online_percentage}%</span>
          </div>
          <div style={styles.statDivider} />
          <div style={styles.statItem}>
            <span style={styles.statLabel}>DEPTS</span>
            <span style={styles.statValue}>{health.departments_connected}</span>
          </div>
        </div>
      ) : (
        <div style={styles.telemetryGroup}>
          <span style={styles.statLabel}>Loading Telemetry...</span>
        </div>
      )}

      {/* Natural Language Search Bar (docs/DESIGN.md §4.1) */}
      <form onSubmit={handleSearchSubmit} style={styles.searchForm}>
        <div style={styles.searchPill}>
          <span style={styles.searchIcon}>🔍</span>
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search plate e.g. Find GJ01-AB-1234 near SG Highway..."
            style={styles.searchInput}
          />
          <button type="submit" style={styles.searchSubmitBtn}>
            Investigate
          </button>
        </div>
      </form>

      {/* RBAC Role Clearance Selector */}
      <div style={styles.roleGroup}>
        <span style={styles.roleLabel}>CLEARANCE:</span>
        <select
          value={currentRole}
          onChange={(e) => onRoleChange && onRoleChange(e.target.value)}
          style={{
            ...styles.roleSelect,
            backgroundColor: roleStyle.bg,
            color: roleStyle.text,
            borderColor: roleStyle.border,
          }}
          title="Switch RBAC Security Clearance (Admin / Analyst / Viewer)"
        >
          <option value="admin" style={{ backgroundColor: '#111827', color: '#f87171' }}>Admin (Full)</option>
          <option value="analyst" style={{ backgroundColor: '#111827', color: '#60a5fa' }}>Analyst (Dossier)</option>
          <option value="viewer" style={{ backgroundColor: '#111827', color: '#9ca3af' }}>Viewer (403 Guard)</option>
        </select>
      </div>
    </div>
  );
}

const styles = {
  bar: {
    height: '64px',
    backgroundColor: '#111827',
    borderBottom: '1px solid #374151',
    color: '#f9fafb',
    display: 'flex',
    alignItems: 'center',
    padding: '0 24px',
    gap: '20px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
    zIndex: 20,
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
  },
  brandGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    minWidth: '240px'
  },
  title: {
    margin: 0,
    fontSize: '18px',
    fontWeight: '700',
    letterSpacing: '-0.025em',
    color: '#ffffff'
  },
  stateBadge: {
    fontSize: '10px',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    backgroundColor: 'rgba(59, 130, 246, 0.15)',
    color: '#60a5fa',
    padding: '2px 8px',
    borderRadius: '9999px',
    border: '1px solid rgba(59, 130, 246, 0.3)'
  },
  telemetryGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px',
    backgroundColor: '#1f2937',
    padding: '6px 14px',
    borderRadius: '8px',
    border: '1px solid #374151'
  },
  statItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center'
  },
  statLabel: {
    fontSize: '9px',
    fontWeight: '700',
    color: '#9ca3af',
    letterSpacing: '0.05em'
  },
  statValue: {
    fontSize: '14px',
    fontWeight: '700',
    fontVariantNumeric: 'tabular-nums',
    color: '#f3f4f6'
  },
  statDivider: {
    width: '1px',
    height: '24px',
    backgroundColor: '#374151'
  },
  searchForm: {
    flex: 1,
    maxWidth: '540px'
  },
  searchPill: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: '#1f2937',
    border: '1px solid #374151',
    borderRadius: '9999px',
    padding: '3px 6px 3px 14px',
    transition: 'border-color 0.2s'
  },
  searchIcon: {
    fontSize: '14px',
    color: '#9ca3af',
    marginRight: '8px'
  },
  searchInput: {
    flex: 1,
    backgroundColor: 'transparent',
    border: 'none',
    outline: 'none',
    color: '#ffffff',
    fontSize: '13px',
    fontFamily: 'inherit'
  },
  searchSubmitBtn: {
    backgroundColor: '#2563eb',
    color: '#ffffff',
    border: 'none',
    borderRadius: '9999px',
    padding: '6px 14px',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s'
  },
  roleGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginLeft: 'auto'
  },
  roleLabel: {
    fontSize: '10px',
    fontWeight: '700',
    color: '#9ca3af',
    letterSpacing: '0.05em'
  },
  roleSelect: {
    padding: '5px 10px',
    borderRadius: '6px',
    borderWidth: '1px',
    borderStyle: 'solid',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
    outline: 'none'
  }
};

export default StatsBar;
