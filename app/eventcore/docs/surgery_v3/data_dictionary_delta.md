# Data Dictionary Delta — Surgery v3.1

## New UI Fields

| Field | Type | Source Table | Spec § | Notes |
|-------|------|-------------|--------|-------|
| `kpi_card_order` | integer | `kpi_snapshots` (MV) | §5.1 / §7 | Display order for KPI cards |
| `timeline_date_range` | daterange | `jobs` computed | §5.1 | Gantt date window |
| `fsm_stage_display` | varchar(20) | `jobs.status` | §2.1 | FSM: Draft→Submitted→Approved→Posted→Reversed |

## Partial Template Mapping

| Partial | Data Source | Chart.js Canvas ID |
|---------|-------------|-------------------|
| `dashboard_kpi.html` | kpi_snapshots MV | (no chart, static values) |
| `dashboard_timeline.html` | `/api/v1/jobs/timeline` | `timelineChart` |
| `dashboard_status.html` | `/api/v1/jobs/active` | `statusDonut` |
| `dashboard_quarter.html` | `/api/v1/jobs/completed/qoq` | `quarterChart` |
| `dashboard_actions.html` | (client-side RBAC) | (no chart) |
