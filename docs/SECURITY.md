# Security Requirements

This project handles government CCTV infrastructure data — treat security as a first-class requirement, not a pre-deployment checklist.

## Authentication
- Private routes (camera control, alerts review, watchlist edits) require an authenticated session (JWT or equivalent).
- No endpoint returning department-specific data should be reachable without a valid session.
- Request headers X-User-Role and X-User-Id supply active clearance levels during API interaction.

## Authorization (RBAC)
- Role-based permissions are enforced server-side, never only hidden in the UI:
  - **Admin**: Full read/write access across all departments, audit logs, and hardware registries.
  - **Analyst**: Access to cross-department threat intelligence, natural language plate search, trajectory reconstruction, and authorized vehicle profiles.
  - **Viewer**: Read-only camera registry telemetry. Blocked with **HTTP 403 Forbidden** on sensitive vehicle profiles and watchlist mutations.
- Multi-agency data fencing ensures municipal-level staff cannot access restricted police or state surveillance feeds without authorization.

## Secrets & Credential Protection
- Camera, VMS, ONVIF credentials, and API keys live strictly in .env (gitignored) — never in source code, never sent to the frontend, never logged in plaintext.
- The public Camera API response schema explicitly omits onvif_password to prevent leaking connection secrets over HTTP.
- Passwords and connection secrets are referenced via environment variables or secret vaults in production.

## Database & Privacy Governance (DPDP Act 2023)
- All queries go through SQLAlchemy ORM — no raw string-built SQL (prevents SQL injection).
- Audit every read/write to sensitive tables (watchlist, ehicle_movements, lerts, and /api/vehicle/{plate}/profile) into udit_logs, supporting statutory surveillance accountability and DPDP Act 2023 compliance.
- No CCTV video files or raw video binaries are stored in PostgreSQL or SQLite. Only structured metadata and secure local URI pointers to cryptographic evidence crops are stored.

## Input Validation & Sanitization
- All request bodies and query parameters are validated via strict Pydantic schemas before reaching business logic.
- License plate and text search inputs are sanitized with regex patterns to remove special characters and injection payloads prior to database queries.

## File Uploads (YOLOv8 /detect Endpoint)
- Validate file type (video only: MP4, AVI, MKV — reject arbitrary uploads).
- Enforce a maximum file size (50MB ceiling).
- Never trust client-supplied filenames directly for storage paths; sanitize and use UUIDs or timestamps.

## Repository Hygiene
- No secrets, credentials, or .env files ever committed to git.
- No large binaries (model weights, video captures, database dumps) committed to git history.
