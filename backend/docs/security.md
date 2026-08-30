# Security

## Registered-User-Only Access

The RailMaintain system requires user registration and authentication before any operation is permitted. Anonymous access is not supported.

## Authentication Flow

1. User registers with valid credentials
2. User logs in with registered credentials
3. System validates credentials and creates a session
4. Session token is issued for authenticated requests
5. All subsequent requests must include valid session token

## Session Expiry

Sessions expire after a configurable timeout period. Expired sessions require re-authentication. The system rejects requests with expired tokens.

## Role Permissions

| Role | Permissions |
|---|---|
| `officer` | Submit fault reports, view assigned tasks, report work status |
| `manager` | Approve maintenance blocks, escalate priorities, view all tasks |
| `team_lead` | Report work completion/interruption, view team assignments |
| `system` | Automated scheduling, audit recording, alert generation |

## Department and Section Restrictions

- Officers are scoped to their assigned department and section
- Managers can approve tasks within their jurisdiction
- Team leads operate within their assigned section
- Cross-section operations require explicit authorization

## Manager Approval

Certain operations require manager approval before execution:

- Maintenance block authorization
- Priority escalation to Critical
- Task cancellation
- Emergency task auto-scheduling prevention
- Cross-department bundle approval

The system enforces: **AI never autonomously authorizes railway operations.**

## Audit Protection

Audit events are:

- Append-only (no modification or deletion)
- Protected from non-admin access
- Immutable once recorded
- Idempotent (duplicate detection via idempotency keys)

Unauthorized audit modification attempts are logged and blocked.

## Sensitive-Data Handling

The following data is never stored in audit logs or reports:

- Passwords
- Access tokens
- Refresh tokens
- Secret keys
- Private credentials
- API keys

The `SENSITIVE_FIELDS` set in `audit_logger.py` automatically strips these from any details passed to audit functions.

## Input Validation

All user inputs are validated:

- Required fields are checked
- Status values are restricted to allowed sets
- Resource IDs must be non-empty strings
- Priority values must follow the defined ladder
- Timestamps must be in ISO 8601 format

Invalid input raises `ValueError` with a descriptive message.

## Duplicate-Request Protection

- Complaint IDs are checked for uniqueness before creation
- Audit idempotency keys prevent duplicate event recording
- Dashboard alerts track creation to avoid duplicates

## No Autonomous Railway Control

The system is a decision-support tool. It:

- Recommends schedules (does not execute them)
- Generates alerts (does not send external notifications in MVP)
- Calculates priorities (does not override human judgment)
- Detects conflicts (does not resolve them without approval)

**Every critical decision requires human review and approval.**

## Testing

```bash
# Security tests
pytest backend/tests/test_security.py -q

# Audit tests
pytest backend/tests/test_audit_logger.py -q

# Integration tests
pytest backend/tests/test_integration_audit_notifications.py -q
```
