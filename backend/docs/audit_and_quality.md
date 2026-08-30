# Audit and Quality Assurance

## Audit Event Schema

Every audit event contains these fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `log_id` | string | Yes | Unique identifier (e.g., `LOG-20260826123000...`) |
| `user_id` | string | Yes | ID of the user who triggered the event |
| `role` | string | Yes | Role of the user (`officer`, `manager`, `system`) |
| `action` | string | Yes | Action performed (see allowed actions below) |
| `resource_type` | string | Yes | Type of resource affected |
| `resource_id` |string | Yes | ID of the resource affected |
| `timestamp` | string | Yes | ISO 8601 UTC timestamp |
| `status` | string | Yes | `SUCCESS`, `FAILED`, or `BLOCKED` |
| `details` | any | No | Additional context (sensitive fields stripped) |

## Allowed Audit Actions

```
TASK_CREATED
TASK_APPROVED
TASK_REJECTED
TASK_COMPLETED
TASK_REQUEUED
WORK_INTERRUPTED
PRIORITY_ESCALATED
SCHEDULE_RECOMMENDED
SCHEDULE_APPROVED
RESOURCE_FAILURE
COMplaint_CLASSIFIED
APPROVAL_ATTEMPTED
BUNDLE_INVALIDATED
TEAM_REASSIGNED
```

## Workflow-Status History

Every task status change is recorded with:

- Previous status
- New status
- Timestamp
- Actor (user or system)
- Reason

This provides full traceability from fault report to completion.

## Dashboard-Alert Behavior

Dashboard alerts are the MVP notification mechanism.

Alert types:

```
CRITICAL_TASK
EMERGENCY_TASK
HUMAN_REVIEW_REQUIRED
OVERDUE_MAINTENANCE
UPCOMING_MAINTENANCE
WORK_INTERRUPTED
TASK_REQUEUED
RESOURCE_UNAVAILABLE
SCHEDULING_APPROVAL_REQUIRED
BUNDLE_INVALIDATED
TEAM_REASSIGNED
FAILED_SYNC
INCOMPLETE_WORK
MATERIALS_UNAVAILABLE
EMERGENCY
```

Alerts are:

- Created deterministically from system events
- Stored in memory (MVP) or database (production)
- Filterable by user and read status
- Markable as read

## Report Structures

### Work Completion Report

```json
{
  "report_id": "RPT-COMP-001",
  "report_type": "WORK_COMPLETION",
  "task_id": "T-001",
  "status": "Completed",
  "completion_percentage": 100,
  "inspection_result": "Completed",
  "materials_status": "Available",
  "safety_status": "Verified",
  "created_at": "2026-08-26T23:40:00+00:00"
}
```

### Work Interruption Report

```json
{
  "report_id": "RPT-INT-001",
  "report_type": "WORK_INTERRUPTION",
  "task_id": "T-001",
  "status": "Interrupted",
  "reason": "Required equipment unavailable",
  "remaining_work_minutes": 60,
  "priority_recalculated": true,
  "created_at": "2026-08-26T23:45:00+00:00"
}
```

### Task Requeue Report

```json
{
  "report_id": "RPT-REQUEUE-001",
  "report_type": "TASK_REQUEUE",
  "task_id": "T-001",
  "status": "Requeued",
  "reason": "Equipment unavailable",
  "previous_status": "Interrupted",
  "new_priority": "High",
  "created_at": "2026-08-26T23:50:00+00:00"
}
```

### Scheduling Block Report

```json
{
  "report_id": "RPT-BLOCK-001",
  "report_type": "SCHEDULING_BLOCK",
  "block_id": "B-301",
  "section_id": "S-02",
  "tasks": ["T-101", "T-104"],
  "train_conflict_check": "PASSED",
  "team_available": true,
  "status": "Recommended",
  "created_at": "2026-08-26T23:55:00+00:00"
}
```

### Resource Failure Report

```json
{
  "report_id": "RPT-RESFAIL-001",
  "report_type": "RESOURCE_FAILURE",
  "resource_id": "EQ-07",
  "resource_type": "Inspection Equipment",
  "failure_reason": "Equipment broken",
  "status": "Failed",
  "created_at": "2026-08-26T23:58:00+00:00"
}
```

## Append-Only Policy

Audit events are append-only:

- Events cannot be modified after creation
- Events cannot be deleted through normal operations
- The `AuditRepository` enforces this invariant
- Only test-mode reset is available

## Idempotency Policy

Each audit event may carry an `idempotency_key`:

- If a key is provided, duplicate events with the same key are rejected
- This prevents double-recording of the same logical event
- Keys are checked at save time

## Sensitive-Data Policy

These fields are automatically stripped from audit event `details`:

```
password, access_token, refresh_token, secret,
secret_key, private_key, api_key, credential,
token, passphrase
```

This applies regardless of how details are provided (dict, list, or nested structure).

## Failure Behavior

| Scenario | Behavior |
|---|---|
| Missing required field | `ValueError` raised |
| Invalid status value | `ValueError` raised |
| Duplicate idempotency key | `ValueError` raised |
| Repository unavailable | Event returned without persistence (backward-compatible) |
| Sensitive data in details | Automatically stripped |

## Testing Commands

```bash
# Run all tests
pytest backend/tests -q

# Run audit tests only
pytest backend/tests/test_audit_logger.py -q

# Run notification tests only
pytest backend/tests/test_notification_rules.py backend/tests/test_notification_service.py -q

# Run report tests only
pytest backend/tests/test_reports.py -q

# Run integration tests only
pytest backend/tests/test_integration_audit_notifications.py -q

# Syntax validation
python -m compileall backend/app backend/tests
```
