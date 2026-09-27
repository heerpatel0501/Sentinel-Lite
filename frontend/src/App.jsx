import React, { useState, useEffect } from 'react';
import MapComponent from './components/MapComponent';
import StatsBar from './components/StatsBar';
import AlertsSidebar from './components/AlertsSidebar';
import VideoModal from './components/VideoModal';
import InvestigatorModal from './components/InvestigatorModal';

// Backend URL - assuming running on localhost
const API_BASE = 'http://localhost:8000';

function App() {
  const [cameras, setCameras] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [health, setHealth] = useState(null);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [currentRole, setCurrentRole] = useState('analyst');
  
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [streamInfo, setStreamInfo] = useState(null);

  // Investigator Dossier Modal State
  const [investigatorPlate, setInvestigatorPlate] = useState(null);
  const [isInvestigatorOpen, setIsInvestigatorOpen] = useState(false);

  const openInvestigator = (plate = 'GJ01-AB-1234') => {
    setInvestigatorPlate(plate);
    setIsInvestigatorOpen(true);
  };

  const fetchAlertsAndHealth = () => {
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error("Health fetch error:", err));

    fetch(`${API_BASE}/alerts`, {
      headers: {
        'X-User-Role': currentRole,
        'X-User-Id': '1'
      }
    })
      .then(res => res.json())
      .then(data => {
        setAlerts(data);
        setAlertsLoading(false);
      })
      .catch(err => {
        console.error("Alerts fetch error:", err);
        setAlertsLoading(false);
      });
  };

  useEffect(() => {
    // Initial fetch of cameras
    fetch(`${API_BASE}/cameras`)
      .then(res => res.json())
      .then(data => setCameras(data))
      .catch(err => console.error("Cameras fetch error:", err));

    // Fetch initial health and alerts
    fetchAlertsAndHealth();

    // Set up live telemetry and alert feed polling (5s interval)
    const intervalId = setInterval(fetchAlertsAndHealth, 5000);
    return () => clearInterval(intervalId);
  }, [currentRole]);

  const handleViewFeed = (cameraId) => {
    fetch(`${API_BASE}/cameras/${cameraId}/stream`)
      .then(res => res.json())
      .then(data => {
        setStreamInfo(data);
        setIsModalOpen(true);
      })
      .catch(err => {
        console.error("Failed to fetch stream:", err);
        alert("Failed to load stream");
      });
  };

  const closeFeed = () => {
    setIsModalOpen(false);
    setStreamInfo(null);
  };

  return (
    <div style={styles.appContainer}>
      {/* High Contrast Command Center Header */}
      <StatsBar 
        health={health} 
        currentRole={currentRole}
        onRoleChange={setCurrentRole}
        onOpenSearch={openInvestigator} 
      />
      
      <div style={styles.mainLayout}>
        {/* Interactive GIS Map Canvas */}
        <div style={styles.mapArea}>
          <MapComponent 
            cameras={cameras} 
            onMarkerClick={setSelectedCamera} 
          />
          
          {/* Selected Camera Telemetry Popup */}
          {selectedCamera && (
            <div style={styles.cameraCard}>
              <div style={styles.cardHeader}>
                <h3 style={styles.cameraTitle}>{selectedCamera.name}</h3>
                <span style={{
                  ...styles.statusTag,
                  color: selectedCamera.status === 'online' ? '#10b981' : '#ef4444',
                  backgroundColor: selectedCamera.status === 'online' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'
                }}>
                  {selectedCamera.status.toUpperCase()}
                </span>
              </div>

              <div style={styles.cardRow}>
                <span style={styles.cardLabel}>DEPARTMENT:</span>
                <span style={styles.cardValue}>{selectedCamera.department}</span>
              </div>
              <div style={styles.cardRow}>
                <span style={styles.cardLabel}>VMS VENDOR:</span>
                <span style={styles.cardValue}>{selectedCamera.vms_vendor}</span>
              </div>
              <div style={styles.cardRow}>
                <span style={styles.cardLabel}>RESOLUTION:</span>
                <span style={styles.cardValue}>{selectedCamera.resolution}</span>
              </div>

              <div style={styles.cardActions}>
                <button 
                  onClick={() => handleViewFeed(selectedCamera.id)}
                  style={styles.viewFeedBtn}
                >
                  ▶ View Live Feed
                </button>
                <button 
                  onClick={() => setSelectedCamera(null)}
                  style={styles.closeCardBtn}
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
        
        {/* Real-time Alerts Sidebar */}
        <AlertsSidebar 
          alerts={alerts} 
          isLoading={alertsLoading}
          onSelectPlate={openInvestigator} 
        />
      </div>

      {/* Live Video Modal */}
      {isModalOpen && streamInfo && (
        <VideoModal 
          streamInfo={streamInfo} 
          onClose={closeFeed} 
          cameraName={selectedCamera?.name} 
        />
      )}

      {/* Forensic Investigator Dossier Modal */}
      {isInvestigatorOpen && (
        <InvestigatorModal 
          initialPlate={investigatorPlate} 
          onClose={() => setIsInvestigatorOpen(false)} 
        />
      )}
    </div>
  );
}

const styles = {
  appContainer: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    backgroundColor: '#0b0f19',
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
  },
  mainLayout: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
    backgroundColor: '#0b0f19'
  },
  mapArea: {
    flex: 1,
    position: 'relative'
  },
  cameraCard: {
    position: 'absolute',
    bottom: '24px',
    left: '24px',
    backgroundColor: '#111827',
    border: '1px solid #374151',
    color: '#f9fafb',
    padding: '18px',
    borderRadius: '10px',
    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
    zIndex: 10,
    minWidth: '260px',
    backdropFilter: 'blur(8px)'
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
    borderBottom: '1px solid #374151',
    paddingBottom: '8px'
  },
  cameraTitle: {
    margin: 0,
    fontSize: '15px',
    fontWeight: '700',
    color: '#ffffff'
  },
  statusTag: {
    fontSize: '10px',
    fontWeight: '700',
    padding: '2px 6px',
    borderRadius: '4px'
  },
  cardRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '12px',
    marginBottom: '6px'
  },
  cardLabel: {
    color: '#9ca3af',
    fontWeight: '600'
  },
  cardValue: {
    color: '#e5e7eb',
    fontWeight: '500'
  },
  cardActions: {
    display: 'flex',
    gap: '8px',
    marginTop: '14px'
  },
  viewFeedBtn: {
    flex: 1,
    padding: '8px 12px',
    backgroundColor: '#2563eb',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer'
  },
  closeCardBtn: {
    padding: '8px 12px',
    backgroundColor: '#374151',
    color: '#d1d5db',
    border: 'none',
    borderRadius: '6px',
    fontSize: '12px',
    cursor: 'pointer'
  }
};

export default App;
