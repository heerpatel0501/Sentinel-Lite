# Sentinel Lite Backend Engineering Rules

1. **Frontend never talks directly to VMS vendors.**
2. **Vendor-specific code stays inside connectors.**
3. **Core domain code consumes canonical models.**
4. **PostgreSQL is the durable source of truth.**
5. **RabbitMQ handles durable asynchronous work.**
6. **Redis handles cache/realtime/transient workloads.**
7. **Never block an API request on long-running AI/video work.**
8. **All state-changing privileged actions are audited.**
9. **Never expose VMS credentials through ordinary APIs.**
10. **Use UTC internally for timestamps.**
11. **Assume message redelivery can happen.**
12. **Make event ingestion idempotent.**
13. **Keep source identifiers for traceability.**
14. **Do not silently swallow connector/worker failures.**
15. **Add/modify architecture decisions in `DECISIONS.md`.**
16. **Keep the API contract stable once frontend integration begins.**
17. **Do not add a microservice merely to make the architecture diagram larger.**
