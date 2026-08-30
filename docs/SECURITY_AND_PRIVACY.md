# Veyra V2.0 Security and Privacy

## Requirements

1. Keep secrets in environment variables or a managed secret store.
2. Validate and rate-limit public inputs.
3. Authenticate and authorize user-owned resources.
4. Protect asynchronous job creation and model-promotion actions.
5. Verify webhook signatures before processing callbacks.
6. Store only necessary location/account data.
7. Log identifiers and outcomes, not secrets or unnecessary raw payloads.
8. Hash/sign model artifacts and verify before loading.
9. Back up configuration, metadata, user data, and model registry state.
10. Test restore and rollback procedures.

## Threats to test

| Threat | Control |
|---|---|
| Secret committed to Git | Secret scanning and `.env` exclusion. |
| Unauthorized saved-location access | Resource-level authorization tests. |
| Malicious job trigger | Authentication, authorization, rate limit, and audit log. |
| Tampered model artifact | Checksum/signature verification. |
| Provider/webhook spoofing | Signature verification and allowlisted sources. |
| Sensitive data in logs | Structured logging review. |
| Denial of service | Request size/rate limits and bounded jobs. |
