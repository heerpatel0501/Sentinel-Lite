CREATE EXTENSION IF NOT EXISTS postgis;

-- =============================================================================
-- 1. CAMERAS (State-wide CCTV Hardware Registry)
-- =============================================================================
CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    department VARCHAR(50) NOT NULL,
    vms_vendor VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    resolution VARCHAR(20) NOT NULL,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    onvif_host VARCHAR(255),
    onvif_port INTEGER,
    onvif_username VARCHAR(255),
    onvif_password VARCHAR(255)
);

INSERT INTO cameras (name, latitude, longitude, department, vms_vendor, status, resolution, onvif_host, onvif_port, onvif_username, onvif_password) VALUES
-- Ahmedabad
('AHM-Junction-01', 23.0225, 72.5714, 'Police', 'Milestone', 'online', '1080p', NULL, NULL, NULL, NULL),
('AHM-Traffic-02', 23.0250, 72.5740, 'RTO', 'Hikvision', 'online', '4K', NULL, NULL, NULL, NULL),
('AHM-BusStop-03', 23.0200, 72.5700, 'GSRTC', 'Genetec', 'online', '1080p', NULL, NULL, NULL, NULL),
('AHM-Park-04', 23.0300, 72.5800, 'Municipal', 'Dahua', 'offline', '720p', NULL, NULL, NULL, NULL),
-- Rajkot
('RJK-MainRoad-01', 22.3039, 70.8022, 'Police', 'Genetec', 'online', '1080p', NULL, NULL, NULL, NULL),
('RJK-Crossroad-02', 22.3050, 70.8050, 'RTO', 'Milestone', 'online', '4K', NULL, NULL, NULL, NULL),
('RJK-Station-03', 22.3000, 70.8000, 'GSRTC', 'Hikvision', 'offline', '1080p', NULL, NULL, NULL, NULL),
('RJK-Square-04', 22.3100, 70.8100, 'Municipal', 'Milestone', 'online', '720p', NULL, NULL, NULL, NULL),
-- Surat
('SRT-Highway-01', 21.1702, 72.8311, 'Police', 'Hikvision', 'online', '4K', NULL, NULL, NULL, NULL),
('SRT-Toll-02', 21.1750, 72.8350, 'RTO', 'Dahua', 'online', '1080p', NULL, NULL, NULL, NULL),
('SRT-Depot-03', 21.1650, 72.8250, 'GSRTC', 'Genetec', 'online', '1080p', NULL, NULL, NULL, NULL),
('SRT-Market-04', 21.1800, 72.8400, 'Municipal', 'Milestone', 'online', '1080p', NULL, NULL, NULL, NULL),
-- Vadodara
('VAD-Entry-01', 22.3072, 73.1812, 'Police', 'Milestone', 'online', '1080p', NULL, NULL, NULL, NULL),
('VAD-Bridge-02', 22.3100, 73.1850, 'RTO', 'Genetec', 'offline', '4K', NULL, NULL, NULL, NULL),
('VAD-Terminal-03', 22.3000, 73.1750, 'GSRTC', 'Hikvision', 'online', '1080p', NULL, NULL, NULL, NULL),
('VAD-Plaza-04', 22.3150, 73.1900, 'Municipal', 'Dahua', 'online', '720p', NULL, NULL, NULL, NULL),
-- Gandhinagar
('GND-Secretariat-01', 23.2156, 72.6369, 'Police', 'Genetec', 'online', '4K', NULL, NULL, NULL, NULL),
('GND-Circle-02', 23.2200, 72.6400, 'RTO', 'Milestone', 'online', '1080p', NULL, NULL, NULL, NULL),
('GND-BusStand-03', 23.2100, 72.6300, 'GSRTC', 'Dahua', 'online', '1080p', NULL, NULL, NULL, NULL),
('GND-Sector-04', 23.2250, 72.6450, 'Municipal', 'Hikvision', 'offline', '1080p', NULL, NULL, NULL, NULL),
-- Mock ONVIF Camera
('TEST-ONVIF-01', 23.0000, 72.0000, 'Police', 'ONVIF', 'online', '1080p', '192.168.1.64', 80, 'admin', 'vault_demo_key')
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- 2. DEPARTMENTS (Gujarat Administrative Bodies)
-- =============================================================================
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    contact_email VARCHAR(255) NOT NULL
);

INSERT INTO departments (name, contact_email) VALUES
('Police', 'controlroom@gujaratpolice.gov.in'),
('RTO', 'helpdesk-rto@gujarat.gov.in'),
('GSRTC', 'centraltransit@gsrtc.in'),
('Municipal', 'smartcity@ahmedabadcity.gov.in'),
('Panchayat', 'panchayat-sec@gujarat.gov.in')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- 3. VEHICLE_DETECTIONS (REAL: Populated dynamically by YOLOv8 /detect)
-- =============================================================================
CREATE TABLE IF NOT EXISTS vehicle_detections (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vehicle_type VARCHAR(50) NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    bounding_box JSON NOT NULL,
    frame_snapshot_path VARCHAR(500)
);

INSERT INTO vehicle_detections (camera_id, vehicle_type, confidence_score, bounding_box, frame_snapshot_path) VALUES
(1, 'car', 0.92, '[0.22, 0.55, 0.51, 0.76]', '/snapshots/det_ahm_01.jpg'),
(11, 'bus', 0.89, '[0.15, 0.30, 0.60, 0.85]', '/snapshots/det_srt_02.jpg')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- 4. PLATES (MOCKED: Ready for Indian ANPR OCR Corpus in Next Phase)
-- =============================================================================
CREATE TABLE IF NOT EXISTS plates (
    id SERIAL PRIMARY KEY,
    detection_id INTEGER REFERENCES vehicle_detections(id),
    plate_text VARCHAR(50) NOT NULL,
    ocr_confidence DOUBLE PRECISION NOT NULL,
    plate_bounding_box JSON
);

INSERT INTO plates (detection_id, plate_text, ocr_confidence, plate_bounding_box) VALUES
(1, 'GJ01-AB-1234', 0.94, '[0.35, 0.65, 0.45, 0.72]'),
(2, 'GJ05-XX-9999', 0.91, '[0.28, 0.68, 0.40, 0.76]')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- 5. WATCHLIST (Flagged / Stolen / Wanted Plates Registry)
-- =============================================================================
CREATE TABLE IF NOT EXISTS watchlist (
    id SERIAL PRIMARY KEY,
    plate_text VARCHAR(50) NOT NULL,
    reason VARCHAR(50) NOT NULL,
    added_by_department VARCHAR(100) NOT NULL,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

INSERT INTO watchlist (plate_text, reason, added_by_department, active) VALUES
('GJ01AB1234', 'stolen', 'Police', TRUE),
('GJ05XX9999', 'wanted', 'Police', TRUE),
('GJ03MC4567', 'flagged', 'RTO', TRUE),
('GJ18ZZ0001', 'flagged', 'Police', TRUE),
('GJ06CD5555', 'stolen', 'Police', FALSE)
ON CONFLICT DO NOTHING;

-- Stream Health & Telemetry Tracking
CREATE TABLE IF NOT EXISTS stream_health (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id),
    status VARCHAR(50) DEFAULT 'active',
    codec VARCHAR(20) DEFAULT 'H.264',
    resolution VARCHAR(20) DEFAULT '1080p',
    last_pts DOUBLE PRECISION DEFAULT 0.0,
    reconnect_attempts INTEGER DEFAULT 0,
    fps_actual DOUBLE PRECISION DEFAULT 0.0,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 6. VEHICLE_MOVEMENTS (Powers Cross-Department Correlation with Evidence Traceability)
-- =============================================================================
CREATE TABLE IF NOT EXISTS vehicle_movements (
    id SERIAL PRIMARY KEY,
    plate_text VARCHAR(50) NOT NULL,
    camera_id INTEGER REFERENCES cameras(id),
    department_id INTEGER REFERENCES departments(id),
    detection_id INTEGER REFERENCES vehicle_detections(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO vehicle_movements (plate_text, camera_id, department_id, detection_id, timestamp) VALUES
-- Target 1: GJ01-AB-1234 (seen across Police, RTO, Municipal)
('GJ01-AB-1234', 1, 1, 1, CURRENT_TIMESTAMP - INTERVAL '45 minutes'),
('GJ01-AB-1234', 2, 2, NULL, CURRENT_TIMESTAMP - INTERVAL '30 minutes'),
('GJ01-AB-1234', 4, 4, NULL, CURRENT_TIMESTAMP - INTERVAL '10 minutes'),

-- Target 2: GJ05-XX-9999 (seen across Police, GSRTC)
('GJ05-XX-9999', 9, 1, NULL, CURRENT_TIMESTAMP - INTERVAL '60 minutes'),
('GJ05-XX-9999', 11, 3, 2, CURRENT_TIMESTAMP - INTERVAL '20 minutes'),

-- Target 3: GJ03-MC-4567 (seen across RTO, Municipal)
('GJ03-MC-4567', 6, 2, NULL, CURRENT_TIMESTAMP - INTERVAL '75 minutes'),
('GJ03-MC-4567', 8, 4, NULL, CURRENT_TIMESTAMP - INTERVAL '35 minutes'),

-- Target 4: GJ18-ZZ-0001 (seen across Police, RTO)
('GJ18-ZZ-0001', 17, 1, NULL, CURRENT_TIMESTAMP - INTERVAL '80 minutes'),
('GJ18-ZZ-0001', 18, 2, NULL, CURRENT_TIMESTAMP - INTERVAL '40 minutes'),

-- Target 5: GJ06-CD-5555 (seen across Police, GSRTC)
('GJ06-CD-5555', 13, 1, NULL, CURRENT_TIMESTAMP - INTERVAL '95 minutes'),
('GJ06-CD-5555', 15, 3, NULL, CURRENT_TIMESTAMP - INTERVAL '50 minutes'),

-- Routine traffic sightings
('GJ27-AA-1122', 3, 3, NULL, CURRENT_TIMESTAMP - INTERVAL '110 minutes'),
('GJ02-BB-3344', 10, 2, NULL, CURRENT_TIMESTAMP - INTERVAL '90 minutes'),
('GJ04-EE-7788', 16, 4, NULL, CURRENT_TIMESTAMP - INTERVAL '65 minutes'),
('GJ01-XY-4455', 1, 1, NULL, CURRENT_TIMESTAMP - INTERVAL '50 minutes'),
('GJ01-XY-4455', 2, 2, NULL, CURRENT_TIMESTAMP - INTERVAL '15 minutes')
ON CONFLICT DO NOTHING;

-- Evidence Records (Metadata & URI links; zero video stored in DB)
CREATE TABLE IF NOT EXISTS evidence_records (
    id SERIAL PRIMARY KEY,
    detection_id INTEGER REFERENCES vehicle_detections(id),
    plate_text VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    uri_reference VARCHAR(500) NOT NULL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pts_timestamp DOUBLE PRECISION DEFAULT 0.0,
    file_size_bytes INTEGER DEFAULT 0,
    sha256_hash VARCHAR(64)
);

INSERT INTO evidence_records (detection_id, plate_text, file_path, uri_reference, pts_timestamp, file_size_bytes) VALUES
(1, 'GJ01-AB-1234', 'evidence/snapshots/GJ01-AB-1234_cam1.jpg', '/evidence/snapshots/GJ01-AB-1234_cam1.jpg', 15.2, 42100),
(2, 'GJ05-XX-9999', 'evidence/snapshots/GJ05-XX-9999_cam11.jpg', '/evidence/snapshots/GJ05-XX-9999_cam11.jpg', 32.8, 51400)
ON CONFLICT DO NOTHING;

-- =============================================================================
-- 7. ALERTS (Cross-Department Threat Intelligence Hub)
-- =============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    plate_text VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    camera_ids_involved JSON NOT NULL,
    departments_involved JSON NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'new',
    description VARCHAR(255)
);

INSERT INTO alerts (plate_text, alert_type, camera_ids_involved, departments_involved, timestamp, status, description) VALUES
('GJ01-AB-1234', 'cross_department', '["AHM-Junction-01", "AHM-Traffic-02"]', '["Police", "RTO"]', CURRENT_TIMESTAMP - INTERVAL '15 minutes', 'new', 'Vehicle tracked across Police and RTO cameras.'),
('GJ05-XX-9999', 'watchlist_match', '["SRT-Highway-01", "SRT-Depot-03"]', '["Police", "GSRTC"]', CURRENT_TIMESTAMP - INTERVAL '25 minutes', 'new', 'Suspicious vehicle near GSRTC depot.'),
('GJ03-MC-4567', 'speeding', '["RJK-Crossroad-02", "RJK-Square-04"]', '["RTO", "Municipal"]', CURRENT_TIMESTAMP - INTERVAL '40 minutes', 'reviewed', 'Speeding violation in municipal zone.'),
('GJ18-ZZ-0001', 'watchlist_match', '["GND-Secretariat-01", "GND-Circle-02"]', '["Police", "RTO"]', CURRENT_TIMESTAMP - INTERVAL '55 minutes', 'new', 'VIP convoy route clearance check.')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- 8. USERS (Departmental Access Control)
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    role VARCHAR(50) NOT NULL
);

INSERT INTO users (email, password_hash, department_id, role) VALUES
('admin@gujaratpolice.gov.in', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 1, 'admin'),
('analyst@rto.gujarat.gov.in', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 2, 'analyst'),
('monitor@gsrtc.in', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 3, 'viewer'),
('civic@ahmedabadcity.gov.in', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 4, 'analyst')
ON CONFLICT (email) DO NOTHING;

-- =============================================================================
-- 9. AUDIT_LOGS (DPDP Act Compliance Access Logging)
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO audit_logs (user_id, action, target_type, target_id, timestamp) VALUES
(1, 'VIEW_ALERT_FEED', 'alert', 'ALL', CURRENT_TIMESTAMP - INTERVAL '2 hours'),
(2, 'WATCHLIST_QUERY', 'watchlist', 'GJ01AB1234', CURRENT_TIMESTAMP - INTERVAL '1 hour'),
(1, 'EXPORT_CROSS_DEPT_TRAIL', 'vehicle_movement', 'GJ05-XX-9999', CURRENT_TIMESTAMP - INTERVAL '30 minutes')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- 10. VMS_SYSTEMS (VMS Federation - Phase 1 & 2)
-- =============================================================================
CREATE TABLE IF NOT EXISTS vms_systems (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    vendor VARCHAR(50) NOT NULL,
    host VARCHAR(255),
    port INTEGER DEFAULT 80,
    protocol VARCHAR(20) DEFAULT 'RTSP',
    department_id INTEGER REFERENCES departments(id),
    status VARCHAR(20) DEFAULT 'active',
    sync_interval_seconds INTEGER DEFAULT 300,
    last_sync TIMESTAMP
);

INSERT INTO vms_systems (name, vendor, host, port, protocol, department_id, status, last_sync) VALUES
('Police-Milestone-XProtect', 'Milestone', '10.0.1.10', 80, 'RTSP', 1, 'active', CURRENT_TIMESTAMP),
('RTO-Hikvision-iVMS', 'Hikvision', '10.0.2.10', 8000, 'RTSP', 2, 'active', CURRENT_TIMESTAMP),
('GSRTC-Genetec-Center', 'Genetec', '10.0.3.10', 443, 'RTSP', 3, 'active', CURRENT_TIMESTAMP),
('Municipal-Dahua-DSS', 'Dahua', '10.0.4.10', 37777, 'RTSP', 4, 'active', CURRENT_TIMESTAMP),
('SmartCity-ONVIF-Gateway', 'ONVIF', '192.168.1.64', 80, 'ONVIF', 4, 'active', CURRENT_TIMESTAMP),
('Sentinel-Official-RTSP-Grid', 'Sentinel', 'cctv.corp8.cloud', 554, 'RTSP', 1, 'active', CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- =============================================================================
-- 11. EVENTS (Canonical Event Model - Phase 4)
-- =============================================================================
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100) UNIQUE NOT NULL,
    camera_id INTEGER REFERENCES cameras(id),
    event_type VARCHAR(50) NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence DOUBLE PRECISION DEFAULT 1.0,
    payload JSON
);

-- =============================================================================
-- 12. INVESTIGATIONS (Case Dossier Tracking - Phase 8)
-- =============================================================================
CREATE TABLE IF NOT EXISTS investigations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    case_number VARCHAR(100) UNIQUE NOT NULL,
    target_plate VARCHAR(50),
    lead_investigator_id INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'active',
    priority VARCHAR(20) DEFAULT 'high',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO investigations (title, case_number, target_plate, lead_investigator_id, status, priority, notes) VALUES
('Investigation: Cross-Agency Interception of Stolen Vehicle GJ01-AB-1234', 'CASE-2026-GUJ-0842', 'GJ01-AB-1234', 1, 'active', 'critical', 'Target vehicle flagged in state stolen vehicle registry. Reconstructed path across Ahmedabad and Gandhinagar.')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- 13. INVESTIGATION_EVIDENCE (Forensic Evidence Linking - Phase 8)
-- =============================================================================
CREATE TABLE IF NOT EXISTS investigation_evidence (
    id SERIAL PRIMARY KEY,
    investigation_id INTEGER REFERENCES investigations(id),
    evidence_record_id INTEGER REFERENCES evidence_records(id),
    title VARCHAR(255) NOT NULL,
    evidence_type VARCHAR(50) DEFAULT 'snapshot',
    uri VARCHAR(500) NOT NULL,
    sha256_hash VARCHAR(64),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

