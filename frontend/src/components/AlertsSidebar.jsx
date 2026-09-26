import React from 'react';

function AlertsSidebar({ alerts, onSelectPlate }) {
  return (
    <div style={styles.sidebar}>
      <div style={styles.header}>
        <h3 style={{ margin: 0 }}>🚨 Cross-Dept Alerts</h3>
        <small style={{ color: '#64748b' }}>Live Intelligence Stream</small>
      </div>
      <div style={styles.list}>
        {alerts.length === 0 ? (
          <p style={{ color: '#64748b', fontSize: '14px' }}>No active alerts</p>
        ) : (
          alerts.map(alert => (
            <div 
              key={alert.id} 
              style={styles.card}
              onClick={() => onSelectPlate && onSelectPlate(alert.plate_number)}
            >
              <div style={styles.timestamp}>{alert.timestamp}</div>
              <div style={styles.titleRow}>
                <span style={styles.plate}>{alert.plate_number}</span>
                <span style={styles.investigateTag}>🔍 Investigate</span>
              </div>
              <p style={styles.desc}>{alert.description}</p>
              <div style={styles.depts}>
                {alert.departments.map(d => (
                  <span key={d} style={styles.badge}>{d}</span>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

const styles = {
  sidebar: {
    width: '320px',
    backgroundColor: 'white',
    borderLeft: '1px solid #e2e8f0',
    display: 'flex',
    flexDirection: 'column'
  },
  header: {
    padding: '20px',
    margin: 0,
    borderBottom: '1px solid #e2e8f0',
    backgroundColor: '#f8fafc'
  },
  list: {
    padding: '15px',
    overflowY: 'auto',
    flex: 1
  },
  card: {
    backgroundColor: '#fff',
    border: '1px solid #fee2e2',
    borderLeft: '4px solid #ef4444',
    padding: '15px',
    marginBottom: '15px',
    borderRadius: '6px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    cursor: 'pointer',
    transition: 'transform 0.15s ease, box-shadow 0.15s ease'
  },
  timestamp: {
    fontSize: '12px',
    color: '#64748b',
    marginBottom: '5px'
  },
  titleRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px'
  },
  plate: {
    fontWeight: 'bold',
    fontFamily: 'monospace',
    fontSize: '15px',
    color: '#0f172a'
  },
  investigateTag: {
    fontSize: '11px',
    color: '#2563eb',
    fontWeight: '600',
    backgroundColor: '#eff6ff',
    padding: '2px 6px',
    borderRadius: '4px'
  },
  desc: {
    margin: '0 0 10px 0',
    fontSize: '13px',
    color: '#334155'
  },
  depts: {
    display: 'flex',
    gap: '5px'
  },
  badge: {
    fontSize: '11px',
    padding: '2px 6px',
    backgroundColor: '#e2e8f0',
    borderRadius: '12px',
    color: '#475569'
  }
};

export default AlertsSidebar;
