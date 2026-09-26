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

  useEffect(() => {
    // Fetch initial data
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error(err));

    fetch(`${API_BASE}/cameras`)
      .then(res => res.json())
      .then(data => setCameras(data))
      .catch(err => console.error(err));

    fetch(`${API_BASE}/alerts`)
      .then(res => res.json())
      .then(data => setAlerts(data))
      .catch(err => console.error(err));
  }, []);

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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#f0f2f5' }}>
      <StatsBar health={health} onOpenSearch={openInvestigator} />
      
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <MapComponent 
            cameras={cameras} 
            onMarkerClick={setSelectedCamera} 
          />
          
          {selectedCamera && (
            <div style={{
              position: 'absolute', bottom: '20px', left: '20px', 
              backgroundColor: 'white', padding: '15px', borderRadius: '8px',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)', zIndex: 10
            }}>
              <h3 style={{ margin: '0 0 10px 0' }}>{selectedCamera.name}</h3>
              <p style={{ margin: '5px 0' }}><strong>Dept:</strong> {selectedCamera.department}</p>
              <p style={{ margin: '5px 0' }}><strong>Status:</strong> {selectedCamera.status}</p>
              <button 
                onClick={() => handleViewFeed(selectedCamera.id)}
                style={{
                  marginTop: '10px', padding: '8px 16px', 
                  backgroundColor: '#0066cc', color: 'white', 
                  border: 'none', borderRadius: '4px', cursor: 'pointer'
                }}
              >
                View Feed
              </button>
              <button 
                onClick={() => setSelectedCamera(null)}
                style={{
                  marginTop: '10px', marginLeft: '10px', padding: '8px 16px', 
                  backgroundColor: '#ccc', color: 'black', 
                  border: 'none', borderRadius: '4px', cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          )}
        </div>
        
        <AlertsSidebar 
          alerts={alerts} 
          onSelectPlate={openInvestigator} 
        />
      </div>

      {isModalOpen && streamInfo && (
        <VideoModal streamInfo={streamInfo} onClose={closeFeed} cameraName={selectedCamera?.name} />
      )}

      {isInvestigatorOpen && (
        <InvestigatorModal 
          initialPlate={investigatorPlate} 
          onClose={() => setIsInvestigatorOpen(false)} 
        />
      )}
    </div>
  );
}

export default App;
