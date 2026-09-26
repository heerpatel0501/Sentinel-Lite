import React from 'react';

function StatsBar({ health, onOpenSearch }) {
  if (!health) return <div style={styles.bar}>Loading stats...</div>;

  return (
    <div style={styles.bar}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginRight: 'auto' }}>
        <h2 style={{ margin: 0 }}>🛡️ Sentinel-Lite</h2>
        <span style={styles.badge}>Gujarat CCTV Sandbox</span>
      </div>

      <div style={styles.stat}>
        <strong>Total Cameras:</strong> {health.total_cameras}
      </div>
      <div style={styles.stat}>
        <strong>Online:</strong> <span style={{ color: '#4caf50' }}>{health.online_percentage}%</span>
      </div>
      <div style={styles.stat}>
        <strong>Depts Connected:</strong> {health.departments_connected}
      </div>

      <button
        onClick={() => onOpenSearch && onOpenSearch('GJ01-AB-1234')}
        style={styles.searchBtn}
      >
        🔍 Investigator Search
      </button>
    </div>
  );
}

const styles = {
  bar: {
    height: '60px',
    backgroundColor: '#0f172a',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    padding: '0 20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  badge: {
    fontSize: '11px',
    backgroundColor: '#1e293b',
    color: '#38bdf8',
    padding: '3px 8px',
    borderRadius: '12px',
    border: '1px solid #0284c7'
  },
  stat: {
    marginLeft: '24px',
    fontSize: '14px'
  },
  searchBtn: {
    marginLeft: '24px',
    backgroundColor: '#2563eb',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    padding: '8px 16px',
    fontWeight: '600',
    fontSize: '13px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px'
  }
};

export default StatsBar;
