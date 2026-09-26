# Sentinel Lite Backend Documentation

This directory is the engineering source of truth for the Sentinel Lite backend and middleware.

## Project
- **Product:** Sentinel Lite
- **Architecture:** Model 3 — VMS Federation & Middleware Layer
- **Primary role covered here:** Backend + Middleware

## Documentation map
| File | Purpose |
|---|---|
| PRD.md | What is being built and why |
| SRS.md | Detailed functional/non-functional requirements |
| ARCHITECTURE.md | System architecture and service boundaries |
| DESIGN.md | Backend code/design conventions |
| API_CONTRACT.md | REST/WebSocket/API contracts |
| DATABASE.md | PostgreSQL data model and persistence rules |
| VMS_FEDERATION.md | Connector and federation design |
| EVENT_PIPELINE.md | Event ingestion, RabbitMQ, retries, delivery |
| CORRELATION.md | Cross-camera correlation and candidate events |
| AI_INTEGRATION.md | AI service contract and orchestration |
| INVESTIGATION.md | Investigation, evidence and verification workflow |
| SECURITY.md | Authentication, RBAC, secrets and audit |
| DEPLOYMENT.md | Docker + AWS deployment architecture |
| TEST_PLAN.md | Test strategy and acceptance tests |
| DECISIONS.md | Architecture decisions and rationale |
| RULES.md | Non-negotiable engineering rules |
| TASKS.md | Implementation backlog and milestones |
| RUNBOOK.md | Operations and troubleshooting |
| MEMORY.md | Durable project context for future AI/dev sessions |

## Source baseline
The project requirements are derived from `Sentinel_Lite_Project_Progress(1).md`. It defines Model 3 as a vendor-neutral federation layer over existing VMS systems, with canonical camera/event models, unified APIs, RabbitMQ-based event processing, correlation, AI-assisted analytics, GIS and investigation workflows.

## Scope note
These documents deliberately distinguish **requirements already defined by the project** from **engineering decisions proposed for implementation**. Proposed decisions can be changed, but changes should be recorded in `DECISIONS.md`.
