import React from 'react';

function StatsBar({ health }) {
  if (!health) return <div style={styles.bar}>Loading stats...</div>;

  return (
    <div style={styles.bar}>
      <h2 style={{ margin: 0, marginRight: 'auto' }}>🛡️ Sentinel-Lite</h2>
      <div style={styles.stat}>
        <strong>Total Cameras:</strong> {health.total_cameras}
      </div>
      <div style={styles.stat}>
        <strong>Online:</strong> <span style={{ color: '#4caf50' }}>{health.online_percentage}%</span>
      </div>
      <div style={styles.stat}>
        <strong>Depts Connected:</strong> {health.departments_connected}
      </div>
    </div>
  );
}

const styles = {
  bar: {
    height: '60px',
    backgroundColor: '#1e293b',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    padding: '0 20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  stat: {
    marginLeft: '30px',
    fontSize: '16px'
  }
};

export default StatsBar;
