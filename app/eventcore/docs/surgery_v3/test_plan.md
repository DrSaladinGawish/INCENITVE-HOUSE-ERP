# Test Plan — Surgery v3.1 Lockdown

| # | Test | Method | Expected | Status |
|---|------|--------|----------|--------|
| 1 | KPI cards render 5 values | Visual | 5 cards with demo numbers | MANUAL |
| 2 | Timeline Chart.js renders ≥4 bars | Visual | Horizontal stacked bar with 4 job rows | MANUAL |
| 3 | Donut has 5 segments | Visual | 5 colored segments | MANUAL |
| 4 | Line chart has 13 data points | Visual | 2 lines, 13 labels | MANUAL |
| 5 | Quick Action disabled when lacking permission | Click button w/o perm | Button disabled, console warn | MANUAL |
| 6 | Quick Action logs audit | Click enabled button | `console.log('AUDIT:', ...)` | MANUAL |
| 7 | Sidebar accordion toggles | Click category | Submenu animates open/close | MANUAL |
| 8 | Only one submenu open | Click category B when A open | A closes, B opens | MANUAL |
| 9 | Header height ≤56px | DevTools measure | ≤56px | MANUAL |
| 10 | Footer padding ≤16px | DevTools measure | ≤16px | MANUAL |
| 11 | `console.time('dashboard_paint')` present | DevTools console | Timing logged | MANUAL |
| 12 | Zero console errors | DevTools console | No errors | MANUAL |
| 13 | Backup files exist | File system check | `.backup.*` files present | DONE |
| 14 | No unauthorized files | `Get-ChildItem` compare | Only whitelisted files | DONE |
