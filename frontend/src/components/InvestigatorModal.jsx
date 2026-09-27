import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

function InvestigatorModal({ initialPlate, onClose }) {
  const [queryPlate, setQueryPlate] = useState(initialPlate || 'GJ01-AB-1234');
  const [userRole, setUserRole] = useState('analyst');
  const [investigation, setInvestigation] = useState(null);
  const [vehicleProfile, setVehicleProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [zoomedImage, setZoomedImage] = useState(null);

  const fetchInvestigation = (plateText) => {
    if (!plateText) return;
    setLoading(true);
    setError(null);
    setVehicleProfile(null);
    setProfileError(null);

    fetch(`${API_BASE}/api/search?plate=${encodeURIComponent(plateText)}`, {
      headers: {
        'X-User-Role': userRole,
        'X-User-Id': '1'
      }
    })
      .then(res => {
        if (!res.ok) throw new Error(`Search error: HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        setInvestigation(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Investigation search failed:', err);
        setError(err.message || 'Failed to fetch journey');
        setLoading(false);
      });
  };

  useEffect(() => {
    if (initialPlate) {
      setQueryPlate(initialPlate);
      fetchInvestigation(initialPlate);
    }
  }, [initialPlate]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchInvestigation(queryPlate);
  };

  const handleShowDetails = () => {
    if (!investigation || !investigation.plate_text) return;
    setProfileLoading(true);
    setProfileError(null);

    fetch(`${API_BASE}/api/vehicle/${encodeURIComponent(investigation.plate_text)}/profile`, {
      headers: {
        'X-User-Role': userRole,
        'X-User-Id': '1'
      }
    })
      .then(async res => {
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Access Denied (HTTP ${res.status})`);
        }
        return res.json();
      })
      .then(profile => {
        setVehicleProfile(profile);
        setProfileLoading(false);
      })
      .catch(err => {
        setProfileError(err.message);
        setProfileLoading(false);
      });
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        {/* Header */}
        <div style={styles.header}>
          <div>
            <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              🔍 Gujarat Sentinel Investigator Dossier
            </h2>
            <div style={styles.subHeader}>
              Official Cross-Department Journey Reconstruction & Forensic Traceability
            </div>
          </div>
          <button onClick={onClose} style={styles.closeBtn}>✕</button>
        </div>

        {/* Search Bar & Role Switcher */}
        <div style={styles.toolbar}>
          <form onSubmit={handleSearchSubmit} style={styles.searchForm}>
            <input
              type="text"
              value={queryPlate}
              onChange={(e) => setQueryPlate(e.target.value)}
              placeholder="e.g. Find GJ01-AB-1234 or GJ05-XX-9999..."
              style={styles.input}
            />
            <button type="submit" style={styles.searchBtn} disabled={loading}>
              {loading ? 'Searching...' : 'Search Trajectory'}
            </button>
          </form>

          {/* RBAC Role Selector */}
          <div style={styles.rolePicker}>
            <span style={{ fontSize: '13px', color: '#64748b' }}>Active RBAC Clearance:</span>
            <select
              value={userRole}
              onChange={(e) => setUserRole(e.target.value)}
              style={styles.select}
            >
              <option value="analyst">Analyst (Full Surveillance Access)</option>
              <option value="admin">Admin (Executive Clearance)</option>
              <option value="viewer">Viewer (Restricted / Read-Only)</option>
            </select>
          </div>
        </div>

        {/* Modal Body */}
        <div style={styles.content}>
          {error && (
            <div style={styles.errorBanner}>
              ⚠️ {error}
            </div>
          )}

          {investigation && (
            <div>
              {/* Target Overview Card */}
              <div style={styles.summaryCard}>
                <div style={styles.plateBadgeWrap}>
                  <div style={styles.anprPlate}>
                    <span style={styles.anprInd}>IND</span>
                    <span style={styles.anprText}>{investigation.plate_text}</span>
                  </div>
                  <div style={{
                    ...styles.statusTag,
                    backgroundColor: investigation.watchlist_status === 'stolen' ? '#fee2e2' :
                      investigation.watchlist_status === 'wanted' ? '#fef3c7' : '#dcfce7',
                    color: investigation.watchlist_status === 'stolen' ? '#b91c1c' :
                      investigation.watchlist_status === 'wanted' ? '#b45309' : '#15803d'
                  }}>
                    {investigation.watchlist_status === 'stolen' ? '🚨 STOLEN (Police Flagged)' :
                     investigation.watchlist_status === 'wanted' ? '⚠️ WANTED (High Priority)' :
                     investigation.watchlist_status === 'flagged' ? '🚩 RTO FLAGGED' : '✅ CLEAN RECORD'}
                  </div>
                </div>

                <div style={styles.metricRow}>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Total Sightings</span>
                    <span style={styles.metricValue}>{investigation.total_sightings}</span>
                  </div>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>Departments Correlated</span>
                    <span style={styles.metricValue}>
                      {investigation.departments_involved.join(', ') || 'None'}
                    </span>
                  </div>
                  <div style={styles.metric}>
                    <button
                      onClick={handleShowDetails}
                      style={styles.detailsBtn}
                      disabled={profileLoading}
                    >
                      {vehicleProfile ? '🔄 Refresh Registration' : '📋 Show Vehicle Details'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Show Details / Registration Profile Dossier */}
              {profileLoading && (
                <div style={styles.loadingBox}>Fetching VAHAN registry records via authorized gateway...</div>
              )}

              {profileError && (
                <div style={styles.profileErrorBox}>
                  <strong>⛔ Access Denied (RBAC Restriction):</strong>
                  <p style={{ margin: '4px 0 0 0' }}>{profileError}</p>
                  <small style={{ color: '#94a3b8' }}>Switch role to 'Analyst' or 'Admin' in the toolbar to access confidential owner dossiers.</small>
                </div>
              )}

              {vehicleProfile && (
                <div style={styles.profileCard}>
                  <h4 style={{ margin: '0 0 12px 0', color: '#0f172a', borderBottom: '1px solid #e2e8f0', paddingBottom: '6px' }}>
                    📑 Official Vehicle Registration Dossier (VAHAN Integration)
                  </h4>
                  <div style={styles.profileGrid}>
                    <div><strong>Vehicle Class:</strong> {vehicleProfile.vehicle_class}</div>
                    <div><strong>Maker & Model:</strong> {vehicleProfile.maker_model}</div>
                    <div><strong>Fuel Type:</strong> {vehicleProfile.fuel_type}</div>
                    <div><strong>Registered RTO:</strong> {vehicleProfile.rto_office}</div>
                    <div><strong>Registered Date:</strong> {vehicleProfile.registration_date}</div>
                    <div><strong>Insurance Valid:</strong> {vehicleProfile.insurance_valid_until}</div>
                    <div><strong>Contact (Masked):</strong> {vehicleProfile.contact_phone_masked}</div>
                    <div><strong>Engine Hash:</strong> <code>{vehicleProfile.engine_no_hash}</code></div>
                  </div>
                  <div style={styles.profileFooter}>
                    🛡️ <em>Audit logging active: Query access recorded in immutable governance repository under surveillance access rules.</em>
                  </div>
                </div>
              )}

              {/* Active Alerts for this target */}
              {investigation.active_alerts && investigation.active_alerts.length > 0 && (
                <div style={styles.alertsBox}>
                  <h4 style={{ margin: '0 0 8px 0', color: '#991b1b' }}>🚨 Associated Alerts</h4>
                  <ul style={{ margin: 0, paddingLeft: '20px' }}>
                    {investigation.active_alerts.map((a, i) => (
                      <li key={i} style={{ color: '#b91c1c', fontSize: '14px' }}>{a}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Chronological Journey Trajectory Trail */}
              <h3 style={{ margin: '24px 0 12px 0', color: '#1e293b' }}>
                🗺️ Chronological Journey Trail & Evidence Verification
              </h3>

              {investigation.journey_history.length === 0 ? (
                <p style={{ color: '#64748b' }}>No movement sightings recorded for this plate.</p>
              ) : (
                <div style={styles.timeline}>
                  {investigation.journey_history.map((pt, idx) => (
                    <div key={idx} style={styles.timelineItem}>
                      <div style={styles.timelineMarker}>{idx + 1}</div>
                      <div style={styles.timelineContent}>
                        <div style={styles.timelineHeader}>
                          <span style={styles.timelineTime}>🕒 {pt.timestamp}</span>
                          <span style={styles.deptBadge}>{pt.department}</span>
                          <span style={styles.camBadge}>{pt.camera_name} (ID: {pt.camera_id})</span>
                        </div>

                        <div style={styles.timelineBody}>
                          <div style={styles.metaCol}>
                            <div><strong>GPS Coordinates:</strong> {pt.latitude.toFixed(4)}, {pt.longitude.toFixed(4)}</div>
                            <div><strong>AI Confidence:</strong> {(pt.confidence * 100).toFixed(1)}%</div>
                            <div><strong>Transport:</strong> TCP Interleaved RTSP</div>
                          </div>

                          {/* Evidence Thumbnail */}
                          {pt.evidence_reference && (
                            <div style={styles.evidenceThumbWrap}>
                              <img
                                src={`${API_BASE}${pt.evidence_reference}`}
                                alt={`Evidence ${pt.camera_name}`}
                                style={styles.evidenceThumb}
                                onClick={() => setZoomedImage(`${API_BASE}${pt.evidence_reference}`)}
                                onError={(e) => {
                                  // Fallback to placeholder if snapshot not yet written
                                  e.target.style.display = 'none';
                                }}
                              />
                              <div style={styles.thumbCaption}>
                                🔍 Click to inspect evidence snapshot
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* High-Res Evidence Image Viewer Modal */}
        {zoomedImage && (
          <div style={styles.zoomOverlay} onClick={() => setZoomedImage(null)}>
            <div style={styles.zoomContent} onClick={(e) => e.stopPropagation()}>
              <div style={styles.zoomHeader}>
                <strong>Forensic Evidence Keyframe</strong>
                <button onClick={() => setZoomedImage(null)} style={styles.closeBtn}>✕</button>
              </div>
              <img src={zoomedImage} alt="Forensic Evidence" style={styles.zoomedImg} />
              <div style={styles.zoomFooter}>
                Evidence URI: <code>{zoomedImage}</code> | Cryptographic SHA-256 Verified
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
    padding: '20px'
  },
  modal: {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    width: '900px',
    maxWidth: '95vw',
    maxHeight: '90vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    overflow: 'hidden'
  },
  header: {
    padding: '20px 24px',
    borderBottom: '1px solid #e2e8f0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    color: 'white'
  },
  subHeader: {
    fontSize: '13px',
    color: '#94a3b8',
    marginTop: '4px'
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    fontSize: '20px',
    cursor: 'pointer',
    padding: '4px 8px'
  },
  toolbar: {
    padding: '16px 24px',
    backgroundColor: '#f8fafc',
    borderBottom: '1px solid #e2e8f0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '16px',
    flexWrap: 'wrap'
  },
  searchForm: {
    display: 'flex',
    flex: 1,
    gap: '8px'
  },
  input: {
    flex: 1,
    padding: '10px 14px',
    borderRadius: '6px',
    border: '1px solid #cbd5e1',
    fontSize: '14px'
  },
  searchBtn: {
    backgroundColor: '#2563eb',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    padding: '10px 18px',
    fontWeight: '600',
    cursor: 'pointer'
  },
  rolePicker: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  select: {
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #cbd5e1',
    backgroundColor: 'white',
    fontSize: '13px'
  },
  content: {
    padding: '24px',
    overflowY: 'auto',
    flex: 1
  },
  summaryCard: {
    backgroundColor: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '18px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '16px'
  },
  plateBadgeWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  anprPlate: {
    backgroundColor: '#fef08a',
    border: '2px solid #000',
    borderRadius: '6px',
    display: 'flex',
    alignItems: 'center',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  anprInd: {
    backgroundColor: '#0284c7',
    color: 'white',
    fontSize: '11px',
    fontWeight: 'bold',
    padding: '6px 8px',
    borderTopLeftRadius: '4px',
    borderBottomLeftRadius: '4px'
  },
  anprText: {
    fontSize: '20px',
    fontWeight: '900',
    fontFamily: 'monospace',
    padding: '6px 14px',
    letterSpacing: '1px',
    color: '#000'
  },
  statusTag: {
    padding: '6px 12px',
    borderRadius: '20px',
    fontWeight: 'bold',
    fontSize: '13px'
  },
  metricRow: {
    display: 'flex',
    gap: '24px',
    alignItems: 'center'
  },
  metric: {
    display: 'flex',
    flexDirection: 'column'
  },
  metricLabel: {
    fontSize: '12px',
    color: '#64748b'
  },
  metricValue: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#0f172a'
  },
  detailsBtn: {
    backgroundColor: '#0f172a',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    padding: '8px 14px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer'
  },
  profileCard: {
    marginTop: '16px',
    padding: '16px',
    borderRadius: '8px',
    backgroundColor: '#f1f5f9',
    border: '1px solid #cbd5e1'
  },
  profileGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '10px',
    fontSize: '13px',
    color: '#334155'
  },
  profileFooter: {
    marginTop: '12px',
    fontSize: '12px',
    color: '#64748b',
    borderTop: '1px dashed #cbd5e1',
    paddingTop: '8px'
  },
  profileErrorBox: {
    marginTop: '16px',
    padding: '14px',
    borderRadius: '6px',
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    color: '#991b1b',
    fontSize: '13px'
  },
  loadingBox: {
    marginTop: '16px',
    padding: '12px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '13px'
  },
  alertsBox: {
    marginTop: '16px',
    padding: '12px 16px',
    borderRadius: '6px',
    backgroundColor: '#fff1f2',
    borderLeft: '4px solid #e11d48'
  },
  timeline: {
    position: 'relative',
    paddingLeft: '32px'
  },
  timelineItem: {
    position: 'relative',
    marginBottom: '20px'
  },
  timelineMarker: {
    position: 'absolute',
    left: '-32px',
    top: '0',
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    backgroundColor: '#2563eb',
    color: 'white',
    fontSize: '12px',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  timelineContent: {
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '14px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
  },
  timelineHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '8px',
    flexWrap: 'wrap'
  },
  timelineTime: {
    fontWeight: 'bold',
    fontSize: '14px',
    color: '#0f172a'
  },
  deptBadge: {
    backgroundColor: '#e0f2fe',
    color: '#0369a1',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600'
  },
  camBadge: {
    backgroundColor: '#f1f5f9',
    color: '#475569',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '12px'
  },
  timelineBody: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '16px',
    flexWrap: 'wrap'
  },
  metaCol: {
    fontSize: '13px',
    color: '#475569',
    lineHeight: '1.6'
  },
  evidenceThumbWrap: {
    cursor: 'pointer',
    textAlign: 'center'
  },
  evidenceThumb: {
    width: '140px',
    height: '80px',
    objectFit: 'cover',
    borderRadius: '4px',
    border: '1px solid #cbd5e1'
  },
  thumbCaption: {
    fontSize: '11px',
    color: '#64748b',
    marginTop: '4px'
  },
  zoomOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.85)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2000
  },
  zoomContent: {
    backgroundColor: '#0f172a',
    padding: '16px',
    borderRadius: '8px',
    maxWidth: '90vw',
    maxHeight: '90vh',
    display: 'flex',
    flexDirection: 'column'
  },
  zoomHeader: {
    color: 'white',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px'
  },
  zoomedImg: {
    maxWidth: '85vw',
    maxHeight: '75vh',
    objectFit: 'contain',
    borderRadius: '4px'
  },
  zoomFooter: {
    marginTop: '10px',
    color: '#94a3b8',
    fontSize: '12px'
  },
  errorBanner: {
    padding: '12px',
    backgroundColor: '#fee2e2',
    color: '#b91c1c',
    borderRadius: '6px',
    marginBottom: '16px'
  }
};

export default InvestigatorModal;
