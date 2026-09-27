import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';

const DEPT_COLORS = {
  'Police': '#ef4444',  // red
  'RTO': '#3b82f6',     // blue
  'GSRTC': '#f59e0b',   // amber
  'Municipal': '#10b981' // green
};

function MapComponent({ cameras, onMarkerClick }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef([]);

  useEffect(() => {
    if (map.current) return; // initialize map only once

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: [
              'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors'
          }
        },
        layers: [
          {
            id: 'osm-tiles-layer',
            type: 'raster',
            source: 'osm-tiles',
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [71.1924, 22.2587], // Gujarat center
      zoom: 6
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
  }, []);

  useEffect(() => {
    if (!map.current || !cameras.length) return;

    // Clear old markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add new markers
    cameras.forEach(camera => {
      const color = DEPT_COLORS[camera.department] || '#94a3b8';
      
      const el = document.createElement('div');
      el.style.width = '20px';
      el.style.height = '20px';
      el.style.backgroundColor = color;
      el.style.borderRadius = '50%';
      el.style.border = '2px solid white';
      el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
      el.style.cursor = 'pointer';

      el.addEventListener('click', () => {
        onMarkerClick(camera);
        map.current.flyTo({
          center: [camera.longitude, camera.latitude],
          zoom: 12
        });
      });

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([camera.longitude, camera.latitude])
        .addTo(map.current);
        
      markersRef.current.push(marker);
    });
  }, [cameras, onMarkerClick]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      
      {/* Legend */}
      <div style={{
        position: 'absolute', top: '20px', left: '20px',
        backgroundColor: 'white', padding: '10px', borderRadius: '4px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)', zIndex: 1
      }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Departments</h4>
        {Object.entries(DEPT_COLORS).map(([dept, color]) => (
          <div key={dept} style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: color, borderRadius: '50%', marginRight: '8px' }}></div>
            <span style={{ fontSize: '12px' }}>{dept}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MapComponent;
