import React from 'react';

function AlertsSidebar({ alerts = [], isLoading = false, onSelectPlate }) {
  const getDeptBadgeStyle = (dept) => {
    switch (dept) {
      case 'Police':
        return { bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa', border: 'rgba(59, 130, 246, 0.3)' };
      case 'RTO':
        return { bg: 'rgba(249, 115, 22, 0.15)', text: '#fb923c', border: 'rgba(249, 115, 22, 0.3)' };
      case 'GSRTC':
        return { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', border: 'rgba(16, 185, 129, 0.3)' };
      case 'Municipal':
        return { bg: 'rgba(139, 92, 246, 0.15)', text: '#a78bfa', border: 'rgba(139, 92, 246, 0.3)' };
      case 'Panchayat':
        return { bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6', border: 'rgba(236, 72, 153, 0.3)' };
      default:
        return { bg: 'rgba(107, 114, 128, 0.15)', text: '#9ca3af', border: 'rgba(107, 114, 128, 0.3)' };
    }
  };

  const getAlertBorderColor = (type) => {
    switch (type) {
      case 'watchlist_match':
        return '#ef4444'; // Red
      case 'speeding':
        return '#f59e0b'; // Amber
      case 'cross_department':
        return '#3b82f6'; // Blue
      default:
        return '#8b5cf6'; // Purple / Sensor
    }
  };

  return (
    <div style={styles.sidebar}>
      <div style={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3 style={styles.headerTitle}>🚨 Intelligence Alerts</h3>
          <span style={styles.livePulse}>● LIVE</span>
        </div>
        <div style={styles.subtext}>State-Wide Cross-Agency Grid</div>
      </div>

      <div style={styles.list}>
        {isLoading ? (
          <div style={styles.emptyContainer}>
            <div style={styles.spinner} />
            <p style={{ color: '#9ca3af', fontSize: '13px', marginTop: '10px' }}>Syncing alerts stream...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div style={styles.emptyContainer}>
            <span style={{ fontSize: '28px' }}>🛡️</span>
            <p style={{ color: '#9ca3af', fontSize: '13px', marginTop: '8px' }}>All sectors clear. No active alerts.</p>
          </div>
        ) : (
          alerts.map((alert) => {
            const borderColor = getAlertBorderColor(alert.alert_type);
            return (
              <div
                key={alert.id}
                style={{
                  ...styles.card,
                  borderLeftColor: borderColor
                }}
                onClick={() => onSelectPlate && onSelectPlate(alert.plate_number)}
                title="Click to open full forensic investigator dossier"
              >
                <div style={styles.cardHeader}>
                  <span style={styles.timestamp}>{alert.timestamp}</span>
                  <span style={styles.typeBadge}>{alert.alert_type?.replace('_', ' ').toUpperCase()}</span>
                </div>

                <div style={styles.titleRow}>
                  <span style={styles.plate}>{alert.plate_number}</span>
                  <span style={styles.investigateTag}>Dossier ➔</span>
                </div>

                <p style={styles.desc}>{alert.description}</p>

                <div style={styles.depts}>
                  {alert.departments && alert.departments.map((d) => {
                    const bStyle = getDeptBadgeStyle(d);
                    return (
                      <span
                        key={d}
                        style={{
                          ...styles.deptBadge,
                          backgroundColor: bStyle.bg,
                          color: bStyle.text,
                          borderColor: bStyle.border
                        }}
                      >
                        {d}
                      </span>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

const styles = {
  sidebar: {
    width: '340px',
    backgroundColor: '#111827',
    borderLeft: '1px solid #374151',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
    color: '#f9fafb'
  },
  header: {
    padding: '16px 20px',
    borderBottom: '1px solid #374151',
    backgroundColor: '#111827'
  },
  headerTitle: {
    margin: 0,
    fontSize: '15px',
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: '-0.01em'
  },
  livePulse: {
    fontSize: '10px',
    fontWeight: '700',
    color: '#10b981',
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    padding: '2px 6px',
    borderRadius: '9999px',
    border: '1px solid rgba(16, 185, 129, 0.3)'
  },
  subtext: {
    fontSize: '11px',
    color: '#9ca3af',
    marginTop: '4px'
  },
  list: {
    padding: '16px',
    overflowY: 'auto',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },
  emptyContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 10px',
    textAlign: 'center'
  },
  spinner: {
    width: '24px',
    height: '24px',
    border: '2px solid #374151',
    borderTopColor: '#3b82f6',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  },
  card: {
    backgroundColor: '#1f2937',
    border: '1px solid #374151',
    borderLeftWidth: '4px',
    padding: '14px',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'transform 0.15s ease, background-color 0.15s ease, border-color 0.15s ease',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px'
  },
  timestamp: {
    fontSize: '11px',
    color: '#9ca3af',
    fontFamily: 'JetBrains Mono, Menlo, monospace'
  },
  typeBadge: {
    fontSize: '9px',
    fontWeight: '700',
    color: '#d1d5db',
    backgroundColor: '#374151',
    padding: '2px 5px',
    borderRadius: '4px',
    letterSpacing: '0.05em'
  },
  titleRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px'
  },
  plate: {
    fontWeight: '700',
    fontFamily: 'JetBrains Mono, Menlo, monospace',
    fontSize: '15px',
    color: '#ffffff',
    letterSpacing: '0.05em'
  },
  investigateTag: {
    fontSize: '11px',
    color: '#60a5fa',
    fontWeight: '600'
  },
  desc: {
    margin: '0 0 10px 0',
    fontSize: '12px',
    lineHeight: '1.4',
    color: '#d1d5db'
  },
  depts: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px'
  },
  deptBadge: {
    fontSize: '10px',
    fontWeight: '600',
    padding: '2px 6px',
    borderRadius: '4px',
    borderWidth: '1px',
    borderStyle: 'solid'
  }
};

export default AlertsSidebar;
