from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_index():
    return DASHBOARD_HTML


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>INCENTIVE HOUSE ERP</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
:root {
  --bg: #231F20; --surface: #2a2527; --surface2: #333; --accent: #324B7F;
  --accent2: #4a6aaa; --text: #e0e0e0; --muted: #888; --green: #4caf50;
  --red: #e53935; --orange: #ff9800; --border: #3a3537;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
a { color: var(--accent2); text-decoration: none; }

/* Login */
#login-screen { display:flex; align-items:center; justify-content:center; min-height:100vh; background: linear-gradient(135deg,#231F20 0%,#1a1819 100%); }
#login-screen .card { background:var(--surface); padding:40px; border-radius:12px; width:380px; border:1px solid var(--border); }
#login-screen h1 { font-size:22px; margin-bottom:4px; }
#login-screen p { color:var(--muted); font-size:13px; margin-bottom:24px; }
#login-screen input { width:100%; padding:12px; margin-bottom:12px; border:1px solid var(--border); border-radius:6px; background:var(--surface2); color:var(--text); font-size:14px; }
#login-screen button { width:100%; padding:12px; background:var(--accent); color:#fff; border:none; border-radius:6px; font-size:15px; cursor:pointer; }
#login-screen button:hover { background:var(--accent2); }
#login-err { color:var(--red); font-size:13px; margin-top:8px; display:none; }

/* App */
#app { display:none; }
#app-header { background:var(--surface); padding:14px 24px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--border); position:sticky; top:0; z-index:100; }
#app-header h1 { font-size:16px; font-weight:600; }
#app-header .user-info { font-size:13px; color:var(--muted); }
#app-header .user-info span { color:var(--text); font-weight:500; }
#app-header .logout-btn { background:var(--surface2); border:1px solid var(--border); color:var(--text); padding:6px 14px; border-radius:4px; cursor:pointer; font-size:12px; margin-left:12px; }
#app-header .logout-btn:hover { background:var(--red); border-color:var(--red); }

#main { display:flex; }
#sidebar { width:220px; background:var(--surface); min-height:calc(100vh - 54px); padding:16px 0; border-right:1px solid var(--border); flex-shrink:0; }
#sidebar a { display:block; padding:10px 20px; font-size:13px; color:var(--muted); border-left:3px solid transparent; transition:all .15s; }
#sidebar a:hover, #sidebar a.active { color:var(--text); background:rgba(255,255,255,0.04); border-left-color:var(--accent); }
#sidebar a.active { color:#fff; font-weight:500; }

#content { flex:1; padding:24px; overflow-x:hidden; }

/* KPI Grid */
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:24px; }
.kpi-card { background:var(--surface); border-radius:8px; padding:18px; border:1px solid var(--border); }
.kpi-card .kpi-label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; }
.kpi-card .kpi-value { font-size:26px; font-weight:700; margin:4px 0 2px; }
.kpi-card .kpi-sub { font-size:12px; color:var(--muted); }

/* Cards */
.card { background:var(--surface); border-radius:8px; padding:20px; border:1px solid var(--border); margin-bottom:20px; }
.card h3 { font-size:14px; margin-bottom:16px; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; }

/* Table */
table { width:100%; border-collapse:collapse; font-size:13px; }
th { text-align:left; padding:10px 8px; color:var(--muted); font-weight:400; border-bottom:1px solid var(--border); font-size:11px; text-transform:uppercase; }
td { padding:8px; border-bottom:1px solid rgba(255,255,255,0.04); }
.status { display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; }
.status-ok { background:rgba(76,175,80,0.15); color:var(--green); }
.status-warn { background:rgba(255,152,0,0.15); color:var(--orange); }
.status-err { background:rgba(229,57,53,0.15); color:var(--red); }

/* Section */
.section-title { font-size:18px; font-weight:600; margin-bottom:16px; display:flex; align-items:center; gap:8px; }
.tab-bar { display:flex; gap:4px; margin-bottom:20px; }
.tab-bar button { padding:8px 16px; background:var(--surface); border:1px solid var(--border); color:var(--muted); border-radius:4px; cursor:pointer; font-size:12px; }
.tab-bar button.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.tab-bar button:hover:not(.active) { color:var(--text); }

/* Two col */
.col2 { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
@media(max-width:900px) { .col2 { grid-template-columns:1fr; } }
</style>
</head>
<body>

<!-- LOGIN -->
<div id="login-screen">
  <div class="card">
    <h1>🏢 IncentiveHouse</h1>
    <p>ERP v2.2.2 — Sign in</p>
    <input type="text" id="login-user" placeholder="Username" value="admin">
    <input type="password" id="login-pass" placeholder="Password" value="admin">
    <button onclick="login()">Sign In</button>
    <div id="login-err"></div>
  </div>
</div>

<!-- APP -->
<div id="app">
  <div id="app-header">
    <h1>🏢 IncentiveHouse ERP</h1>
    <div class="user-info">
      <span id="user-display">—</span> · <span id="user-role">—</span>
      <button class="logout-btn" onclick="logout()">Logout</button>
    </div>
  </div>
  <div id="main">
    <div id="sidebar">
      <a class="active" onclick="showSection('dashboard')">📊 Dashboard</a>
      <a onclick="showSection('pipeline')">🔄 Pipeline</a>
      <a onclick="showSection('coa')">📋 Chart of Accounts</a>
      <a onclick="showSection('pettycash')">💰 Petty Cash</a>
      <a onclick="showSection('cheques')">📝 Cheques</a>
      <a onclick="showSection('wht')">🧾 WHT Records</a>
      <a onclick="showSection('currency')">💱 Currency</a>
      <a onclick="showSection('vendor')">⭐ Vendor Rating</a>
      <a onclick="showSection('health')">🔍 System Health</a>
    </div>
    <div id="content">
      <div id="section-dashboard"></div>
      <div id="section-pipeline" style="display:none"></div>
      <div id="section-coa" style="display:none"></div>
      <div id="section-pettycash" style="display:none"></div>
      <div id="section-cheques" style="display:none"></div>
      <div id="section-wht" style="display:none"></div>
      <div id="section-currency" style="display:none"></div>
      <div id="section-vendor" style="display:none"></div>
      <div id="section-health" style="display:none"></div>
    </div>
  </div>
</div>

<script>
let TOKEN = '';
let USER = '';

function showErr(msg) { let e=document.getElementById('login-err'); e.textContent=msg; e.style.display='block'; }

async function api(path, opts={}) {
  let headers = {...opts.headers||{}, 'Authorization':'Bearer '+TOKEN};
  if (!headers['Content-Type'] && !(opts.body instanceof FormData)) headers['Content-Type']='application/json';
  let r = await fetch(path, {...opts, headers});
  if (r.status===401) { logout(); return null; }
  let ct = r.headers.get('content-type')||'';
  if (ct.includes('json')) return r.json();
  if (ct.includes('pdf')) return r.blob();
  return r.text();
}

async function login() {
  let u = document.getElementById('login-user').value;
  let p = document.getElementById('login-pass').value;
  try {
    let r = await fetch('/api/v1/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:u,password:p})});
    if (!r.ok) { showErr('Invalid credentials'); return; }
    let d = await r.json();
    TOKEN = d.access_token; USER = d;
    document.getElementById('login-screen').style.display='none';
    document.getElementById('app').style.display='block';
    document.getElementById('user-display').textContent = d.username;
    document.getElementById('user-role').textContent = d.role;
    showSection('dashboard');
  } catch(e) { showErr('Connection error'); }
}

function logout() { TOKEN=''; document.getElementById('app').style.display='none'; document.getElementById('login-screen').style.display='flex'; }

function showSection(name) {
  document.querySelectorAll('#sidebar a').forEach(a=>a.classList.remove('active'));
  document.querySelectorAll('[id^="section-"]').forEach(s=>s.style.display='none');
  document.getElementById('section-'+name).style.display='block';
  event.target.classList.add('active');
  if (name==='dashboard') loadDashboard();
  else if (name==='pipeline') loadPipeline();
  else if (name==='coa') loadCOA();
  else if (name==='pettycash') loadPettyCash();
  else if (name==='cheques') loadCheques();
  else if (name==='wht') loadWHT();
  else if (name==='currency') loadCurrency();
  else if (name==='vendor') loadVendor();
  else if (name==='health') loadHealth();
}

/* ---- DASHBOARD ---- */
async function loadDashboard() {
  let el = document.getElementById('section-dashboard');
  el.innerHTML = '<div class="section-title">📊 Dashboard Overview</div><div class="kpi-grid" id="dash-kpis"></div><div class="col2"><div class="card" id="dash-pipeline-card"><h3>Pipeline Status</h3><div id="dash-pipeline-body">Loading...</div></div><div class="card" id="dash-chart-card"><h3>Stage Activity</h3><canvas id="stage-chart" height="180"></canvas></div></div>';
  let [kpi, pipe] = await Promise.all([api('/api/v1/reports/dashboard'), api('/api/v2/status')]);
  if (kpi) {
    let kg = document.getElementById('dash-kpis');
    let cards = [
      {label:'Total Revenue', val:kpi.total_revenue||kpi.event_count||'—', sub:'All time'},
      {label:'Active Events', val:kpi.event_count||'—', sub:''},
      {label:'Total Clients', val:kpi.client_count||'—', sub:''},
      {label:'Total Vendors', val:kpi.vendor_count||'—', sub:''},
    ];
    kg.innerHTML = cards.map(c=>'<div class="kpi-card"><div class="kpi-label">'+c.label+'</div><div class="kpi-value">'+(c.val||'—')+'</div><div class="kpi-sub">'+c.sub+'</div></div>').join('');
  }
  if (pipe) {
    let body = document.getElementById('dash-pipeline-body');
    let stages = pipe.stages||{};
    body.innerHTML = '<table><tr><th>Stage</th><th>Count</th></tr>'+Object.entries(stages).map(([k,v])=>'<tr><td>'+k+'</td><td>'+(v||0)+'</td></tr>').join('')+'</table>';
    let ctx = document.getElementById('stage-chart').getContext('2d');
    new Chart(ctx, {type:'bar', data:{
      labels:Object.keys(stages).map(s=>s.replace(/_/g,' ')),
      datasets:[{label:'Records', data:Object.values(stages), backgroundColor:'#324B7F', borderRadius:4}]
    }, options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true, ticks:{color:'#888'}}, x:{ticks:{color:'#888',maxRotation:45}}}}});
  }
}

/* ---- PIPELINE ---- */
async function loadPipeline() {
  let el = document.getElementById('section-pipeline');
  el.innerHTML = '<div class="section-title">🔄 Pipeline Status</div><div class="card" id="pipe-status">Loading...</div>';
  let s = await api('/api/v2/status');
  if (!s) return;
  let stages = s.stages||{};
  el.innerHTML = '<div class="section-title">🔄 Pipeline Status</div><div class="kpi-grid">'+
    Object.entries(stages).map(([k,v])=>'<div class="kpi-card"><div class="kpi-label">'+k.replace(/_/g,' ')+'</div><div class="kpi-value">'+(v||0)+'</div></div>').join('')+
    '</div><div class="card"><h3>8-Stage Pipeline Flow</h3>'+
    ['extract','validate','stage','reconcile','approve','promote','observe','journal'].map(st=>'<div style="display:inline-block;background:var(--surface2);padding:8px 14px;margin:4px;border-radius:4px;font-size:12px">'+st+'</div>').join('')+
    '</div>';
}

/* ---- COA ---- */
async function loadCOA() {
  let el = document.getElementById('section-coa');
  el.innerHTML = '<div class="section-title">📋 Chart of Accounts</div><div id="coa-body">Loading...</div>';
  let data = await api('/api/v1/coa/');
  if (!data) return;
  el.innerHTML = '<div class="section-title">📋 Chart of Accounts <span style="font-size:13px;font-weight:400;color:var(--muted)">('+data.length+' accounts)</span></div>'+
    '<div class="card" style="overflow-x:auto"><table><tr><th>Code</th><th>Name</th><th>Category</th><th>Type</th><th>Active</th></tr>'+
    data.map(a=>'<tr><td>'+a.acc_key+'</td><td>'+a.acc_name+'</td><td>'+a.categ_key+'</td><td>'+a.acc_type+'</td><td>'+(a.is_active?'✅':'❌')+'</td></tr>').join('')+'</table></div>';
}

/* ---- PETTY CASH ---- */
async function loadPettyCash() {
  let el = document.getElementById('section-pettycash');
  el.innerHTML = '<div class="section-title">💰 Petty Cash</div><div id="pc-body">Loading...</div>';
  let [list, stats] = await Promise.all([api('/api/v1/petty-cash/'), api('/api/v1/petty-cash/summary/stats')]);
  if (!list) return;
  el.innerHTML = '<div class="section-title">💰 Petty Cash</div>'+
    (stats?'<div class="kpi-grid"><div class="kpi-card"><div class="kpi-label">Approved</div><div class="kpi-value">'+stats.total_approved+'</div></div><div class="kpi-card"><div class="kpi-label">Pending</div><div class="kpi-value">'+stats.total_pending+'</div><div class="kpi-sub">EGP</div></div></div>':'')+
    '<div class="card" style="overflow-x:auto"><table><tr><th>Voucher</th><th>Date</th><th>Description</th><th>Amount</th><th>Status</th></tr>'+
    list.map(v=>'<tr><td>'+v.voucher_no+'</td><td>'+v.voucher_date+'</td><td>'+v.description+'</td><td>'+v.amount+'</td><td><span class="status status-'+(v.status==='approved'?'ok':'warn')+'">'+v.status+'</span></td></tr>').join('')+'</table></div>';
}

/* ---- CHEQUES ---- */
async function loadCheques() {
  let el = document.getElementById('section-cheques');
  el.innerHTML = '<div class="section-title">📝 Cheques</div><div id="chq-body">Loading...</div>';
  let [list, stats] = await Promise.all([api('/api/v1/cheques/'), api('/api/v1/cheques/summary/stats')]);
  if (!list) return;
  el.innerHTML = '<div class="section-title">📝 Cheques</div>'+
    (stats?'<div class="kpi-grid"><div class="kpi-card"><div class="kpi-label">Issued</div><div class="kpi-value">'+stats.total_issued+'</div></div><div class="kpi-card"><div class="kpi-label">Cleared</div><div class="kpi-value">'+stats.total_cleared+'</div></div><div class="kpi-card"><div class="kpi-label">Outstanding</div><div class="kpi-value">'+stats.total_outstanding+'</div></div></div>':'')+
    '<div class="card" style="overflow-x:auto"><table><tr><th>No</th><th>Payee</th><th>Amount</th><th>Status</th></tr>'+
    list.map(c=>'<tr><td>'+c.cheque_no+'</td><td>'+c.payee+'</td><td>'+c.amount+'</td><td><span class="status status-'+(c.status==='cleared'?'ok':c.status==='issued'?'warn':'err')+'">'+c.status+'</span></td></tr>').join('')+'</table></div>';
}

/* ---- WHT ---- */
async function loadWHT() {
  let el = document.getElementById('section-wht');
  el.innerHTML = '<div class="section-title">🧾 WHT Records</div><div id="wht-body">Loading...</div>';
  let [list, stats] = await Promise.all([api('/api/v1/wht/'), api('/api/v1/wht/summary/stats')]);
  if (!list) return;
  el.innerHTML = '<div class="section-title">🧾 WHT Records</div>'+
    (stats?'<div class="kpi-grid"><div class="kpi-card"><div class="kpi-label">Total WHT</div><div class="kpi-value">'+stats.total_wht+'</div></div><div class="kpi-card"><div class="kpi-label">Pending</div><div class="kpi-value">'+stats.pending_wht+'</div></div></div>':'')+
    '<div class="card" style="overflow-x:auto"><table><tr><th>Certificate</th><th>Gross</th><th>WHT</th><th>Status</th></tr>'+
    list.map(w=>'<tr><td>'+w.certificate_no+'</td><td>'+w.gross_amount+'</td><td>'+w.wht_amount+'</td><td><span class="status status-'+(w.status==='filed'?'ok':'warn')+'">'+w.status+'</span></td></tr>').join('')+'</table></div>';
}

/* ---- CURRENCY ---- */
async function loadCurrency() {
  let el = document.getElementById('section-currency');
  el.innerHTML = '<div class="section-title">💱 Currency Rates</div><div id="cur-body">Loading...</div>';
  let data = await api('/api/v1/currency/rates');
  if (!data) return;
  el.innerHTML = '<div class="section-title">💱 Currency Rates</div>'+
    '<div class="card" style="overflow-x:auto"><table><tr><th>Currency</th><th>Rate to EGP</th><th>Date</th></tr>'+
    data.map(c=>'<tr><td>'+c.currency+'</td><td>'+c.rate+'</td><td>'+c.date+'</td></tr>').join('')+'</table></div>';
}

/* ---- VENDOR RATING ---- */
async function loadVendor() {
  let el = document.getElementById('section-vendor');
  el.innerHTML = '<div class="section-title">⭐ Vendor Performance</div><div>Select a vendor to load (use API directly).</div>';
}

/* ---- HEALTH ---- */
async function loadHealth() {
  let el = document.getElementById('section-health');
  el.innerHTML = '<div class="section-title">🔍 System Health</div><div id="health-body">Loading...</div>';
  let h = await api('/health');
  if (!h) return;
  el.innerHTML = '<div class="section-title">🔍 System Health</div>'+
    '<div class="kpi-grid">'+
    '<div class="kpi-card"><div class="kpi-label">Status</div><div class="kpi-value" style="color:var(--green)">'+h.status+'</div></div>'+
    '<div class="kpi-card"><div class="kpi-label">Version</div><div class="kpi-value">'+h.version+'</div></div>'+
    '</div>';
}

/* Auto-login if token exists */
window.onload = function() { document.getElementById('login-pass').addEventListener('keydown',e=>{if(e.key==='Enter')login()}); }
</script>
</body>
</html>"""
