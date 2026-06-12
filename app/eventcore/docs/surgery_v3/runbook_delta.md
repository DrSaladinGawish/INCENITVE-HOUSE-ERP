# Runbook Delta — Surgery v3.1

## Rollback

```powershell
Get-ChildItem -Recurse -Filter "*.backup.*" | ForEach-Object {
  $orig = $_.FullName -replace '\.backup\.\d{8}-\d{6}',''
  Copy-Item -Path $_.FullName -Destination $orig -Force
}
Remove-Item -Recurse -Force templates\partials, static\js\dashboard_charts.js, docs\surgery_v3
```

## Incident Response

| Symptom | Action |
|---------|--------|
| Chart.js not loading | Verify CDN script in base.html |
| KPI cards show 0 | Check `demoKPIs` array in dashboard_charts.js |
| Sidebar not accordion | Verify CSS rules for `.submenu.collapsed`/`.expanded` |
