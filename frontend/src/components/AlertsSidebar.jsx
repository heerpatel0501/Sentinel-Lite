import React from 'react';

function AlertsSidebar({ alerts }) {
  return (
    <div style={styles.sidebar}>
      <h3 style={styles.header}>🚨 Cross-Dept Alerts</h3>
      <div style={styles.list}>
        {alerts.length === 0 ? (
          <p>No active alerts</p>
        ) : (
          alerts.map(alert => (
            <div key={alert.id} style={styles.card}>
              <div style={styles.timestamp}>{alert.timestamp}</div>
              <div style={styles.title}>Plate: {alert.plate_number}</div>
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
    borderRadius: '4px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
  },
  timestamp: {
    fontSize: '12px',
    color: '#64748b',
    marginBottom: '5px'
  },
  title: {
    fontWeight: 'bold',
    marginBottom: '8px'
  },
  desc: {
    margin: '0 0 10px 0',
    fontSize: '14px',
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
