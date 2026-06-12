# Sequence Diagram — Quick Action (v3.1 Lockdown)

```
User Click → dashboard_actions.html
  → data-permission check in dashboard_charts.js
    → if denied: console.warn + return
    → if allowed: console.log('AUDIT:', {user, action, timestamp, correlation_id})
  → window.location.href = '/path'
```

No real API calls. Audit is console-only per v3.1 strictures.
