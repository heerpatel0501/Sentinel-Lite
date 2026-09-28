import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

function InvestigatorModal({ initialPlate, onClose }) {
  const [queryPlate, setQueryPlate] = useState(
    initialPlate || 'GJ01-AB-1234'
  );
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

    fetch(
      `${API_BASE}/api/search?plate=${encodeURIComponent(plateText)}`,
      {
        headers: {
          'X-User-Role': userRole,
          'X-User-Id': '1'
        }
      }
    )
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Search error: HTTP ${res.status}`);
        }

        return res.json();
      })
      .then((data) => {
        setInvestigation(data);
        setLoading(false);
      })
      .catch((err) => {
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

    fetch(
      `${API_BASE}/api/vehicle/${encodeURIComponent(
        investigation.plate_text
      )}/profile`,
      {
        headers: {
          'X-User-Role': userRole,
          'X-User-Id': '1'
        }
      }
    )
      .then(async (res) => {
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));

          throw new Error(
            errData.detail ||
              `Access Denied (HTTP ${res.status})`
          );
        }

        return res.json();
      })
      .then((profile) => {
        setVehicleProfile(profile);
        setProfileLoading(false);
      })
      .catch((err) => {
        setProfileError(err.message);
        setProfileLoading(false);
      });
  };

  const getStatusStyle = (status) => {
    if (status === 'stolen') {
      return {
        backgroundColor: 'rgba(239, 68, 68, 0.12)',
        border: '1px solid rgba(239, 68, 68, 0.35)',
        color: '#f87171'
      };
    }

    if (status === 'wanted') {
      return {
        backgroundColor: 'rgba(245, 158, 11, 0.12)',
        border: '1px solid rgba(245, 158, 11, 0.35)',
        color: '#fbbf24'
      };
    }

    if (status === 'flagged') {
      return {
        backgroundColor: 'rgba(59, 130, 246, 0.12)',
        border: '1px solid rgba(59, 130, 246, 0.35)',
        color: '#60a5fa'
      };
    }

    return {
      backgroundColor: 'rgba(16, 185, 129, 0.12)',
      border: '1px solid rgba(16, 185, 129, 0.35)',
      color: '#34d399'
    };
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>

        {/* HEADER */}
        <div style={styles.header}>
          <div style={styles.headerLeft}>
            <div style={styles.headerIcon}>
              ◈
            </div>

            <div>
              <div style={styles.headerTitle}>
                INVESTIGATOR DOSSIER
              </div>

              <div style={styles.headerSubtitle}>
                Cross-Department Intelligence & Forensic Traceability
              </div>
            </div>
          </div>

          <div style={styles.headerRight}>
            <div style={styles.secureIndicator}>
              <span style={styles.liveDot}></span>
              SECURE SESSION
            </div>

            <button
              onClick={onClose}
              style={styles.closeBtn}
            >
              ×
            </button>
          </div>
        </div>

        {/* SEARCH / CONTROL BAR */}
        <div style={styles.toolbar}>
          <form
            onSubmit={handleSearchSubmit}
            style={styles.searchForm}
          >
            <div style={styles.searchIcon}>
              ⌕
            </div>

            <input
              type="text"
              value={queryPlate}
              onChange={(e) => setQueryPlate(e.target.value)}
              placeholder="Enter vehicle registration..."
              style={styles.input}
            />

            <button
              type="submit"
              style={styles.searchBtn}
              disabled={loading}
            >
              {loading ? 'PROCESSING...' : 'SEARCH TRAJECTORY'}
            </button>
          </form>

          <div style={styles.rolePicker}>
            <span style={styles.roleLabel}>
              CLEARANCE
            </span>

            <select
              value={userRole}
              onChange={(e) => setUserRole(e.target.value)}
              style={styles.select}
            >
              <option value="analyst">
                Analyst — Full Surveillance Access
              </option>

              <option value="admin">
                Admin — Executive Clearance
              </option>

              <option value="viewer">
                Viewer — Read Only
              </option>
            </select>
          </div>
        </div>

        {/* CONTENT */}
        <div style={styles.content}>

          {error && (
            <div style={styles.errorBanner}>
              <strong>SEARCH FAILURE</strong>
              <span>{error}</span>
            </div>
          )}

          {investigation && (
            <div>

              {/* TARGET OVERVIEW */}
              <div style={styles.summaryCard}>

                <div style={styles.targetSection}>
                  <div style={styles.sectionEyebrow}>
                    TARGET VEHICLE
                  </div>

                  <div style={styles.plateRow}>
                    <div style={styles.anprPlate}>
                      <span style={styles.anprInd}>
                        IND
                      </span>

                      <span style={styles.anprText}>
                        {investigation.plate_text}
                      </span>
                    </div>

                    <div
                      style={{
                        ...styles.statusTag,
                        ...getStatusStyle(
                          investigation.watchlist_status
                        )
                      }}
                    >
                      <span style={styles.statusDot}></span>

                      {investigation.watchlist_status ===
                      'stolen'
                        ? 'STOLEN'
                        : investigation.watchlist_status ===
                          'wanted'
                        ? 'WANTED'
                        : investigation.watchlist_status ===
                          'flagged'
                        ? 'RTO FLAGGED'
                        : 'CLEAN RECORD'}
                    </div>
                  </div>
                </div>

                <div style={styles.metrics}>
                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>
                      SIGHTINGS
                    </span>

                    <span style={styles.metricValue}>
                      {investigation.total_sightings}
                    </span>
                  </div>

                  <div style={styles.metricDivider}></div>

                  <div style={styles.metric}>
                    <span style={styles.metricLabel}>
                      DEPARTMENTS
                    </span>

                    <span style={styles.metricValueSmall}>
                      {investigation.departments_involved.join(
                        ' / '
                      ) || 'NONE'}
                    </span>
                  </div>

                  <div style={styles.metricDivider}></div>

                  <button
                    onClick={handleShowDetails}
                    style={styles.detailsBtn}
                    disabled={profileLoading}
                  >
                    {vehicleProfile
                      ? 'REFRESH REGISTRATION'
                      : 'VIEW VEHICLE DOSSIER'}
                  </button>
                </div>
              </div>

              {/* LOADING */}
              {profileLoading && (
                <div style={styles.loadingBox}>
                  <span style={styles.spinner}></span>
                  AUTHORIZING VAHAN REGISTRY REQUEST...
                </div>
              )}

              {/* PROFILE ERROR */}
              {profileError && (
                <div style={styles.profileErrorBox}>
                  <div style={styles.profileErrorTitle}>
                    ACCESS RESTRICTED
                  </div>

                  <div style={styles.profileErrorText}>
                    {profileError}
                  </div>

                  <small>
                    Switch clearance level to Analyst or Admin
                    to access the vehicle dossier.
                  </small>
                </div>
              )}

              {/* VEHICLE PROFILE */}
              {vehicleProfile && (
                <div style={styles.profileCard}>

                  <div style={styles.cardHeader}>
                    <div>
                      <div style={styles.cardEyebrow}>
                        AUTHORIZED REGISTRY DATA
                      </div>

                      <h3 style={styles.cardTitle}>
                        Vehicle Registration Dossier
                      </h3>
                    </div>

                    <div style={styles.registryBadge}>
                      VAHAN
                    </div>
                  </div>

                  <div style={styles.profileGrid}>
                    <div style={styles.profileItem}>
                      <span>Vehicle Class</span>
                      <strong>
                        {vehicleProfile.vehicle_class}
                      </strong>
                    </div>

                    <div style={styles.profileItem}>
                      <span>Maker & Model</span>
                      <strong>
                        {vehicleProfile.maker_model}
                      </strong>
                    </div>

                    <div style={styles.profileItem}>
                      <span>Fuel Type</span>
                      <strong>
                        {vehicleProfile.fuel_type}
                      </strong>
                    </div>

                    <div style={styles.profileItem}>
                      <span>Registered RTO</span>
                      <strong>
                        {vehicleProfile.rto_office}
                      </strong>
                    </div>

                    <div style={styles.profileItem}>
                      <span>Registration Date</span>
                      <strong>
                        {vehicleProfile.registration_date}
                      </strong>
                    </div>

                    <div style={styles.profileItem}>
                      <span>Insurance Valid Until</span>
                      <strong>
                        {vehicleProfile.insurance_valid_until}
                      </strong>
                    </div>

                    <div style={styles.profileItem}>
                      <span>Contact</span>
                      <strong>
                        {vehicleProfile.contact_phone_masked}
                      </strong>
                    </div>

                    <div style={styles.profileItem}>
                      <span>Engine Hash</span>
                      <strong>
                        {vehicleProfile.engine_no_hash}
                      </strong>
                    </div>
                  </div>

                  <div style={styles.profileFooter}>
                    AUDIT LOG ACTIVE
                    <span>
                      Query access recorded in governance
                      repository.
                    </span>
                  </div>
                </div>
              )}

              {/* ALERTS */}
              {investigation.active_alerts &&
                investigation.active_alerts.length > 0 && (
                  <div style={styles.alertsBox}>

                    <div style={styles.alertHeader}>
                      <div style={styles.alertSignal}>
                        !
                      </div>

                      <div>
                        <div style={styles.alertTitle}>
                          ACTIVE INTELLIGENCE ALERTS
                        </div>

                        <div style={styles.alertSubtitle}>
                          Associated with target vehicle
                        </div>
                      </div>
                    </div>

                    <div style={styles.alertList}>
                      {investigation.active_alerts.map(
                        (a, i) => (
                          <div
                            key={i}
                            style={styles.alertItem}
                          >
                            {a}
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

              {/* TIMELINE HEADER */}
              <div style={styles.timelineTitle}>
                <div>
                  <div style={styles.sectionEyebrow}>
                    MOVEMENT ANALYSIS
                  </div>

                  <h3 style={styles.timelineHeading}>
                    Chronological Journey Trail
                  </h3>
                </div>

                <div style={styles.evidenceLabel}>
                  EVIDENCE VERIFIED
                </div>
              </div>

              {/* TIMELINE */}
              {investigation.journey_history.length === 0 ? (
                <div style={styles.emptyState}>
                  NO MOVEMENT SIGHTINGS RECORDED
                </div>
              ) : (
                <div style={styles.timeline}>

                  {investigation.journey_history.map(
                    (pt, idx) => (
                      <div
                        key={idx}
                        style={styles.timelineItem}
                      >

                        <div style={styles.timelineLine}></div>

                        <div style={styles.timelineMarker}>
                          {String(idx + 1).padStart(2, '0')}
                        </div>

                        <div style={styles.timelineContent}>

                          <div style={styles.timelineHeader}>

                            <div>
                              <div style={styles.timelineTime}>
                                {pt.timestamp}
                              </div>

                              <div style={styles.timelineCamera}>
                                {pt.camera_name}
                                <span>
                                  ID {pt.camera_id}
                                </span>
                              </div>
                            </div>

                            <div style={styles.badgeGroup}>
                              <span style={styles.deptBadge}>
                                {pt.department}
                              </span>

                              <span style={styles.camBadge}>
                                ONLINE TRACE
                              </span>
                            </div>
                          </div>

                          <div style={styles.timelineBody}>

                            <div style={styles.metaCol}>

                              <div style={styles.dataRow}>
                                <span>GPS POSITION</span>

                                <strong>
                                  {pt.latitude.toFixed(4)}
                                  {' / '}
                                  {pt.longitude.toFixed(4)}
                                </strong>
                              </div>

                              <div style={styles.dataRow}>
                                <span>AI CONFIDENCE</span>

                                <strong style={styles.confidence}>
                                  {(pt.confidence * 100).toFixed(
                                    1
                                  )}
                                  %
                                </strong>
                              </div>

                              <div style={styles.dataRow}>
                                <span>TRANSPORT</span>

                                <strong>
                                  TCP / RTSP
                                </strong>
                              </div>

                            </div>

                            {/* EVIDENCE */}
                            {pt.evidence_reference && (
                              <div
                                style={
                                  styles.evidenceThumbWrap
                                }
                                onClick={() =>
                                  setZoomedImage(
                                    `${API_BASE}${pt.evidence_reference}`
                                  )
                                }
                              >
                                <div
                                  style={
                                    styles.evidenceFrame
                                  }
                                >
                                  <img
                                    src={`${API_BASE}${pt.evidence_reference}`}
                                    alt={`Evidence ${pt.camera_name}`}
                                    style={
                                      styles.evidenceThumb
                                    }
                                    onError={(e) => {
                                      e.target.style.display =
                                        'none';
                                    }}
                                  />

                                  <div
                                    style={
                                      styles.evidenceOverlay
                                    }
                                  >
                                    INSPECT
                                  </div>
                                </div>

                                <div
                                  style={
                                    styles.thumbCaption
                                  }
                                >
                                  EVIDENCE KEYFRAME
                                </div>
                              </div>
                            )}

                          </div>
                        </div>
                      </div>
                    )
                  )}

                </div>
              )}
            </div>
          )}
        </div>

        {/* IMAGE VIEWER */}
        {zoomedImage && (
          <div
            style={styles.zoomOverlay}
            onClick={() => setZoomedImage(null)}
          >
            <div
              style={styles.zoomContent}
              onClick={(e) => e.stopPropagation()}
            >

              <div style={styles.zoomHeader}>

                <div>
                  <div style={styles.zoomEyebrow}>
                    FORENSIC EVIDENCE
                  </div>

                  <strong>
                    Evidence Keyframe
                  </strong>
                </div>

                <button
                  onClick={() => setZoomedImage(null)}
                  style={styles.zoomClose}
                >
                  ×
                </button>
              </div>

              <div style={styles.imageContainer}>
                <img
                  src={zoomedImage}
                  alt="Forensic Evidence"
                  style={styles.zoomedImg}
                />
              </div>

              <div style={styles.zoomFooter}>
                <span>
                  SHA-256 VERIFIED
                </span>

                <code>
                  {zoomedImage}
                </code>
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
    inset: 0,
    background:
      'radial-gradient(circle at 50% 20%, rgba(15, 40, 70, 0.35), rgba(2, 6, 12, 0.94))',
    backdropFilter: 'blur(10px)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
    padding: '24px',
    animation: 'fadeIn 0.25s ease'
  },

  modal: {
    width: '1100px',
    maxWidth: '96vw',
    height: '92vh',
    maxHeight: '920px',
    display: 'flex',
    flexDirection: 'column',
    background:
      'linear-gradient(145deg, #0b1220, #0f172a)',
    border:
      '1px solid rgba(148, 163, 184, 0.18)',
    borderRadius: '18px',
    overflow: 'hidden',
    boxShadow:
      '0 40px 100px rgba(0,0,0,0.65), 0 0 80px rgba(14,165,233,0.08)'
  },

  header: {
    minHeight: '76px',
    padding: '0 24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom:
      '1px solid rgba(148,163,184,0.12)',
    background:
      'linear-gradient(90deg, rgba(15,23,42,0.98), rgba(15,30,48,0.98))'
  },

  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px'
  },

  headerIcon: {
    width: '42px',
    height: '42px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '12px',
    background:
      'linear-gradient(135deg, #0ea5e9, #2563eb)',
    color: 'white',
    fontSize: '24px',
    boxShadow:
      '0 0 25px rgba(14,165,233,0.25)'
  },

  headerTitle: {
    color: '#f8fafc',
    fontSize: '18px',
    fontWeight: '800',
    letterSpacing: '1.5px'
  },

  headerSubtitle: {
    marginTop: '4px',
    color: '#64748b',
    fontSize: '11px',
    letterSpacing: '0.8px'
  },

  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '18px'
  },

  secureIndicator: {
    color: '#64748b',
    fontSize: '10px',
    fontWeight: '700',
    letterSpacing: '1px',
    display: 'flex',
    alignItems: 'center',
    gap: '7px'
  },

  liveDot: {
    width: '7px',
    height: '7px',
    borderRadius: '50%',
    backgroundColor: '#22c55e',
    boxShadow:
      '0 0 10px rgba(34,197,94,0.8)'
  },

  closeBtn: {
    background: 'rgba(255,255,255,0.04)',
    border:
      '1px solid rgba(255,255,255,0.08)',
    color: '#94a3b8',
    width: '36px',
    height: '36px',
    borderRadius: '8px',
    fontSize: '22px',
    cursor: 'pointer'
  },

  toolbar: {
    padding: '14px 20px',
    background: '#080f1b',
    borderBottom:
      '1px solid rgba(148,163,184,0.1)',
    display: 'flex',
    alignItems: 'center',
    gap: '14px'
  },

  searchForm: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    background: '#111c2d',
    border:
      '1px solid rgba(148,163,184,0.15)',
    borderRadius: '9px',
    overflow: 'hidden'
  },

  searchIcon: {
    color: '#38bdf8',
    paddingLeft: '14px',
    fontSize: '20px'
  },

  input: {
    flex: 1,
    background: 'transparent',
    border: 'none',
    outline: 'none',
    color: '#e2e8f0',
    padding: '12px',
    fontSize: '13px'
  },

  searchBtn: {
    background:
      'linear-gradient(135deg, #0284c7, #2563eb)',
    color: 'white',
    border: 'none',
    padding: '12px 18px',
    fontSize: '11px',
    fontWeight: '800',
    letterSpacing: '0.8px',
    cursor: 'pointer'
  },

  rolePicker: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },

  roleLabel: {
    color: '#475569',
    fontSize: '9px',
    fontWeight: '800',
    letterSpacing: '1px'
  },

  select: {
    background: '#111c2d',
    color: '#cbd5e1',
    border:
      '1px solid rgba(148,163,184,0.16)',
    borderRadius: '8px',
    padding: '9px 10px',
    fontSize: '11px',
    outline: 'none'
  },

  content: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
    background:
      'linear-gradient(180deg, #0a1220, #080e18)'
  },

  errorBanner: {
    padding: '13px 16px',
    background: 'rgba(239,68,68,0.08)',
    border:
      '1px solid rgba(239,68,68,0.25)',
    borderRadius: '9px',
    color: '#f87171',
    display: 'flex',
    gap: '12px',
    marginBottom: '16px',
    fontSize: '12px'
  },

  summaryCard: {
    padding: '20px',
    background:
      'linear-gradient(145deg, rgba(17,28,45,0.95), rgba(11,19,32,0.95))',
    border:
      '1px solid rgba(56,189,248,0.12)',
    borderRadius: '14px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '20px',
    flexWrap: 'wrap',
    boxShadow:
      'inset 0 1px rgba(255,255,255,0.03)'
  },

  targetSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '9px'
  },

  sectionEyebrow: {
    color: '#38bdf8',
    fontSize: '9px',
    fontWeight: '800',
    letterSpacing: '1.5px'
  },

  plateRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  },

  anprPlate: {
    display: 'flex',
    alignItems: 'center',
    background: '#f5f5f5',
    borderRadius: '5px',
    overflow: 'hidden',
    boxShadow:
      '0 4px 15px rgba(0,0,0,0.25)'
  },

  anprInd: {
    background: '#075985',
    color: 'white',
    padding: '9px 7px',
    fontSize: '9px',
    fontWeight: '900',
    letterSpacing: '1px'
  },

  anprText: {
    color: '#020617',
    padding: '7px 12px',
    fontFamily: 'monospace',
    fontSize: '17px',
    fontWeight: '900',
    letterSpacing: '1.5px'
  },

  statusTag: {
    display: 'flex',
    alignItems: 'center',
    gap: '7px',
    padding: '6px 10px',
    borderRadius: '20px',
    fontSize: '9px',
    fontWeight: '800',
    letterSpacing: '0.7px'
  },

  statusDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: 'currentColor'
  },

  metrics: {
    display: 'flex',
    alignItems: 'center',
    gap: '18px'
  },

  metric: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  },

  metricLabel: {
    color: '#475569',
    fontSize: '8px',
    fontWeight: '800',
    letterSpacing: '1px'
  },

  metricValue: {
    color: '#e2e8f0',
    fontSize: '22px',
    fontWeight: '800'
  },

  metricValueSmall: {
    color: '#cbd5e1',
    fontSize: '11px',
    fontWeight: '700',
    maxWidth: '190px'
  },

  metricDivider: {
    width: '1px',
    height: '34px',
    background:
      'rgba(148,163,184,0.12)'
  },

  detailsBtn: {
    background:
      'rgba(14,165,233,0.08)',
    border:
      '1px solid rgba(14,165,233,0.25)',
    color: '#38bdf8',
    borderRadius: '8px',
    padding: '10px 13px',
    fontSize: '9px',
    fontWeight: '800',
    letterSpacing: '0.6px',
    cursor: 'pointer'
  },

  loadingBox: {
    marginTop: '14px',
    padding: '13px',
    background: 'rgba(14,165,233,0.06)',
    border:
      '1px solid rgba(14,165,233,0.15)',
    color: '#38bdf8',
    textAlign: 'center',
    fontSize: '10px',
    letterSpacing: '1px'
  },

  spinner: {
    display: 'inline-block',
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#38bdf8',
    marginRight: '8px',
    boxShadow:
      '0 0 12px rgba(56,189,248,0.8)'
  },

  profileErrorBox: {
    marginTop: '14px',
    padding: '16px',
    background: 'rgba(239,68,68,0.06)',
    border:
      '1px solid rgba(239,68,68,0.2)',
    borderRadius: '10px',
    color: '#f87171',
    fontSize: '12px'
  },

  profileErrorTitle: {
    fontWeight: '800',
    letterSpacing: '1px',
    marginBottom: '5px'
  },

  profileErrorText: {
    color: '#cbd5e1',
    marginBottom: '8px'
  },

  profileCard: {
    marginTop: '14px',
    padding: '20px',
    background:
      'linear-gradient(145deg, #101b2d, #0c1524)',
    border:
      '1px solid rgba(56,189,248,0.12)',
    borderRadius: '12px'
  },

  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: '14px',
    borderBottom:
      '1px solid rgba(148,163,184,0.1)',
    marginBottom: '16px'
  },

  cardEyebrow: {
    color: '#38bdf8',
    fontSize: '8px',
    fontWeight: '800',
    letterSpacing: '1.2px'
  },

  cardTitle: {
    margin: '4px 0 0',
    color: '#e2e8f0',
    fontSize: '15px'
  },

  registryBadge: {
    color: '#64748b',
    border:
      '1px solid rgba(148,163,184,0.15)',
    padding: '5px 8px',
    borderRadius: '5px',
    fontSize: '9px',
    fontWeight: '800'
  },

  profileGrid: {
    display: 'grid',
    gridTemplateColumns:
      'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '10px'
  },

  profileItem: {
    padding: '11px',
    background:
      'rgba(255,255,255,0.025)',
    borderRadius: '7px',
    display: 'flex',
    flexDirection: 'column',
    gap: '5px',
    fontSize: '10px'
  },

  profileFooter: {
    marginTop: '14px',
    paddingTop: '11px',
    borderTop:
      '1px dashed rgba(148,163,184,0.15)',
    color: '#34d399',
    fontSize: '8px',
    fontWeight: '800',
    letterSpacing: '0.7px',
    display: 'flex',
    gap: '10px'
  },

  alertsBox: {
    marginTop: '14px',
    padding: '16px',
    background:
      'rgba(239,68,68,0.045)',
    border:
      '1px solid rgba(239,68,68,0.18)',
    borderRadius: '10px'
  },

  alertHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px'
  },

  alertSignal: {
    width: '27px',
    height: '27px',
    borderRadius: '7px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(239,68,68,0.12)',
    color: '#f87171',
    fontWeight: '900'
  },

  alertTitle: {
    color: '#f87171',
    fontSize: '10px',
    fontWeight: '800',
    letterSpacing: '1px'
  },

  alertSubtitle: {
    color: '#64748b',
    fontSize: '9px',
    marginTop: '2px'
  },

  alertList: {
    marginTop: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '5px'
  },

  alertItem: {
    padding: '8px 10px',
    background: 'rgba(239,68,68,0.06)',
    color: '#cbd5e1',
    borderRadius: '5px',
    fontSize: '11px'
  },

  timelineTitle: {
    marginTop: '28px',
    marginBottom: '16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'end'
  },

  timelineHeading: {
    margin: '4px 0 0',
    color: '#f1f5f9',
    fontSize: '19px',
    fontWeight: '800'
  },

  evidenceLabel: {
    color: '#34d399',
    fontSize: '8px',
    fontWeight: '800',
    letterSpacing: '1px'
  },

  emptyState: {
    padding: '30px',
    textAlign: 'center',
    color: '#475569',
    fontSize: '10px',
    letterSpacing: '1px'
  },

  timeline: {
    position: 'relative',
    paddingLeft: '42px'
  },

  timelineItem: {
    position: 'relative',
    marginBottom: '14px'
  },

  timelineLine: {
    position: 'absolute',
    left: '-24px',
    top: '27px',
    bottom: '-20px',
    width: '1px',
    background:
      'linear-gradient(#0ea5e9, rgba(14,165,233,0.03))'
  },

  timelineMarker: {
    position: 'absolute',
    left: '-42px',
    top: '0',
    width: '34px',
    height: '34px',
    borderRadius: '9px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background:
      'linear-gradient(135deg, #0c4a6e, #0369a1)',
    color: '#bae6fd',
    fontSize: '9px',
    fontWeight: '900',
    boxShadow:
      '0 0 18px rgba(14,165,233,0.12)'
  },

  timelineContent: {
    background:
      'linear-gradient(145deg, #101b2d, #0d1726)',
    border:
      '1px solid rgba(148,163,184,0.1)',
    borderRadius: '11px',
    padding: '16px'
  },

  timelineHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: '10px',
    alignItems: 'center',
    flexWrap: 'wrap',
    paddingBottom: '12px',
    borderBottom:
      '1px solid rgba(148,163,184,0.08)'
  },

  timelineTime: {
    color: '#e2e8f0',
    fontSize: '12px',
    fontWeight: '800',
    fontFamily: 'monospace'
  },

  timelineCamera: {
    marginTop: '4px',
    color: '#64748b',
    fontSize: '10px'
  },

  badgeGroup: {
    display: 'flex',
    gap: '6px'
  },

  deptBadge: {
    padding: '4px 7px',
    background:
      'rgba(14,165,233,0.08)',
    border:
      '1px solid rgba(14,165,233,0.15)',
    color: '#38bdf8',
    borderRadius: '5px',
    fontSize: '8px',
    fontWeight: '800'
  },

  camBadge: {
    padding: '4px 7px',
    background:
      'rgba(34,197,94,0.07)',
    color: '#4ade80',
    borderRadius: '5px',
    fontSize: '8px',
    fontWeight: '800'
  },

  timelineBody: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '20px',
    paddingTop: '13px'
  },

  metaCol: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '9px'
  },

  dataRow: {
    display: 'flex',
    justifyContent: 'space-between',
    maxWidth: '440px',
    paddingBottom: '6px',
    borderBottom:
      '1px solid rgba(148,163,184,0.05)',
    fontSize: '9px'
  },

  confidence: {
    color: '#34d399'
  },

  evidenceThumbWrap: {
    cursor: 'pointer',
    width: '170px',
    flexShrink: 0
  },

  evidenceFrame: {
    position: 'relative',
    width: '170px',
    height: '96px',
    borderRadius: '7px',
    overflow: 'hidden',
    border:
      '1px solid rgba(56,189,248,0.25)',
    background: '#020617'
  },

  evidenceThumb: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    display: 'block'
  },

  evidenceOverlay: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background:
      'rgba(2,6,23,0.45)',
    color: '#e0f2fe',
    fontSize: '9px',
    fontWeight: '900',
    letterSpacing: '1px',
    opacity: 0,
    transition: 'opacity 0.2s ease'
  },

  thumbCaption: {
    marginTop: '5px',
    color: '#475569',
    fontSize: '8px',
    fontWeight: '800',
    letterSpacing: '0.8px',
    textAlign: 'right'
  },

  zoomOverlay: {
    position: 'fixed',
    inset: 0,
    background:
      'rgba(0,0,0,0.88)',
    backdropFilter: 'blur(14px)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2000,
    padding: '30px'
  },

  zoomContent: {
    width: '900px',
    maxWidth: '94vw',
    maxHeight: '92vh',
    background: '#080f1b',
    border:
      '1px solid rgba(56,189,248,0.2)',
    borderRadius: '14px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    boxShadow:
      '0 30px 100px rgba(0,0,0,0.7)'
  },

  zoomHeader: {
    color: '#e2e8f0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '4px 4px 14px'
  },

  zoomEyebrow: {
    color: '#38bdf8',
    fontSize: '8px',
    fontWeight: '800',
    letterSpacing: '1px',
    marginBottom: '3px'
  },

  zoomClose: {
    width: '34px',
    height: '34px',
    borderRadius: '7px',
    border:
      '1px solid rgba(255,255,255,0.1)',
    background: 'rgba(255,255,255,0.04)',
    color: '#94a3b8',
    fontSize: '20px',
    cursor: 'pointer'
  },

  imageContainer: {
    flex: 1,
    minHeight: 0,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    background: '#020617',
    borderRadius: '8px',
    overflow: 'hidden'
  },

  zoomedImg: {
    maxWidth: '100%',
    maxHeight: '72vh',
    objectFit: 'contain'
  },

  zoomFooter: {
    marginTop: '10px',
    display: 'flex',
    gap: '15px',
    color: '#475569',
    fontSize: '8px',
    letterSpacing: '0.6px',
    overflow: 'hidden'
  }
};

export default InvestigatorModal;