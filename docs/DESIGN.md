# UI/UX Design System Specification

## 1. Design Philosophy
Sentinel-Lite is designed for **mission-critical government command centers** and traffic control rooms. The interface emphasizes:
- **High Contrast Dark Mode**: Reduces eye strain during 24/7 monitoring shifts.
- **Low Cognitive Load**: Uses color-coded visual hierarchy to distinguish between administrative jurisdictions at a glance.
- **Information Density**: Balances rich geographic telemetry with instant access to investigative search and evidence forensics.

---

## 2. Design Tokens & Color Palette

### Base Surfaces (Dark Theme)
| Token | Hex Value | Usage |
|-------|-----------|-------|
| g-primary | #0B0F19 | Application backdrop, map underlay |
| g-surface | #111827 | Header navigation, sidebar panels, modals |
| g-elevated | #1F2937 | Cards, input fields, popups |
| order-subtle | #374151 | Dividers, card borders, tab outlines |

### Department Jurisdictional Accents
| Department | Primary Color | Hex Value | Badge Style |
|------------|---------------|-----------|-------------|
| **Police** | Blue | #3B82F6 | g-blue-500/10 text-blue-400 border-blue-500/20 |
| **RTO** | Orange | #F97316 | g-orange-500/10 text-orange-400 border-orange-500/20 |
| **GSRTC** | Green | #10B981 | g-emerald-500/10 text-emerald-400 border-emerald-500/20 |
| **Municipal**| Purple | #8B5CF6 | g-purple-500/10 text-purple-400 border-purple-500/20 |
| **Panchayat**| Pink | #EC4899 | g-pink-500/10 text-pink-400 border-pink-500/20 |

### Telemetry & Alert Indicators
| Status | Hex Value | Meaning |
|--------|-----------|---------|
| **Online / Active** | #10B981 | Live stream operating, normal FPS/PTS |
| **Reconnecting** | #F59E0B | Exponential backoff retry in progress |
| **Offline / Alert** | #EF4444 | Camera unreachable, active watchlist violation |

---

## 3. Typography & Numerical Formatting
- **Primary Font**: Inter, system-ui, -apple-system, sans-serif
- **Monospace Font**: JetBrains Mono, Menlo, monospace (used for GPS coordinates, plate numbers, PTS timestamps, and SHA-256 hashes).
- **Tabular Figures**: Numeric badges and telemetry values utilize ont-variant-numeric: tabular-nums to prevent horizontal jitter during real-time data streaming.

---

## 4. Core UI Components

### 4.1 Top Navigation & Investigator Search Bar
- **Natural Language Input**: Styled pill input with magnifying glass icon:  
  Search plate e.g. Find GJ01-AB-1234...
- **Stats Bar Telemetry**:
  - Total Monitored Cameras
  - State-Wide Uptime Percentage
  - Connected Department Count

### 4.2 Geospatial Map Component (MapComponent.jsx)
- Built with **MapLibre GL JS** on open vector map tiles.
- Custom DOM markers colored by departmental jurisdiction.
- Interactive click-through: Clicking any camera pin opens a quick telemetry popup with location coordinates, resolution, VMS vendor, and a **'View Live Feed'** action button.

### 4.3 Real-Time Alerts Sidebar (AlertsSidebar.jsx)
- Fixed-width collapsible sidebar docked to the right viewport.
- Real-time alert cards classified by threat category:
  - 🚨 cross_department: Target vehicle tracked across 2+ agencies.
  - ⚠️ watchlist_match: Stolen or wanted plate flagged in state database.
  - ⚡ speeding: Speed violation in municipal smart city corridor.
- Clicking any alert card triggers the full **Investigator Dossier Modal** for that plate.

### 4.4 Investigator Dossier Modal (InvestigatorModal.jsx)
Comprehensive forensic investigation modal structured into 4 tabbed/vertical sections:
1. **Telemetry Header**: Large normalized plate banner (GJ01-AB-1234), active watchlist status badge (STOLEN / WANTED / CLEAN), and total inter-agency sightings.
2. **Chronological Journey Trail**: Step-card timeline detailing the exact chronological traversal:
   - Sighting timestamp (PTS-synchronized)
   - Department badge and Camera identifier
   - Geographic coordinates and ward
3. **Forensic Evidence Snapshot Gallery**: High-resolution thumbnail crops of the detected vehicle and plate bounding box. Clicking an image expands the full-size view with cryptographic SHA-256 verification hash.
4. **Authorized Vehicle Registration Profile**: Guarded by RBAC (Analyst or Admin clearance required). Unlocks synthetic VAHAN attributes (Maker/Model, Vehicle Class, Registration Date, Issuing RTO, masked contact).

### 4.5 Live Video Streaming Modal (VideoModal.jsx)
- Universal video player using **hls.js**.
- Automatically binds to HLS streams provided by MediaMTX or simulated endpoints.
- Displays live latency, stream resolution, and audio/video codec indicators.
