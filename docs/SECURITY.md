# Security Design

## 1. Security principles

- deny by default;
- authenticate before privileged operations;
- authorize server-side;
- minimize exposed data;
- keep secrets out of source control;
- audit state-changing actions;
- isolate public and internal components.

## 2. Authentication

Use JWT-based authentication for the application API in the MVP, with access/refresh separation and configurable expiry.

## 3. Roles

Initial conceptual roles:

```text
ADMIN
OPERATOR
INVESTIGATOR
```

Role alone is not always sufficient. Department/resource scope should also be enforced where required.

## 4. Credential handling

VMS credentials must not be returned by camera/VMS read APIs. Store secrets in a secret manager or protected infrastructure configuration rather than plaintext repository files.

## 5. Gateway boundary

```text
Internet
 ↓
API Gateway / NGINX
 ↓
FastAPI
```

Internal worker services should not need to be directly internet-addressable.

## 6. Input validation

Validate all external payloads with explicit schemas. Never trust vendor fields or user-supplied IDs.

## 7. Audit events

Examples:

```text
LOGIN
VMS_CREATED
VMS_UPDATED
CAMERA_CREATED
CAMERA_UPDATED
EVENT_VIEWED
CANDIDATE_VERIFIED
CANDIDATE_REJECTED
INVESTIGATION_CREATED
EVIDENCE_ADDED
USER_ROLE_CHANGED
```

## 8. Sensitive logging

Never log:

- passwords;
- JWTs/access tokens;
- database credentials;
- raw secret keys;
- unnecessary evidence contents.

## 9. Realtime security

WebSocket/realtime clients must be authenticated and must receive only events authorized for their scope.

## 10. TLS

Use HTTPS/WSS at the public boundary.

## 11. Threat areas to test

- token replay/expiry;
- unauthorized department access;
- insecure direct object references;
- malformed vendor payloads;
- event injection;
- duplicate/replayed messages;
- excessive API requests;
- secret exposure through logs or errors.
