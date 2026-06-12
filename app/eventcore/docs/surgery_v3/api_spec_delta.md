# API Spec Delta — Surgery v3.1

## All API calls are deferred (demo data only)
Use `{# TODO: Wire to /api/v1/... #}` comments for integration points.

## Planned Endpoint Signatures

### `GET /api/v1/dashboard/kpi/snapshots`
```json
{
  "total_jobs": 124,
  "active_jobs": 12,
  "completed_this_q": 47,
  "pending_approval": 8,
  "total_revenue_qtd": 1240000.00
}
```

### `GET /api/v1/dashboard/jobs/timeline?days=30`
```json
[
  {
    "id": "EV-1147",
    "job_code": "25.C0001.101",
    "event_name": "Al-Futtaim Gala",
    "stage": "Execution",
    "start_date": "2026-05-28",
    "end_date": "2026-06-02",
    "percent_complete": 65
  }
]
```

### `POST /api/v1/dashboard/audit/log`
```json
{
  "user_id": "u-admin-001",
  "action": "click:new_event",
  "correlation_id": "uuid"
}
```

### Headers (future)
- `Authorization: Bearer <JWT>` per Spec §4.1
- `X-Correlation-ID: <uuid>` per Spec §9
- `Idempotency-Key: <uuid>` for POST per Spec §4.1
