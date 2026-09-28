# Development Rules

## General
- **Backend Standards**: Python 3.10+ and FastAPI conventions (strict type hints, Pydantic v2 schemas for all request/response models).
- **Frontend Standards**: React 18 functional components and hooks only — no legacy class components.
- **Component Reusability**: Reuse existing core UI components (MapComponent, VideoModal, AlertsSidebar, InvestigatorModal, StatsBar) rather than creating duplicate widgets.
- **Function Simplicity**: Keep functions small, modular, and single-purpose.
- **Scope Discipline**: Do not modify unrelated files in the same pull request or commit.

## Before Coding
- Review PRD.md, ARCHITECTURE.md, and this file prior to beginning any implementation.
- Check MEMORY.md for current progress to avoid reimplementing existing features.
- Reuse existing adapters/endpoints where possible — check ackend/vms_adapters.py before writing a new integration from scratch.
- For non-trivial architectural changes, write a brief plan before modifying source files.

## UI / UX
- Adhere to DESIGN.md regarding color schemes, spacing, typography, and dark mode themes.
- **Loading State**: Every asynchronous view or data fetch must render a clear loading indicator.
- **Empty State**: Every list, feed, or modal panel must provide an informative empty state.
- **Error State**: Every network request failure must present a user-friendly error message.
- Ensure layout responsiveness across 375px (mobile), 768px (tablet), and 1440px+ (desktop/command center) displays.

## Security & Secrets
- Never commit .env or real operational credentials to git — commit only .env.example with placeholder values.
- Passwords and connection secrets (e.g. onvif_password) must never be transmitted to the frontend or printed in plain text logs.
- Enforce server-side authorization and schema validation on all incoming requests.
- Validate all file uploads by MIME type, maximum file size, and sanitized file paths before processing.

## Testing & Verification
- Add automated test cases for any new endpoint, adapter, or model extension.
- Execute python test_e2e_pipeline.py after backend modifications and verify all 8 test stages pass before committing.
- Run 
pm run build in rontend/ to confirm zero bundler or JSX errors.

## Git & Repository Hygiene
- Commit frequently with small, focused changes.
- Write descriptive commit messages following the Conventional Commits specification (e.g. eat: add ONVIF adapter, ix: SQLite column migration).
- Never commit large binaries (weights files, CCTV video recordings, database dumps) — add them to .gitignore.
