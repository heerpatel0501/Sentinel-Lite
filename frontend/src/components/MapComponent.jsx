import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';

const DEPT_COLORS = {
  Police: '#ef4444',
  RTO: '#3b82f6',
  GSRTC: '#f59e0b',
  Municipal: '#10b981'
};

function MapComponent({ cameras, onMarkerClick }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef([]);

  // Initialize map
  useEffect(() => {
    if (map.current) return;

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
      center: [72.5, 22.5],
      zoom: 7
    });

    map.current.addControl(
      new maplibregl.NavigationControl(),
      'top-right'
    );

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Add cameras to map
  useEffect(() => {
    if (!map.current || !cameras || cameras.length === 0) {
      return;
    }

    const addCameraMarkers = () => {
      // Remove existing markers
      markersRef.current.forEach((marker) => {
        marker.remove();
      });

      markersRef.current = [];

      // Add every camera
      cameras.forEach((camera) => {
        const latitude = parseFloat(camera.latitude);
        const longitude = parseFloat(camera.longitude);

        // Ignore invalid coordinates
        if (
          !Number.isFinite(latitude) ||
          !Number.isFinite(longitude)
        ) {
          console.warn(
            'Invalid camera coordinates:',
            camera
          );
          return;
        }

        const color =
          DEPT_COLORS[camera.department] || '#94a3b8';

        // Marker element
        const el = document.createElement('div');

        el.style.width = '22px';
        el.style.height = '22px';
        el.style.backgroundColor = color;
        el.style.borderRadius = '50%';
        el.style.border = '3px solid white';
        el.style.boxShadow = '0 2px 6px rgba(0,0,0,0.4)';
        el.style.cursor = 'pointer';

        // Camera number
        const label = document.createElement('span');

        label.innerText = camera.id;

        label.style.position = 'absolute';
        label.style.left = '50%';
        label.style.top = '50%';
        label.style.transform = 'translate(-50%, -50%)';
        label.style.fontSize = '9px';
        label.style.fontWeight = 'bold';
        label.style.color = 'white';
        label.style.pointerEvents = 'none';

        el.appendChild(label);

        // Camera click
        el.addEventListener('click', () => {
          onMarkerClick(camera);

          if (map.current) {
            map.current.flyTo({
              center: [
                longitude,
                latitude
              ],
              zoom: 14
            });
          }
        });

        // Create marker
        const marker = new maplibregl.Marker({
          element: el,
          anchor: 'center'
        })
          .setLngLat([
            longitude,
            latitude
          ])
          .setPopup(
            new maplibregl.Popup({
              offset: 15
            }).setHTML(`
              <strong>${camera.name}</strong><br/>
              Department: ${camera.department}<br/>
              Status: ${camera.status}<br/>
              ID: ${camera.id}
            `)
          )
          .addTo(map.current);

        markersRef.current.push(marker);
      });

      // Automatically fit all cameras
      if (cameras.length > 1) {
        const bounds = new maplibregl.LngLatBounds();

        cameras.forEach((camera) => {
          const latitude = parseFloat(camera.latitude);
          const longitude = parseFloat(camera.longitude);

          if (
            Number.isFinite(latitude) &&
            Number.isFinite(longitude)
          ) {
            bounds.extend([
              longitude,
              latitude
            ]);
          }
        });

        if (!bounds.isEmpty()) {
          map.current.fitBounds(bounds, {
            padding: 80,
            maxZoom: 8
          });
        }
      }
    };

    // Wait until map is ready
    if (map.current.loaded()) {
      addCameraMarkers();
    } else {
      map.current.once('load', addCameraMarkers);
    }

    return () => {
      markersRef.current.forEach((marker) => {
        marker.remove();
      });

      markersRef.current = [];
    };
  }, [cameras, onMarkerClick]);

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative'
      }}
    >
      <div
        ref={mapContainer}
        style={{
          width: '100%',
          height: '100%'
        }}
      />

      {/* Legend */}
      <div
        style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          backgroundColor: 'white',
          padding: '12px',
          borderRadius: '6px',
          boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
          zIndex: 2
        }}
      >
        <h4
          style={{
            margin: '0 0 10px 0',
            fontSize: '14px'
          }}
        >
          Departments
        </h4>

        {Object.entries(DEPT_COLORS).map(
          ([dept, color]) => (
            <div
              key={dept}
              style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '6px'
              }}
            >
              <div
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: color,
                  borderRadius: '50%',
                  marginRight: '8px'
                }}
              />

              <span style={{ fontSize: '12px' }}>
                {dept}
              </span>
            </div>
          )
        )}

        <div
          style={{
            marginTop: '8px',
            paddingTop: '8px',
            borderTop: '1px solid #ddd',
            fontSize: '12px',
            fontWeight: 'bold'
          }}
        >
          Cameras: {cameras.length}
        </div>
      </div>
    </div>
  );
}

export default MapComponent;