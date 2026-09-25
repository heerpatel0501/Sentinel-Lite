CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    department VARCHAR(50) NOT NULL,
    vms_vendor VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    resolution VARCHAR(20) NOT NULL,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: We use DOUBLE PRECISION for lat/long instead of PostGIS geometry types for simplicity in this MVP,
-- but the postgis extension is enabled for future geospatial queries if needed.

INSERT INTO cameras (name, latitude, longitude, department, vms_vendor, status, resolution) VALUES
-- Ahmedabad
('AHM-Junction-01', 23.0225, 72.5714, 'Police', 'Milestone', 'online', '1080p'),
('AHM-Traffic-02', 23.0250, 72.5740, 'RTO', 'Hikvision', 'online', '4K'),
('AHM-BusStop-03', 23.0200, 72.5700, 'GSRTC', 'Genetec', 'online', '1080p'),
('AHM-Park-04', 23.0300, 72.5800, 'Municipal', 'Dahua', 'offline', '720p'),

-- Rajkot
('RJK-MainRoad-01', 22.3039, 70.8022, 'Police', 'Genetec', 'online', '1080p'),
('RJK-Crossroad-02', 22.3050, 70.8050, 'RTO', 'Milestone', 'online', '4K'),
('RJK-Station-03', 22.3000, 70.8000, 'GSRTC', 'Hikvision', 'offline', '1080p'),
('RJK-Square-04', 22.3100, 70.8100, 'Municipal', 'Milestone', 'online', '720p'),

-- Surat
('SRT-Highway-01', 21.1702, 72.8311, 'Police', 'Hikvision', 'online', '4K'),
('SRT-Toll-02', 21.1750, 72.8350, 'RTO', 'Dahua', 'online', '1080p'),
('SRT-Depot-03', 21.1650, 72.8250, 'GSRTC', 'Genetec', 'online', '1080p'),
('SRT-Market-04', 21.1800, 72.8400, 'Municipal', 'Milestone', 'online', '1080p'),

-- Vadodara
('VAD-Entry-01', 22.3072, 73.1812, 'Police', 'Milestone', 'online', '1080p'),
('VAD-Bridge-02', 22.3100, 73.1850, 'RTO', 'Genetec', 'offline', '4K'),
('VAD-Terminal-03', 22.3000, 73.1750, 'GSRTC', 'Hikvision', 'online', '1080p'),
('VAD-Plaza-04', 22.3150, 73.1900, 'Municipal', 'Dahua', 'online', '720p'),

-- Gandhinagar
('GND-Secretariat-01', 23.2156, 72.6369, 'Police', 'Genetec', 'online', '4K'),
('GND-Circle-02', 23.2200, 72.6400, 'RTO', 'Milestone', 'online', '1080p'),
('GND-BusStand-03', 23.2100, 72.6300, 'GSRTC', 'Dahua', 'online', '1080p'),
('GND-Sector-04', 23.2250, 72.6450, 'Municipal', 'Hikvision', 'offline', '1080p');
