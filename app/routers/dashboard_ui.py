from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_index():
    return DASHBOARD_HTML


DASHBOARD_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>IncentiveHouse ERP</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<style>
:root{--bg:#1a1819;--surface:#231F20;--surface2:#2a2527;--surface3:#333;--accent:#324B7F;--accent2:#4a6aaa;--text:#e0e0e0;--muted:#888;--green:#4caf50;--red:#e53935;--orange:#ff9800;--cyan:#00bcd4;--border:#3a3537}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;font-size:14px}
a{color:var(--accent2);text-decoration:none}
input,select,textarea{background:var(--surface3);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:4px;font-size:13px;width:100%;margin-bottom:8px}
input:focus,select:focus{outline:none;border-color:var(--accent2)}
button{cursor:pointer;font-size:13px;padding:8px 18px;border-radius:4px;border:none;background:var(--accent);color:#fff;transition:all .15s}
button:hover{background:var(--accent2)}
button.danger{background:var(--red)}button.danger:hover{background:#c62828}
button.success{background:var(--green)}button.success:hover{background:#388e3c}
button.small{padding:4px 10px;font-size:11px}
.btn-outline{background:transparent;border:1px solid var(--border);color:var(--text)}
.btn-outline:hover{background:var(--surface2);border-color:var(--accent2)}

/* LOGIN SCREEN */
#login-screen{display:flex;align-items:center;justify-content:center;min-height:100vh;background:linear-gradient(135deg,#231F20 0%,#111 100%)}
.login-card{background:var(--surface);padding:40px;border-radius:12px;width:380px;border:1px solid var(--border)}
.login-card h1{font-size:22px;margin-bottom:4px}
.login-card .sub{color:var(--muted);font-size:13px;margin-bottom:24px}
.login-card .login-btn{width:100%;padding:12px;background:var(--accent);font-size:15px;margin-top:4px}
.login-card .login-btn:hover{background:var(--accent2)}
.login-card .login-err{color:var(--red);font-size:13px;margin-top:8px;display:none}

/* APP LAYOUT */
#app{display:none}
#app-header{background:var(--surface);padding:10px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}
#app-header .logo{font-size:16px;font-weight:600;letter-spacing:.3px}
#app-header .logo span{color:var(--accent2)}
#app-header .user-badge{font-size:12px;color:var(--muted);display:flex;align-items:center;gap:10px}
#app-header .user-badge .uname{color:var(--text);font-weight:500}
#app-header .user-badge .role-tag{background:var(--accent);padding:2px 8px;border-radius:10px;font-size:10px;color:#fff}
#app-header .logout-btn{background:transparent;border:1px solid var(--border);color:var(--muted);padding:5px 12px;font-size:11px}
#app-header .logout-btn:hover{background:var(--red);border-color:var(--red);color:#fff}

#main{display:flex}
#sidebar{width:230px;background:var(--surface);min-height:calc(100vh-54px);padding:8px 0;border-right:1px solid var(--border);flex-shrink:0;overflow-y:auto}
#sidebar .sec-label{padding:12px 16px 4px;font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px}
#sidebar a{display:flex;align-items:center;gap:8px;padding:9px 16px;font-size:13px;color:var(--muted);border-left:3px solid transparent;transition:all .12s}
#sidebar a:hover,#sidebar a.active{color:var(--text);background:rgba(255,255,255,.03);border-left-color:var(--accent)}
#sidebar a.active{color:#fff;font-weight:500}

#content{flex:1;padding:24px;overflow-x:hidden;max-width:calc(100vw-230px)}

.pg-title{font-size:20px;font-weight:600;margin-bottom:20px;display:flex;align-items:center;gap:10px}
.pg-title .sub{font-size:13px;font-weight:400;color:var(--muted)}

/* KPI grid */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:24px}
.kpi-card{background:var(--surface);border-radius:8px;padding:16px;border:1px solid var(--border);position:relative}
.kpi-card .kpi-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.kpi-card .kpi-value{font-size:24px;font-weight:700;margin:4px 0 2px}
.kpi-card .kpi-sub{font-size:11px;color:var(--muted)}
.kpi-card .kpi-icon{position:absolute;top:12px;right:12px;font-size:22px;opacity:.3}

/* Card */
.card{background:var(--surface);border-radius:8px;padding:20px;border:1px solid var(--border);margin-bottom:20px}
.card h3{font-size:13px;margin-bottom:14px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.card .card-actions{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}

/* Table */
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 8px;color:var(--muted);font-weight:400;border-bottom:1px solid var(--border);font-size:11px;text-transform:uppercase;white-space:nowrap}
td{padding:8px;border-bottom:1px solid rgba(255,255,255,.04);white-space:nowrap}
tr:hover td{background:rgba(255,255,255,.02)}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:500}
.badge-green{background:rgba(76,175,80,.15);color:var(--green)}
.badge-orange{background:rgba(255,152,0,.15);color:var(--orange)}
.badge-red{background:rgba(229,57,53,.15);color:var(--red)}
.badge-blue{background:rgba(50,75,127,.2);color:#7a9ad9}
.badge-cyan{background:rgba(0,188,212,.15);color:var(--cyan)}

/* Two/three column */
.col2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.col3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}
@media(max-width:900px){.col2,.col3{grid-template-columns:1fr}}

/* Search bar */
.search-bar{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.search-bar input{width:220px;margin-bottom:0}
.search-bar select{width:150px;margin-bottom:0}

/* Modal overlay */
.modal-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:1000;align-items:center;justify-content:center}
.modal-overlay.show{display:flex}
.modal{background:var(--surface);border-radius:10px;padding:28px;width:520px;max-width:90vw;max-height:85vh;overflow-y:auto;border:1px solid var(--border)}
.modal h2{font-size:16px;margin-bottom:16px}
.modal .form-group{margin-bottom:10px}
.modal .form-group label{display:block;font-size:12px;color:var(--muted);margin-bottom:2px}
.modal .modal-actions{display:flex;gap:8px;justify-content:flex-end;margin-top:16px}
.empty-state{text-align:center;padding:30px;color:var(--muted);font-size:13px}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="login-screen">
  <div class="login-card">
    <h1>🏢 IncentiveHouse</h1>
    <div class="sub">ERP v2.2.2 — Sign in to your account</div>
    <input type="text" id="login-user" placeholder="Username" value="admin">
    <input type="password" id="login-pass" placeholder="Password" value="admin">
    <button class="login-btn" onclick="login()">Sign In</button>
    <div class="login-err" id="login-err"></div>
  </div>
</div>

<!-- APP -->
<div id="app">
  <div id="app-header">
    <div class="logo">🏢 <span>IncentiveHouse</span> ERP</div>
    <div class="user-badge">
      <span class="uname" id="user-display">—</span>
      <span class="role-tag" id="user-role">—</span>
      <button class="logout-btn" onclick="logout()">Logout</button>
    </div>
  </div>
  <div id="main">
    <div id="sidebar">
      <div class="sec-label">Main</div>
      <a class="active" onclick="showPage('dashboard')">📊 Dashboard</a>
      <a onclick="showPage('events')">📅 Event Management + PNR</a>
      <div class="sec-label">Finance & Accounting</div>
      <a onclick="showPage('sales')">💰 Sales + Clients</a>
      <a onclick="showPage('purchasing')">📦 Purchasing + Vendors</a>
      <a onclick="showPage('financial')">🏦 Financial Dashboard</a>
      <a onclick="showPage('coa')">📋 COA</a>
      <a onclick="showPage('pettycash')">💵 Petty Cash</a>
      <a onclick="showPage('cheques')">📝 Cheques</a>
      <a onclick="showPage('wht')">🧾 WHT & VAT</a>
      <a onclick="showPage('currency')">💱 Currency</a>
      <a onclick="showPage('audit')">📜 Audit Trail</a>
      <div class="sec-label">Operations</div>
      <a onclick="showPage('bank')">🏧 Bank</a>
      <a onclick="showPage('pipeline')">🔄 Pipeline</a>
      <a onclick="showPage('health')">🔍 System Health</a>
    </div>
    <div id="content">
      <div id="pg-dashboard"></div>
      <div id="pg-events" style="display:none"></div>
      <div id="pg-sales" style="display:none"></div>
      <div id="pg-purchasing" style="display:none"></div>
      <div id="pg-financial" style="display:none"></div>
      <div id="pg-coa" style="display:none"></div>
      <div id="pg-clients" style="display:none"></div>
      <div id="pg-vendors" style="display:none"></div>
      <div id="pg-pnr" style="display:none"></div>
      <div id="pg-bank" style="display:none"></div>
      <div id="pg-pettycash" style="display:none"></div>
      <div id="pg-cheques" style="display:none"></div>
      <div id="pg-wht" style="display:none"></div>
      <div id="pg-pipeline" style="display:none"></div>
      <div id="pg-currency" style="display:none"></div>
      <div id="pg-audit" style="display:none"></div>
      <div id="pg-health" style="display:none"></div>
    </div>
  </div>
</div>

<!-- MODAL -->
<div class="modal-overlay" id="modal-overlay"><div class="modal" id="modal-content"></div></div>

<script>
let TOKEN='', USER=null, currentPage='dashboard', chartInstances={};

function showLoginErr(m){let e=document.getElementById('login-err');e.textContent=m;e.style.display='block'}
function closeModal(){document.getElementById('modal-overlay').classList.remove('show')}

async function api(path,opts={}){
  let h={...opts.headers||{},'Authorization':'Bearer '+TOKEN};
  if(!h['Content-Type']&&!(opts.body instanceof FormData))h['Content-Type']='application/json';
  let r=await fetch(path,{...opts,headers:h});
  if(r.status===401){logout();return null}
  let ct=r.headers.get('content-type')||'';
  if(ct.includes('json'))return r.json();
  if(ct.includes('pdf'))return r.blob();
  return r.text();
}

async function login(){
  let u=document.getElementById('login-user').value;
  let p=document.getElementById('login-pass').value;
  try{
    let r=await fetch('/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
    if(!r.ok){showLoginErr('Invalid credentials');return}
    let d=await r.json();TOKEN=d.access_token;USER=d;
    document.getElementById('login-screen').style.display='none';
    document.getElementById('app').style.display='block';
    document.getElementById('user-display').textContent=d.username;
    document.getElementById('user-role').textContent=d.role;
    showPage('dashboard');
  }catch(e){showLoginErr('Connection error')}
}

function logout(){TOKEN='';document.getElementById('app').style.display='none';document.getElementById('login-screen').style.display='flex';closeModal()}

function showPage(name){
  currentPage=name;
  document.querySelectorAll('#sidebar a').forEach(a=>a.classList.remove('active'));
  document.querySelectorAll('[id^="pg-"]').forEach(s=>s.style.display='none');
  document.getElementById('pg-'+name).style.display='block';
  // Highlight nearest sidebar link
  document.querySelectorAll('#sidebar a').forEach(a=>{if(a.textContent.includes(name)||name.includes(a.textContent.trim().split(' ')[0]))a.classList.add('active')});
  let fn={dashboard:loadDashboard,events:loadEvents,sales:loadSales,purchasing:loadPurchasing,financial:loadFinancial,coa:loadCOA,clients:loadClients,vendors:loadVendors,pnr:loadPNR,bank:loadBank,pettycash:loadPettyCash,cheques:loadCheques,wht:loadWHT,pipeline:loadPipeline,currency:loadCurrency,audit:loadAudit,health:loadHealth};
  if(fn[name])fn[name]();
}
function showPageDirect(name){showPage(name)}

/* ====================== DASHBOARD ====================== */
async function loadDashboard(){
  let el=document.getElementById('pg-dashboard');
  el.innerHTML='<div class="pg-title">📊 Dashboard</div><div class="kpi-grid" id="dash-kpis"></div><div class="col2"><div class="card"><h3>Pipeline Stage Activity</h3><canvas id="chart-pipeline" height="200"></canvas></div><div class="card"><h3>Recent Audit Activity</h3><div id="dash-audit"></div></div></div>';
  let [kpi,pipe,audit]=await Promise.all([api('/api/v1/reports/dashboard'),api('/api/v2/status'),api('/api/v1/finance/audit?limit=8')]);
  if(kpi){
    let g=document.getElementById('dash-kpis');
    let items=[
      {label:'Events',val:kpi.event_count||0,icon:'📅',sub:'Total events'},
      {label:'Clients',val:kpi.client_count||0,icon:'👥',sub:'Active clients'},
      {label:'Vendors',val:kpi.vendor_count||0,icon:'🏭',sub:'Active vendors'},
      {label:'Invoices',val:kpi.invoice_count||0,icon:'💰',sub:'Sales invoices'}];
    g.innerHTML=items.map(i=>'<div class="kpi-card"><div class="kpi-icon">'+i.icon+'</div><div class="kpi-label">'+i.label+'</div><div class="kpi-value">'+i.val+'</div><div class="kpi-sub">'+i.sub+'</div></div>').join('');
  }
  if(pipe){
    let s=pipe.stages||{},labels=Object.keys(s).map(k=>k.replace(/_/g,' '));
    setTimeout(()=>{
      let ctx=document.getElementById('chart-pipeline');if(!ctx)return;
      if(chartInstances.pipeline)chartInstances.pipeline.destroy();
      chartInstances.pipeline=new Chart(ctx.getContext('2d'),{type:'bar',data:{labels,datasets:[{label:'Records',data:Object.values(s),backgroundColor:'#324B7F',borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{color:'#888'}},x:{ticks:{color:'#888',maxRotation:45}}}}});
    },100);
  }
  if(audit){
    document.getElementById('dash-audit').innerHTML='<table><tr><th>Action</th><th>Table</th><th>User</th></tr>'+
      audit.slice(0,8).map(a=>'<tr><td><span class="badge badge-blue">'+a.action+'</span></td><td>'+a.table_name+'</td><td>'+a.changed_by+'</td></tr>').join('')+'</table>';
  }
}

/* ====================== EVENTS ====================== */
async function loadEvents(){
  let el=document.getElementById('pg-events');
  el.innerHTML='<div class="pg-title">📅 Event Management <span class="sub">Events + linked PNR Work Orders</span></div><div class="card-actions"><button onclick="showEventForm()">+ New Event</button><button class="btn-outline" onclick="showPageDirect(\'pnr\')">📄 Go to PNR Module</button></div>'+
    '<div class="card"><h3>Events</h3><div class="table-wrap"><table id="events-table"><tr><th>Code</th><th>Name</th><th>Type</th><th>Status</th><th>Date</th><th>Branch</th><th>Actions</th></tr><tr><td colspan="7" class="empty-state">Loading...</td></tr></table></div></div>'+
    '<div class="card"><h3>📄 Linked PNR / Work Orders</h3><div class="table-wrap"><table id="evt-pnr-table"><tr><th>PNR Code</th><th>Name</th><th>Type</th><th>Customer</th><th>Budget</th></tr><tr><td colspan="5" class="empty-state">Loading PNRs...</td></tr></table></div></div>';
  let [events,pnrs]=await Promise.all([api('/api/v1/events/?limit=200'),api('/api/v1/pnr/?limit=200')]);
  if(events){
    let tb=document.getElementById('events-table');
    if(events.length===0){tb.innerHTML='<tr><td colspan="7" class="empty-state">No events found</td></tr>'}
    else tb.innerHTML=events.map(e=>'<tr><td>'+e.event_code+'</td><td><strong>'+e.event_name+'</strong></td><td>'+(e.event_type||'—')+'</td><td><span class="badge '+(e.status==='active'?'badge-green':e.status==='cancelled'?'badge-red':'badge-orange')+'">'+(e.status||'—')+'</span></td><td>'+(e.start_date||'—')+'</td><td>'+(e.branch||'—')+'</td><td><button class="small btn-outline" onclick="viewEvent('+e.event_id+')">View</button></td></tr>').join('');
  }
  if(pnrs){
    let tb=document.getElementById('evt-pnr-table');
    if(pnrs.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No PNR records</td></tr>'}
    else tb.innerHTML=pnrs.map(p=>'<tr><td><strong>'+p.pnr_code+'</strong></td><td>'+(p.name||'—')+'</td><td>'+(p.pnr_type||'—')+'</td><td>'+(p.customer_name||'—')+'</td><td>'+(p.total_budget||'—')+'</td></tr>').join('');
  }
}

function showEventForm(data){
  let m=document.getElementById('modal-content');
  let isEdit=data&&data.event_id;
  m.innerHTML='<h2>'+(isEdit?'Edit Event':'New Event')+'</h2>'+
    '<div class="form-group"><label>Event Code</label><input id="f-evt-code" value="'+(data?data.event_code:'')+'"></div>'+
    '<div class="form-group"><label>Event Name</label><input id="f-evt-name" value="'+(data?data.event_name:'')+'"></div>'+
    '<div class="col2"><div class="form-group"><label>Type</label><select id="f-evt-type"><option>Corporate</option><option>Wedding</option><option>Conference</option><option>Exhibition</option><option>Private</option></select></div>'+
    '<div class="form-group"><label>Status</label><select id="f-evt-status"><option>active</option><option>planning</option><option>completed</option><option>cancelled</option></select></div></div>'+
    '<div class="col2"><div class="form-group"><label>Start Date</label><input type="date" id="f-evt-start" value="'+(data&&data.start_date?data.start_date:'')+'"></div>'+
    '<div class="form-group"><label>End Date</label><input type="date" id="f-evt-end" value="'+(data&&data.end_date?data.end_date:'')+'"></div></div>'+
    '<div class="form-group"><label>Branch</label><input id="f-evt-branch" value="'+(data?data.branch||'':'')+'"></div>'+
    '<div class="modal-actions"><button class="btn-outline" onclick="closeModal()">Cancel</button><button class="success" onclick="saveEvent('+(data?data.event_id:'null')+')">'+(isEdit?'Update':'Create')+'</button></div>';
  document.getElementById('modal-overlay').classList.add('show');
}

async function saveEvent(id){
  let body={event_code:document.getElementById('f-evt-code').value,event_name:document.getElementById('f-evt-name').value,event_type:document.getElementById('f-evt-type').value,status:document.getElementById('f-evt-status').value,start_date:document.getElementById('f-evt-start').value||null,end_date:document.getElementById('f-evt-end').value||null,branch:document.getElementById('f-evt-branch').value||null};
  let r=id?await api('/api/v1/events/'+id,{method:'PUT',body:JSON.stringify(body)}):await api('/api/v1/events/',{method:'POST',body:JSON.stringify(body)});
  if(r){closeModal();loadEvents()}
}

async function viewEvent(id){
  let e=await api('/api/v1/events/'+id);if(!e)return;
  let m=document.getElementById('modal-content');
  m.innerHTML='<h2>📅 '+e.event_name+'</h2>'+
    '<div class="col2"><div class="form-group"><label>Code</label><div>'+e.event_code+'</div></div>'+
    '<div class="form-group"><label>Status</label><div><span class="badge badge-green">'+(e.status||'—')+'</span></div></div></div>'+
    '<div class="col2"><div class="form-group"><label>Type</label><div>'+(e.event_type||'—')+'</div></div>'+
    '<div class="form-group"><label>Branch</label><div>'+(e.branch||'—')+'</div></div></div>'+
    '<div class="col2"><div class="form-group"><label>Start</label><div>'+(e.start_date||'—')+'</div></div>'+
    '<div class="form-group"><label>End</label><div>'+(e.end_date||'—')+'</div></div></div>'+
    '<div class="modal-actions"><button class="btn-outline" onclick="closeModal()">Close</button><button onclick="showEventForm('+JSON.stringify(e).replace(/"/g,'&quot;')+')">Edit</button></div>';
  document.getElementById('modal-overlay').classList.add('show');
}

/* ====================== SALES ====================== */
async function loadSales(){
  let el=document.getElementById('pg-sales');
  el.innerHTML='<div class="pg-title">💰 Sales <span class="sub">Sales invoices + linked Clients</span></div><div class="card-actions"><button onclick="showSalesForm()">+ New Invoice</button><button class="btn-outline" onclick="showPageDirect(\'clients\')">👥 Go to Clients Module</button></div>'+
    '<div class="card"><h3>Sales Invoices</h3><div class="table-wrap"><table id="sales-table"><tr><th>Invoice#</th><th>Client</th><th>Category</th><th>Amount</th><th>Status</th><th>Date</th><th>Actions</th></tr><tr><td colspan="7" class="empty-state">Loading...</td></tr></table></div></div>'+
    '<div class="card"><h3>👥 Client Directory</h3><div class="table-wrap"><table id="sal-clients-table"><tr><th>Code</th><th>Name</th><th>Email</th><th>Phone</th><th>Category</th></tr><tr><td colspan="5" class="empty-state">Loading clients...</td></tr></table></div></div>';
  let [list,clients]=await Promise.all([api('/api/v1/sales/?limit=200'),api('/api/v1/clients/?limit=200')]);
  if(list){
    let tb=document.getElementById('sales-table');
    if(list.length===0){tb.innerHTML='<tr><td colspan="7" class="empty-state">No sales invoices</td></tr>'}
    else tb.innerHTML=list.map(i=>'<tr><td><strong>'+i.invoice_no+'</strong></td><td>'+(i.client_name||i.client_code||'—')+'</td><td>'+(i.category||'—')+'</td><td>'+i.total_amount+'</td><td><span class="badge '+(i.status==='paid'?'badge-green':i.status==='pending'?'badge-orange':'badge-blue')+'">'+(i.status||'—')+'</span></td><td>'+(i.invoice_date||'—')+'</td><td><button class="small btn-outline" onclick="viewSales('+i.inv_id+')">View</button></td></tr>').join('');
  }
  if(clients){
    let tb=document.getElementById('sal-clients-table');
    if(clients.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No clients</td></tr>'}
    else tb.innerHTML=clients.map(c=>'<tr><td>'+c.client_code+'</td><td><strong>'+c.name+'</strong></td><td>'+(c.email||'—')+'</td><td>'+(c.phone||'—')+'</td><td>'+(c.category||'—')+'</td></tr>').join('');
  }
}

function showSalesForm(){
  let m=document.getElementById('modal-content');
  m.innerHTML='<h2>New Sales Invoice</h2>'+
    '<div class="form-group"><label>Invoice No</label><input id="f-sal-no"></div>'+
    '<div class="form-group"><label>Client Code</label><input id="f-sal-client"></div>'+
    '<div class="form-group"><label>Client Name</label><input id="f-sal-cname"></div>'+
    '<div class="col2"><div class="form-group"><label>Category</label><select id="f-sal-cat"><option>Services</option><option>Products</option><option>Consulting</option><option>Events</option></select></div>'+
    '<div class="form-group"><label>Amount</label><input type="number" id="f-sal-amt" step="0.01"></div></div>'+
    '<div class="col2"><div class="form-group"><label>Invoice Date</label><input type="date" id="f-sal-date"></div>'+
    '<div class="form-group"><label>Due Date</label><input type="date" id="f-sal-due"></div></div>'+
    '<div class="form-group"><label>Status</label><select id="f-sal-status"><option>pending</option><option>paid</option><option>overdue</option></select></div>'+
    '<div class="modal-actions"><button class="btn-outline" onclick="closeModal()">Cancel</button><button class="success" onclick="saveSales()">Create</button></div>';
  document.getElementById('modal-overlay').classList.add('show');
}

async function saveSales(){
  let body={invoice_no:document.getElementById('f-sal-no').value,client_code:document.getElementById('f-sal-client').value,client_name:document.getElementById('f-sal-cname').value,category:document.getElementById('f-sal-cat').value,total_amount:parseFloat(document.getElementById('f-sal-amt').value)||0,invoice_date:document.getElementById('f-sal-date').value||null,due_date:document.getElementById('f-sal-due').value||null,status:document.getElementById('f-sal-status').value};
  let r=await api('/api/v1/sales/',{method:'POST',body:JSON.stringify(body)});
  if(r){closeModal();loadSales()}
}

async function viewSales(id){
  let i=await api('/api/v1/sales/'+id);if(!i)return;
  let m=document.getElementById('modal-content');
  m.innerHTML='<h2>💰 Invoice #'+i.invoice_no+'</h2>'+
    '<div class="col2"><div class="form-group"><label>Client</label><div>'+(i.client_name||i.client_code||'—')+'</div></div>'+
    '<div class="form-group"><label>Status</label><div><span class="badge badge-green">'+(i.status||'—')+'</span></div></div></div>'+
    '<div class="col2"><div class="form-group"><label>Amount</label><div style="font-size:20px;font-weight:700">'+i.total_amount+' EGP</div></div>'+
    '<div class="form-group"><label>Category</label><div>'+(i.category||'—')+'</div></div></div>'+
    '<div class="col2"><div class="form-group"><label>Date</label><div>'+(i.invoice_date||'—')+'</div></div>'+
    '<div class="form-group"><label>Due Date</label><div>'+(i.due_date||'—')+'</div></div></div>'+
    '<div class="modal-actions"><button class="btn-outline" onclick="closeModal()">Close</button></div>';
  document.getElementById('modal-overlay').classList.add('show');
}

/* ====================== PURCHASING ====================== */
async function loadPurchasing(){
  let el=document.getElementById('pg-purchasing');
  el.innerHTML='<div class="pg-title">📦 Purchasing <span class="sub">Purchase invoices + linked Vendors</span></div><div class="card-actions"><button class="btn-outline" onclick="showPageDirect(\'vendors\')">🏭 Go to Vendors Module</button></div>'+
    '<div class="card"><h3>Purchase Invoices</h3><div class="table-wrap"><table id="purch-table"><tr><th>Invoice#</th><th>Vendor</th><th>Amount</th><th>Status</th><th>Date</th></tr><tr><td colspan="5" class="empty-state">Loading...</td></tr></table></div></div>'+
    '<div class="card"><h3>🏭 Vendor Directory</h3><div class="table-wrap"><table id="pur-vendors-table"><tr><th>Code</th><th>Name</th><th>Category</th><th>Phone</th><th>Email</th></tr><tr><td colspan="5" class="empty-state">Loading vendors...</td></tr></table></div></div>';
  let [purchases,vendors]=await Promise.all([api('/api/v1/finance/invoices/purchases'),api('/api/v1/vendors/?limit=200')]);
  if(purchases){
    let tb=document.getElementById('purch-table');
    if(purchases.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No purchase invoices</td></tr>'}
    else tb.innerHTML=purchases.map(i=>'<tr><td><strong>'+i.invoice_no+'</strong></td><td>'+(i.vendor_name||'—')+'</td><td>'+i.total_amount+'</td><td><span class="badge '+(i.status==='paid'?'badge-green':i.status==='pending'?'badge-orange':'badge-blue')+'">'+(i.status||'—')+'</span></td><td>'+(i.due_date||'—')+'</td></tr>').join('');
  }
  if(vendors){
    let tb=document.getElementById('pur-vendors-table');
    if(vendors.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No vendors</td></tr>'}
    else tb.innerHTML=vendors.map(v=>'<tr><td>'+v.vendor_code+'</td><td><strong>'+v.name+'</strong></td><td>'+(v.category||'—')+'</td><td>'+(v.phone||'—')+'</td><td>'+(v.email||'—')+'</td></tr>').join('');
  }
}

/* ====================== FINANCIAL ====================== */
async function loadFinancial(){
  let el=document.getElementById('pg-financial');
  el.innerHTML='<div class="pg-title">🏦 Financial Dashboard <span class="sub">Cash flow · Aging · COA · Petty Cash · Cheques · WHT/VAT · Currency</span></div>'+
    '<div class="kpi-grid" id="fin-kpis"></div>'+
    '<div class="col2"><div class="card"><h3>Cash Flow (30d Projection)</h3><div id="fin-cashflow"></div></div><div class="card"><h3>Aging Report</h3><div id="fin-aging"></div></div></div>'+
    '<div class="col3"><div class="card"><h3>📋 COA Quick</h3><div id="fin-coa">Loading...</div><div style="margin-top:10px"><button class="small btn-outline" onclick="showPageDirect(\'coa\')">Full COA →</button></div></div>'+
    '<div class="card"><h3>💵 Petty Cash</h3><div id="fin-pc">Loading...</div><div style="margin-top:10px"><button class="small btn-outline" onclick="showPageDirect(\'pettycash\')">Full Petty Cash →</button></div></div>'+
    '<div class="card"><h3>🧾 WHT & VAT</h3><div id="fin-wht">Loading...</div><div style="margin-top:10px"><button class="small btn-outline" onclick="showPageDirect(\'wht\')">Full WHT →</button></div></div></div>'+
    '<div class="col2"><div class="card"><h3>📝 Cheques Summary</h3><div id="fin-chq">Loading...</div><div style="margin-top:10px"><button class="small btn-outline" onclick="showPageDirect(\'cheques\')">Full Cheques →</button></div></div>'+
    '<div class="card"><h3>💱 Currency Rates</h3><div id="fin-currency">Loading...</div><div style="margin-top:10px"><button class="small btn-outline" onclick="showPageDirect(\'currency\')">Full Currency →</button></div></div></div>';
  let [cashflow,aging,coa,pc,wht,chq,currency]=await Promise.all([
    api('/api/v1/finance/cash-flow-projections?days=30'),api('/api/v1/finance/aging-report'),
    api('/api/v1/coa/?limit=5'),api('/api/v1/petty-cash/summary/stats'),
    api('/api/v1/wht/summary/stats'),api('/api/v1/cheques/summary/stats'),
    api('/api/v1/currency/rates?limit=5')]);
  if(cashflow){
    document.getElementById('fin-kpis').innerHTML='<div class="kpi-card"><div class="kpi-label">Expected Inflow</div><div class="kpi-value" style="color:var(--green)">'+cashflow.expected_inflow+'</div><div class="kpi-sub">Next 30 days</div></div><div class="kpi-card"><div class="kpi-label">Expected Outflow</div><div class="kpi-value" style="color:var(--red)">'+cashflow.expected_outflow+'</div><div class="kpi-sub">Next 30 days</div></div><div class="kpi-card"><div class="kpi-label">Net Position</div><div class="kpi-value">'+cashflow.net_position+'</div><div class="kpi-sub">Projected</div></div>';
  }
  if(aging){
    let html='';
    for(let [k,items] of Object.entries(aging)){let total=items.reduce((s,i)=>s+(i.balance||0),0);html+='<div style="margin-bottom:6px;font-size:12px"><strong>'+k+'</strong>: '+items.length+' inv · '+total.toFixed(2)+' EGP</div>';}
    document.getElementById('fin-aging').innerHTML=html||'<div class="empty-state">No aging</div>';
  }
  if(coa) document.getElementById('fin-coa').innerHTML='<table><tr><th>Code</th><th>Name</th></tr>'+coa.slice(0,5).map(a=>'<tr><td style="font-size:11px">'+a.acc_key+'</td><td style="font-size:11px">'+a.acc_name+'</td></tr>').join('')+'</table>';
  if(pc) document.getElementById('fin-pc').innerHTML='<div style="font-size:13px">Approved: <strong style="color:var(--green)">'+pc.total_approved+'</strong></div><div style="font-size:13px">Pending: <strong style="color:var(--orange)">'+pc.total_pending+'</strong></div>';
  if(wht) document.getElementById('fin-wht').innerHTML='<div style="font-size:13px">Total WHT: <strong style="color:var(--red)">'+wht.total_wht+'</strong></div><div style="font-size:13px">Pending: <strong style="color:var(--orange)">'+wht.pending_wht+'</strong></div><div style="font-size:11px;color:var(--muted);margin-top:4px">VAT rate: 14% (standard)</div>';
  if(chq) document.getElementById('fin-chq').innerHTML='<div style="font-size:13px">Issued: <strong>'+chq.total_issued+'</strong></div><div style="font-size:13px">Cleared: <strong style="color:var(--green)">'+chq.total_cleared+'</strong></div><div style="font-size:13px">Outstanding: <strong style="color:var(--orange)">'+chq.total_outstanding+'</strong></div>';
  if(currency) document.getElementById('fin-currency').innerHTML='<table><tr><th>Curr</th><th>Rate</th></tr>'+currency.slice(0,5).map(c=>'<tr><td style="font-size:11px">'+c.currency+'</td><td style="font-size:11px">'+c.rate+'</td></tr>').join('')+'</table>';
}

/* ====================== COA ====================== */
async function loadCOA(){
  let el=document.getElementById('pg-coa');
  el.innerHTML='<div class="pg-title">📋 Chart of Accounts <span class="sub">General ledger accounts</span></div><div class="card"><div class="table-wrap"><table id="coa-table"><tr><th>Code</th><th>Name</th><th>Category</th><th>Type</th><th>Active</th></tr><tr><td colspan="5" class="empty-state">Loading...</td></tr></table></div></div>';
  let data=await api('/api/v1/coa/');
  let tb=document.getElementById('coa-table');
  if(!data||data.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No accounts</td></tr>';return}
  tb.innerHTML=data.map(a=>'<tr><td>'+a.acc_key+'</td><td><strong>'+a.acc_name+'</strong></td><td>'+(a.categ_key||'—')+'</td><td>'+(a.acc_type||'—')+'</td><td>'+(a.is_active?'✅':'❌')+'</td></tr>').join('');
}

/* ====================== CLIENTS ====================== */
async function loadClients(){
  let el=document.getElementById('pg-clients');
  el.innerHTML='<div class="pg-title">👥 Clients <span class="sub">Manage client records</span></div><div class="card-actions"><button onclick="showClientForm()">+ New Client</button></div><div class="card"><div class="table-wrap"><table id="clients-table"><tr><th>Code</th><th>Name</th><th>Email</th><th>Phone</th><th>Category</th><th>Actions</th></tr><tr><td colspan="6" class="empty-state">Loading...</td></tr></table></div></div>';
  let data=await api('/api/v1/clients/?limit=200');
  if(!data)return;
  let tb=document.getElementById('clients-table');
  if(data.length===0){tb.innerHTML='<tr><td colspan="6" class="empty-state">No clients</td></tr>';return}
  tb.innerHTML=data.map(c=>'<tr><td>'+c.client_code+'</td><td><strong>'+c.name+'</strong></td><td>'+(c.email||'—')+'</td><td>'+(c.phone||'—')+'</td><td>'+(c.category||'—')+'</td><td><button class="small btn-outline" onclick="viewClient('+c.client_id+')">View</button></td></tr>').join('');
}

function showClientForm(){
  let m=document.getElementById('modal-content');
  m.innerHTML='<h2>New Client</h2><div class="col2"><div class="form-group"><label>Client Code</label><input id="f-cl-code"></div><div class="form-group"><label>Name</label><input id="f-cl-name"></div></div><div class="col2"><div class="form-group"><label>Email</label><input id="f-cl-email" type="email"></div><div class="form-group"><label>Phone</label><input id="f-cl-phone"></div></div><div class="form-group"><label>Category</label><select id="f-cl-cat"><option>Corporate</option><option>Individual</option><option>Government</option><option>NGO</option></select></div><div class="modal-actions"><button class="btn-outline" onclick="closeModal()">Cancel</button><button class="success" onclick="saveClient()">Create</button></div>';
  document.getElementById('modal-overlay').classList.add('show');
}
async function saveClient(){
  let body={client_code:document.getElementById('f-cl-code').value,name:document.getElementById('f-cl-name').value,email:document.getElementById('f-cl-email').value||null,phone:document.getElementById('f-cl-phone').value||null,category:document.getElementById('f-cl-cat').value};
  let r=await api('/api/v1/clients/',{method:'POST',body:JSON.stringify(body)});
  if(r){closeModal();loadClients()}
}
async function viewClient(id){
  let c=await api('/api/v1/clients/'+id);if(!c)return;
  let m=document.getElementById('modal-content');
  m.innerHTML='<h2>👥 '+c.name+'</h2><div class="col2"><div class="form-group"><label>Code</label><div>'+c.client_code+'</div></div><div class="form-group"><label>Email</label><div>'+(c.email||'—')+'</div></div></div><div class="col2"><div class="form-group"><label>Phone</label><div>'+(c.phone||'—')+'</div></div><div class="form-group"><label>Category</label><div>'+(c.category||'—')+'</div></div></div><div class="modal-actions"><button class="btn-outline" onclick="closeModal()">Close</button></div>';
  document.getElementById('modal-overlay').classList.add('show');
}

/* ====================== VENDORS ====================== */
async function loadVendors(){
  let el=document.getElementById('pg-vendors');
  el.innerHTML='<div class="pg-title">🏭 Vendors <span class="sub">Vendor directory & performance</span></div><div class="card-actions"><button onclick="showVendorForm()">+ New Vendor</button></div><div class="card"><div class="table-wrap"><table id="vendors-table"><tr><th>Code</th><th>Name</th><th>Category</th><th>Phone</th><th>Email</th><th>Actions</th></tr><tr><td colspan="6" class="empty-state">Loading...</td></tr></table></div></div>';
  let data=await api('/api/v1/vendors/?limit=200');
  if(!data)return;
  let tb=document.getElementById('vendors-table');
  if(data.length===0){tb.innerHTML='<tr><td colspan="6" class="empty-state">No vendors</td></tr>';return}
  tb.innerHTML=data.map(v=>'<tr><td>'+v.vendor_code+'</td><td><strong>'+v.name+'</strong></td><td>'+(v.category||'—')+'</td><td>'+(v.phone||'—')+'</td><td>'+(v.email||'—')+'</td><td><button class="small btn-outline" onclick="viewVendor('+v.vendor_id+')">View</button></td></tr>').join('');
}

function showVendorForm(){
  let m=document.getElementById('modal-content');
  m.innerHTML='<h2>New Vendor</h2><div class="col2"><div class="form-group"><label>Vendor Code</label><input id="f-v-code"></div><div class="form-group"><label>Name</label><input id="f-v-name"></div></div><div class="col2"><div class="form-group"><label>Email</label><input id="f-v-email" type="email"></div><div class="form-group"><label>Phone</label><input id="f-v-phone"></div></div><div class="form-group"><label>Category</label><select id="f-v-cat"><option>Supplier</option><option>Service</option><option>Contractor</option><option>Consultant</option></select></div><div class="modal-actions"><button class="btn-outline" onclick="closeModal()">Cancel</button><button class="success" onclick="saveVendor()">Create</button></div>';
  document.getElementById('modal-overlay').classList.add('show');
}
async function saveVendor(){
  let body={vendor_code:document.getElementById('f-v-code').value,name:document.getElementById('f-v-name').value,email:document.getElementById('f-v-email').value||null,phone:document.getElementById('f-v-phone').value||null,category:document.getElementById('f-v-cat').value};
  let r=await api('/api/v1/vendors/',{method:'POST',body:JSON.stringify(body)});
  if(r){closeModal();loadVendors()}
}
async function viewVendor(id){
  let v=await api('/api/v1/vendors/'+id);if(!v)return;
  let m=document.getElementById('modal-content');
  m.innerHTML='<h2>🏭 '+v.name+'</h2><div class="col2"><div class="form-group"><label>Code</label><div>'+v.vendor_code+'</div></div><div class="form-group"><label>Category</label><div>'+(v.category||'—')+'</div></div></div><div class="col2"><div class="form-group"><label>Email</label><div>'+(v.email||'—')+'</div></div><div class="form-group"><label>Phone</label><div>'+(v.phone||'—')+'</div></div></div><div class="modal-actions"><button class="btn-outline" onclick="closeModal()">Close</button></div>';
  document.getElementById('modal-overlay').classList.add('show');
}

/* ====================== PNR ====================== */
async function loadPNR(){
  let el=document.getElementById('pg-pnr');
  el.innerHTML='<div class="pg-title">📄 PNR / Work Orders <span class="sub">Purchase order & work order management</span></div><div class="card"><div class="table-wrap"><table><tr><th>PNR Code</th><th>Name</th><th>Type</th><th>Customer</th><th>Total</th></tr><tr><td colspan="5" class="empty-state">Loading...</td></tr></table></div></div>';
  let data=await api('/api/v1/pnr/?limit=200');
  let tb=document.querySelector('#pg-pnr table');
  if(!data||data.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No PNR records</td></tr>';return}
  tb.innerHTML=data.map(p=>'<tr><td><strong>'+p.pnr_code+'</strong></td><td>'+(p.name||'—')+'</td><td>'+(p.pnr_type||'—')+'</td><td>'+(p.customer_name||'—')+'</td><td>'+(p.total_budget||'—')+'</td></tr>').join('');
}

/* ====================== BANK ====================== */
async function loadBank(){
  let el=document.getElementById('pg-bank');
  el.innerHTML='<div class="pg-title">🏧 Bank <span class="sub">Bank transactions & reconciliation</span></div><div class="kpi-grid" id="bank-kpis"></div><div class="card"><div class="table-wrap"><table id="bank-table"><tr><th>Date</th><th>Description</th><th>Amount</th><th>Type</th><th>Status</th></tr><tr><td colspan="5" class="empty-state">Loading...</td></tr></table></div></div>';
  let [list,sum]=await Promise.all([api('/api/v1/bnk/?limit=200'),api('/api/v1/bnk/summary')]);
  if(sum){
    document.getElementById('bank-kpis').innerHTML='<div class="kpi-card"><div class="kpi-label">Total Debit</div><div class="kpi-value" style="color:var(--green)">'+sum.total_debit+'</div></div><div class="kpi-card"><div class="kpi-label">Total Credit</div><div class="kpi-value" style="color:var(--red)">'+sum.total_credit+'</div></div><div class="kpi-card"><div class="kpi-label">Net</div><div class="kpi-value">'+(sum.total_debit-sum.total_credit).toFixed(2)+'</div></div>';
  }
  let tb=document.getElementById('bank-table');
  if(!list||list.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No transactions</td></tr>';return}
  tb.innerHTML=list.map(t=>'<tr><td>'+(t.trx_date||'—')+'</td><td>'+(t.description||t.trx_desc||'—')+'</td><td>'+(t.amount||'—')+'</td><td>'+(t.trx_type||'—')+'</td><td><span class="badge '+(t.status==='reconciled'?'badge-green':'badge-orange')+'">'+(t.status||'—')+'</span></td></tr>').join('');
}

/* ====================== PETTY CASH ====================== */
async function loadPettyCash(){
  let el=document.getElementById('pg-pettycash');
  el.innerHTML='<div class="pg-title">💵 Petty Cash <span class="sub">Petty cash vouchers</span></div><div class="kpi-grid" id="pc-kpis"></div><div class="card"><div class="table-wrap"><table><tr><th>Voucher</th><th>Date</th><th>Description</th><th>Amount</th><th>Category</th><th>Status</th></tr><tr><td colspan="6" class="empty-state">Loading...</td></tr></table></div></div>';
  let [list,stats]=await Promise.all([api('/api/v1/petty-cash/'),api('/api/v1/petty-cash/summary/stats')]);
  if(stats)document.getElementById('pc-kpis').innerHTML='<div class="kpi-card"><div class="kpi-label">Approved</div><div class="kpi-value" style="color:var(--green)">'+stats.total_approved+'</div></div><div class="kpi-card"><div class="kpi-label">Pending</div><div class="kpi-value" style="color:var(--orange)">'+stats.total_pending+'</div></div>';
  let tb=document.querySelector('#pg-pettycash table');
  if(!list||list.length===0){tb.innerHTML='<tr><td colspan="6" class="empty-state">No vouchers</td></tr>';return}
  tb.innerHTML=list.map(v=>'<tr><td><strong>'+v.voucher_no+'</strong></td><td>'+(v.voucher_date||'—')+'</td><td>'+(v.description||'—')+'</td><td>'+v.amount+'</td><td>'+(v.category||'—')+'</td><td><span class="badge '+(v.status==='approved'?'badge-green':'badge-orange')+'">'+v.status+'</span></td></tr>').join('');
}

/* ====================== CHEQUES ====================== */
async function loadCheques(){
  let el=document.getElementById('pg-cheques');
  el.innerHTML='<div class="pg-title">📝 Cheques <span class="sub">Cheque book tracking</span></div><div class="kpi-grid" id="chq-kpis"></div><div class="card"><div class="table-wrap"><table><tr><th>Cheque#</th><th>Payee</th><th>Amount</th><th>Bank</th><th>Status</th></tr><tr><td colspan="5" class="empty-state">Loading...</td></tr></table></div></div>';
  let [list,stats]=await Promise.all([api('/api/v1/cheques/'),api('/api/v1/cheques/summary/stats')]);
  if(stats)document.getElementById('chq-kpis').innerHTML='<div class="kpi-card"><div class="kpi-label">Issued</div><div class="kpi-value">'+stats.total_issued+'</div></div><div class="kpi-card"><div class="kpi-label">Cleared</div><div class="kpi-value" style="color:var(--green)">'+stats.total_cleared+'</div></div><div class="kpi-card"><div class="kpi-label">Outstanding</div><div class="kpi-value" style="color:var(--orange)">'+stats.total_outstanding+'</div></div>';
  let tb=document.querySelector('#pg-cheques table');
  if(!list||list.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No cheques</td></tr>';return}
  tb.innerHTML=list.map(c=>'<tr><td><strong>'+c.cheque_no+'</strong></td><td>'+(c.payee||'—')+'</td><td>'+c.amount+'</td><td>'+(c.bank_account||'—')+'</td><td><span class="badge '+(c.status==='cleared'?'badge-green':c.status==='issued'?'badge-orange':'badge-red')+'">'+c.status+'</span></td></tr>').join('');
}

/* ====================== WHT ====================== */
async function loadWHT(){
  let el=document.getElementById('pg-wht');
  el.innerHTML='<div class="pg-title">🧾 Withholding Tax <span class="sub">WHT certificates</span></div><div class="kpi-grid" id="wht-kpis"></div><div class="card"><div class="table-wrap"><table><tr><th>Certificate</th><th>Gross</th><th>WHT</th><th>Rate</th><th>Status</th></tr><tr><td colspan="5" class="empty-state">Loading...</td></tr></table></div></div>';
  let [list,stats]=await Promise.all([api('/api/v1/wht/'),api('/api/v1/wht/summary/stats')]);
  if(stats)document.getElementById('wht-kpis').innerHTML='<div class="kpi-card"><div class="kpi-label">Total WHT</div><div class="kpi-value" style="color:var(--red)">'+stats.total_wht+'</div></div><div class="kpi-card"><div class="kpi-label">Pending</div><div class="kpi-value" style="color:var(--orange)">'+stats.pending_wht+'</div></div>';
  let tb=document.querySelector('#pg-wht table');
  if(!list||list.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No WHT records</td></tr>';return}
  tb.innerHTML=list.map(w=>'<tr><td><strong>'+w.certificate_no+'</strong></td><td>'+w.gross_amount+'</td><td>'+w.wht_amount+'</td><td>'+(w.wht_rate||'—')+'%</td><td><span class="badge '+(w.status==='filed'?'badge-green':'badge-orange')+'">'+w.status+'</span></td></tr>').join('');
}

/* ====================== PIPELINE ====================== */
async function loadPipeline(){
  let el=document.getElementById('pg-pipeline');
  el.innerHTML='<div class="pg-title">🔄 Pipeline <span class="sub">8-stage ERP Builder Protocol</span></div><div id="pipe-body">Loading...</div>';
  let s=await api('/api/v2/status');
  if(!s)return;
  let stages=s.stages||{};
  el.innerHTML='<div class="pg-title">🔄 Pipeline <span class="sub">8-stage ERP Builder Protocol</span></div><div class="kpi-grid">'+Object.entries(stages).map(([k,v])=>'<div class="kpi-card"><div class="kpi-label">'+k.replace(/_/g,' ')+'</div><div class="kpi-value">'+v+'</div></div>').join('')+'</div><div class="card"><h3>Pipeline Flow</h3>'+['extract','validate','stage','reconcile','approve','promote','observe','journal'].map(st=>'<div style="display:inline-block;background:var(--surface2);padding:8px 14px;margin:4px;border-radius:4px;font-size:12px">'+st+'</div>').join('')+'</div>';
}

/* ====================== CURRENCY ====================== */
async function loadCurrency(){
  let el=document.getElementById('pg-currency');
  el.innerHTML='<div class="pg-title">💱 Currency Rates <span class="sub">Exchange rates to EGP</span></div><div class="card-actions"><button onclick="showCurrencyForm()">+ Add Rate</button></div><div class="card"><div class="table-wrap"><table><tr><th>Currency</th><th>Rate to EGP</th><th>Date</th></tr><tr><td colspan="3" class="empty-state">Loading...</td></tr></table></div></div>';
  let data=await api('/api/v1/currency/rates');
  let tb=document.querySelector('#pg-currency table');
  if(!data||data.length===0){tb.innerHTML='<tr><td colspan="3" class="empty-state">No rates</td></tr>';return}
  tb.innerHTML=data.map(c=>'<tr><td><strong>'+c.currency+'</strong></td><td>'+c.rate+'</td><td>'+(c.date||'—')+'</td></tr>').join('');
}
function showCurrencyForm(){
  let m=document.getElementById('modal-content');
  m.innerHTML='<h2>Add Currency Rate</h2><div class="form-group"><label>Currency Code</label><input id="f-cur-code" placeholder="USD" maxlength="3"></div><div class="form-group"><label>Rate to EGP</label><input id="f-cur-rate" type="number" step="0.01"></div><div class="form-group"><label>Date</label><input id="f-cur-date" type="date"></div><div class="modal-actions"><button class="btn-outline" onclick="closeModal()">Cancel</button><button class="success" onclick="saveCurrency()">Add</button></div>';
  document.getElementById('modal-overlay').classList.add('show');
}
async function saveCurrency(){
  let body={currency_code:document.getElementById('f-cur-code').value.toUpperCase(),rate_to_egp:parseFloat(document.getElementById('f-cur-rate').value)||0,rate_date:document.getElementById('f-cur-date').value||''};
  let r=await api('/api/v1/currency/rates',{method:'POST',body:JSON.stringify(body)});
  if(r){closeModal();loadCurrency()}
}

/* ====================== AUDIT ====================== */
async function loadAudit(){
  let el=document.getElementById('pg-audit');
  el.innerHTML='<div class="pg-title">📜 Audit Trail <span class="sub">All system changes</span></div><div class="card"><div class="table-wrap"><table><tr><th>Time</th><th>Action</th><th>Table</th><th>Record</th><th>User</th></tr><tr><td colspan="5" class="empty-state">Loading...</td></tr></table></div></div>';
  let data=await api('/api/v1/finance/audit?limit=100');
  let tb=document.querySelector('#pg-audit table');
  if(!data||data.length===0){tb.innerHTML='<tr><td colspan="5" class="empty-state">No audit records</td></tr>';return}
  tb.innerHTML=data.map(a=>'<tr><td style="font-size:11px;color:var(--muted)">'+(a.changed_at||'—')+'</td><td><span class="badge badge-blue">'+a.action+'</span></td><td>'+(a.table_name||'—')+'</td><td>'+(a.record_id||'—')+'</td><td>'+(a.changed_by||'—')+'</td></tr>').join('');
}

/* ====================== HEALTH ====================== */
async function loadHealth(){
  let el=document.getElementById('pg-health');
  el.innerHTML='<div class="pg-title">🔍 System Health</div><div id="health-body">Loading...</div>';
  let [h,r]=await Promise.all([api('/health'),api('/ready')]);
  if(!h)return;
  el.innerHTML='<div class="pg-title">🔍 System Health</div><div class="kpi-grid"><div class="kpi-card"><div class="kpi-label">Server</div><div class="kpi-value" style="color:var(--green)">'+h.status+'</div></div><div class="kpi-card"><div class="kpi-label">Version</div><div class="kpi-value">'+h.version+'</div></div><div class="kpi-card"><div class="kpi-label">Database</div><div class="kpi-value" style="color:'+(r&&r.status==='ready'?'var(--green)':'var(--red)')+'">'+(r?r.status:'—')+'</div></div></div>';
}

// Enter key on login
document.addEventListener('DOMContentLoaded',function(){
  document.getElementById('login-pass').addEventListener('keydown',function(e){if(e.key==='Enter')login()});
});
</script>
</body>
</html>'''
