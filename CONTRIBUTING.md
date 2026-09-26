# Contributing to Sentinel-Lite

Thank you for your interest in contributing to **Sentinel-Lite**! This project is a vendor-agnostic surveillance command platform and CCTV federation gateway designed for multi-agency smart city and traffic monitoring.

Please review our authoritative guidelines in the `docs/` folder before submitting code:
- **`docs/ARCHITECTURE.md`**: Overall system architecture, data flow, and table schema.
- **`docs/RULES.md`**: Core development rules, coding standards, and security constraints.
- **`docs/SECURITY.md`**: RBAC permissions, credential protection, and statutory compliance (DPDP Act 2023).
- **`docs/DESIGN.md`**: UI/UX design tokens, dark mode guidelines, and component specifications.
- **`docs/TEST_PLAN.md`**: Verification suites and testing expectations.

---

## 1. Development Environment Setup

### Backend (Python 3.10+)
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv env
   # Windows:
   .\env\Scripts\activate
   # Linux/macOS:
   source env/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Copy `.env.example` to `.env` (never commit `.env`):
   ```bash
   cp backend/.env.example backend/.env
   ```

### Frontend (React 18 / Vite)
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

### Docker Compose Multi-Service Setup
To run all services (PostgreSQL PostGIS, FastAPI backend, React frontend, MediaMTX relay):
```bash
docker compose up --build
```

---

## 2. Contribution Guidelines

### Branching & Commits
- Use feature branches: `feature/my-feature-name` or `fix/my-bug-fix`.
- Write descriptive commit messages using the [Conventional Commits](https://www.conventionalcommits.org/) specification:
  - `feat: add new vendor VMS adapter`
  - `fix: resolve stream reconnect backoff ceiling`
  - `docs: update API ingestion specification`
  - `test: add unit test for license plate normalizer`

### Coding Standards
- **Backend**: Strict type hints, FastAPI routes, and Pydantic v2 schemas for all requests and responses. Follow PEP 8.
- **Frontend**: React 18 functional components and hooks only. Follow design tokens defined in `docs/DESIGN.md` (high-contrast dark mode `#0B0F19`, `#111827`, `#1F2937`).
- **Security**: Never commit real credentials, API tokens, or `.env` files. Public schemas must omit sensitive connection parameters (such as `onvif_password`).

---

## 3. Testing & Verification

Before submitting any Pull Request:
1. Run the end-to-end automated verification suite:
   ```bash
   python test_e2e_pipeline.py
   ```
   All tests (`[TEST 1/8]` through `[TEST 8/8]`) must pass or report expected network constraints.
2. Build the frontend to verify there are no bundling or syntax errors:
   ```bash
   cd frontend && npm run build
   ```
3. Verify Docker Compose configuration:
   ```bash
   docker compose config
   ```

---

## 4. Code of Conduct

Maintain professional, constructive, and respectful communication in all issues, discussions, and pull requests.
