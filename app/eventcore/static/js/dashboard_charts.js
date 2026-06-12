/**
 * dashboard_charts.js — Chart.js dashboard widgets
 * SURGERY v4.2 — Wired to /api/v1/... endpoints with demo fallback
 */

console.time('dashboard_paint')

/* ===================================================================
 * 0. API Fetch Utility
 * =================================================================== */
var API_BASE = '/api/v1/dashboard'

async function apiFetch(endpoint, options) {
  options = options || {}
  var token = window.accessToken || localStorage.getItem('jwt') || ''
  var correlationId = crypto.randomUUID()

  var defaults = {
    headers: {
      'Content-Type': 'application/json',
      'X-Correlation-ID': correlationId,
    },
  }
  if (token) defaults.headers['Authorization'] = 'Bearer ' + token

  try {
    var res = await fetch(API_BASE + endpoint, Object.assign({}, defaults, options))
    if (res.status === 401) { console.warn('[API] 401 — redirecting'); return null }
    if (!res.ok) { console.error('[API] ' + endpoint + ' failed:', res.status); return null }
    return await res.json()
  } catch (err) {
    console.error('[API] Network error on ' + endpoint + ':', err)
    return null
  }
}

function hasData(d) {
  return d !== null && d !== undefined && typeof d === 'object' && Object.keys(d).length > 0
}

function useDemoMode() {
  return new URLSearchParams(window.location.search).has('demo')
}

/* ===================================================================
 * 1. RBAC Simulation
 * =================================================================== */
window.userPermissions = window.userPermissions || [
  'event:create', 'staff:assign', 'invoice:create', 'report:read',
]

function hasPermission(perm) {
  return window.userPermissions.indexOf(perm) !== -1
}

/* ===================================================================
 * 2. Quick Actions — Audit logging + RBAC gating
 * =================================================================== */
async function handleQuickAction(btn) {
  var action = btn.getAttribute('data-action')
  var required = btn.getAttribute('data-permission')

  if (required && !hasPermission(required)) {
    console.warn('[RBAC] Denied: ' + action + ' requires ' + required)
    return
  }

  await apiFetch('/audit/log', {
    method: 'POST',
    body: JSON.stringify({
      action: 'click:' + action,
      timestamp: new Date().toISOString(),
      correlation_id: crypto.randomUUID(),
    }),
  })

  console.log('[AUDIT]', action)

  switch (action) {
    case 'new-event': window.location.href = '/events/new'; break
    case 'assign-staff': window.location.href = '/operation/task/new'; break
    case 'gen-invoice': window.location.href = '/sales/invoice/new'; break
    case 'run-report': window.location.href = '/analysis/dashboard'; break
  }
}

/* ===================================================================
 * 3. KPI Cards — Wired to /kpis
 * =================================================================== */
async function loadKPIs() {
  var data = useDemoMode() ? DEMO_KPIS : await apiFetch('/kpis')
  var kpis = hasData(data) ? data : DEMO_KPIS

  var el = {
    total: document.getElementById('kpi-total'),
    active: document.getElementById('kpi-active'),
    completed: document.getElementById('kpi-completed'),
    pending: document.getElementById('kpi-pending'),
    revenue: document.getElementById('kpi-revenue'),
  }

  if (el.total)     el.total.textContent     = kpis.total_jobs ?? '—'
  if (el.active)    el.active.textContent    = kpis.active_jobs ?? '—'
  if (el.completed) el.completed.textContent = kpis.completed_q ?? '—'
  if (el.pending)   el.pending.textContent   = kpis.pending_approval ?? '—'
  if (el.revenue)   el.revenue.textContent   = '€' + (kpis.revenue_q / 100).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})
}

/* ===================================================================
 * 4. Timeline Gantt — Wired to /jobs/timeline
 * =================================================================== */
async function loadTimeline() {
  var ctx = document.getElementById('timelineChart')
  if (!ctx) return

  var data = useDemoMode() ? DEMO_TIMELINE : await apiFetch('/jobs/timeline')
  var jobs = data || DEMO_TIMELINE

  var labels = []
  var now = new Date()
  for (var i = 0; i < 30; i++) {
    var d = new Date(now.getTime() + i * 86400000)
    labels.push((d.getMonth() + 1) + '/' + d.getDate())
  }

  var datasets = jobs.map(function (job) {
    var arr = Array(30).fill(0)
    var startIdx = dayIndex(job.start, now)
    var endIdx = dayIndex(job.end, now)
    for (var i = startIdx; i <= endIdx && i < 30; i++) {
      if (i >= 0) arr[i] = 1
    }
    return {
      label: job.name,
      data: arr,
      backgroundColor: stageColor(job.stage || 'planning'),
      borderWidth: 1,
      borderColor: '#1a2332',
      barPercentage: 0.4,
    }
  })

  new Chart(ctx, {
    type: 'bar',
    data: { labels: labels, datasets: datasets },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { stacked: true, display: false },
        y: { stacked: true, ticks: { font: { size: 9 }, color: '#8A8A8A' } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1a2332',
          titleFont: { size: 11 },
          bodyFont: { size: 10 },
          callbacks: {
            title: function (items) {
              var job = jobs[items[0].datasetIndex]
              return job ? job.name : ''
            },
            label: function (ctx) {
              return 'Day ' + (ctx.dataIndex + 1) + ': Active'
            },
          },
        },
      },
    },
  })
}

function dayIndex(dateStr, refDate) {
  var d = new Date(dateStr)
  return Math.floor((d.getTime() - refDate.getTime()) / 86400000)
}

function stageColor(stage) {
  var map = {
    planning: '#4a5568',
    design: '#3b82f6',
    procurement: '#f59e0b',
    executing: '#10b981',
    execution: '#10b981',
    invoicing: '#c9a227',
    wrap: '#c9a227',
  }
  return map[stage.toLowerCase()] || '#8A8A8A'
}

/* ===================================================================
 * 5. Status Donut — Wired to /jobs/active
 * =================================================================== */
async function loadStatus() {
  var data = useDemoMode() ? DEMO_ACTIVE : await apiFetch('/jobs/active')
  var jobs = data || DEMO_ACTIVE

  var labelMap = {
    planning: 'Planning',
    design: 'Design',
    procurement: 'Procurement',
    executing: 'Execution',
    execution: 'Execution',
    invoicing: 'Wrap',
    wrap: 'Wrap',
  }
  var colorMap = {
    planning: '#4a5568',
    design: '#3b82f6',
    procurement: '#f59e0b',
    execution: '#10b981',
    wrap: '#c9a227',
  }

  var counts = {}
  if (jobs.length && jobs[0].count != null) {
    jobs.forEach(function (j) {
      var label = labelMap[j.status] || j.status
      counts[label] = (counts[label] || 0) + j.count
    })
  } else {
    jobs.forEach(function (j) {
      var label = labelMap[j.stage] || j.stage || 'Unknown'
      counts[label] = (counts[label] || 0) + 1
    })
  }

  var labels = Object.keys(counts)
  var values = labels.map(function (l) { return counts[l] })
  var colors = labels.map(function (l) { return colorMap[l.toLowerCase()] || '#8A8A8A' })

  var centerEl = document.getElementById('donut-center')
  if (centerEl) {
    var total = values.reduce(function (a, b) { return a + b }, 0)
    centerEl.textContent = total + ' Active'
  }

  var ctx = document.getElementById('statusDonut')
  if (!ctx) return

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: '#1a2332' },
      },
    },
  })
}

/* ===================================================================
 * 6. Quarter Line — Wired to /jobs/completed/qoq
 * =================================================================== */
async function loadQuarter() {
  var data = useDemoMode() ? DEMO_QOQ : await apiFetch('/jobs/completed/qoq')
  var q = data || DEMO_QOQ

  var latest = q[q.length - 1]

  var bn = document.querySelector('.ih-big-number')
  if (bn && latest) bn.textContent = latest.job_count + ' Jobs Completed'

  var sub = document.querySelector('.ih-sub-line')
  if (sub && latest) {
    sub.innerHTML = 'EGP ' + (latest.revenue / 1e6).toFixed(2) + 'M revenue &middot; ' + latest.margin_pct + '% margin'
  }

  var badge = document.querySelector('.ih-delta-badge')
  if (badge && q.length >= 2) {
    var prev = q[q.length - 2]
    var diff = latest.job_count - prev.job_count
    badge.textContent = (diff >= 0 ? '\u25B2 ' : '\u25BC ') + Math.abs(diff) + ' vs prior Q'
  }

  var ctx = document.getElementById('quarterChart')
  if (!ctx) return

  var weekLabels = []
  for (var w = 1; w <= 13; w++) weekLabels.push('W' + w)

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: weekLabels,
      datasets: [
        {
          label: 'Actual',
          data: DEMO_WEEKLY_ACTUAL,
          borderColor: '#1B2A4A',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 2,
          pointBackgroundColor: '#1B2A4A',
          tension: 0.3,
        },
        {
          label: 'Target',
          data: DEMO_WEEKLY_TARGET,
          borderColor: '#C9A84C',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [6, 3],
          pointRadius: 0,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { font: { size: 9 }, color: '#8A8A8A' } },
        y: {
          ticks: { font: { size: 9 }, color: '#8A8A8A', callback: function (v) { return v + ' jobs' } },
          beginAtZero: true,
        },
      },
      plugins: {
        legend: { labels: { font: { size: 10 }, color: '#4a5568' } },
        tooltip: { backgroundColor: '#1a2332' },
      },
    },
  })
}

/* ===================================================================
 * 7. DEMO FALLBACK DATA — Used when API is unreachable
 * =================================================================== */

var DEMO_KPIS = {
  tenant_id: 'demo',
  total_jobs: 124,
  active_jobs: 12,
  completed_q: 47,
  pending_approval: 8,
  revenue_q: 12400000,
  on_time_pct: 94.0,
  refreshed_at: new Date().toISOString()
}

var DEMO_TIMELINE = [
  { job_id: 'J001', name: 'Al-Futtaim Gala',  start: getDateStr(5),  end: getDateStr(22), stage: 'execution' },
  { job_id: 'J002', name: 'Finance Gala',      start: getDateStr(7),  end: getDateStr(27), stage: 'procurement' },
  { job_id: 'J003', name: 'Tech Conference',   start: getDateStr(12), end: getDateStr(29), stage: 'planning' },
  { job_id: 'J004', name: 'Auto Expo',         start: getDateStr(3),  end: getDateStr(24), stage: 'design' },
]

var DEMO_ACTIVE = [
  { status: 'planning', count: 4 },
  { status: 'design', count: 3 },
  { status: 'procurement', count: 2 },
  { status: 'executing', count: 2 },
  { status: 'invoicing', count: 1 },
]

var DEMO_QOQ = [
  { quarter: '2025 Q1', revenue: 980000, margin_pct: 24.5, job_count: 18 },
  { quarter: '2025 Q2', revenue: 1120000, margin_pct: 26.1, job_count: 22 },
  { quarter: '2025 Q3', revenue: 1050000, margin_pct: 25.3, job_count: 20 },
  { quarter: '2025 Q4', revenue: 1210000, margin_pct: 27.8, job_count: 25 },
  { quarter: '2026 Q1', revenue: 1140000, margin_pct: 26.5, job_count: 23 },
]

var DEMO_WEEKLY_ACTUAL = [3, 5, 4, 6, 7, 5, 8, 6, 7, 9, 8, 7, 10]
var DEMO_WEEKLY_TARGET = [4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10]

function getDateStr(offsetDays) {
  var d = new Date(Date.now() + offsetDays * 86400000)
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
}

/* ===================================================================
 * 8. DOMContentLoaded — Init all widgets
 * =================================================================== */
document.addEventListener('DOMContentLoaded', async function () {
  document.querySelectorAll('[data-permission]').forEach(function (btn) {
    var perm = btn.getAttribute('data-permission')
    if (!hasPermission(perm)) {
      btn.disabled = true
      btn.title = 'Requires permission: ' + perm
      btn.classList.add('ih-disabled')
    }
  })

  await loadKPIs()
  await loadTimeline()
  await loadStatus()
  await loadQuarter()

  console.timeEnd('dashboard_paint')
})
