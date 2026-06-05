/* IHE-ERP Smart Dashboard — ApexCharts + html2pdf */
var charts = {};
var txData = [];

function randBetween(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }

var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

/* ===== KPI DATA ===== */
function loadKPI() {
    document.getElementById('kpiRevenue').textContent = 'EGP ' + (4850000).toLocaleString();
    document.getElementById('kpiEvents').textContent = '72';
    document.getElementById('kpiPending').textContent = '15';
    document.getElementById('kpiBank').textContent = 'EGP ' + (2100000).toLocaleString();
    document.getElementById('kpiClient').textContent = 'CISCO';
    document.getElementById('kpiVariance').textContent = '-8.3%';
}

/* ===== CHARTS ===== */
function initCharts() {
    /* Revenue Trend */
    charts.revenue = new ApexCharts(document.getElementById('revenueChart'), {
        chart: { type: 'area', height: 300, toolbar: { show: false }, foreColor: '#94a3b8' },
        series: [{ name: 'Revenue', data: [120,190,170,250,210,280,260,310,290,340,320,380] }],
        xaxis: { categories: months, labels: { style: { fontSize: '12px' } } },
        yaxis: { labels: { formatter: function(v) { return (v/1000).toFixed(0) + 'K'; } } },
        colors: ['#6366f1'],
        fill: { type: 'gradient', gradient: { shadeIntensity: .3, opacityFrom: .6, opacityTo: .1 } },
        stroke: { curve: 'smooth', width: 2 },
        grid: { borderColor: '#334155' },
        tooltip: { theme: 'dark' }
    });
    charts.revenue.render();

    /* Revenue by Client (Donut) */
    charts.clients = new ApexCharts(document.getElementById('clientChart'), {
        chart: { type: 'donut', height: 300, foreColor: '#94a3b8' },
        series: [42, 28, 18, 12],
        labels: ['CISCO', 'NVIDIA', 'Google', 'Microsoft'],
        colors: ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd'],
        legend: { position: 'bottom', fontSize: '12px', labels: { colors: '#94a3b8' } },
        dataLabels: { enabled: true, formatter: function(v) { return v.toFixed(1) + '%'; } },
        tooltip: { theme: 'dark' }
    });
    charts.clients.render();

    /* Bank Account Breakdown (Bar) */
    charts.bank = new ApexCharts(document.getElementById('bankChart'), {
        chart: { type: 'bar', height: 250, toolbar: { show: false }, foreColor: '#94a3b8' },
        series: [{ name: 'Balance', data: [1200000, 450000, 350000, 250000] }],
        xaxis: { categories: ['CIB EGP', 'HSBC USD', 'QNB EGP', 'AAIB EGP'], labels: { style: { fontSize: '11px' } } },
        colors: ['#22c55e'],
        plotOptions: { bar: { borderRadius: 6, horizontal: true } },
        grid: { borderColor: '#334155' },
        tooltip: { theme: 'dark' }
    });
    charts.bank.render();

    /* Event Pipeline (Bar) */
    charts.pipeline = new ApexCharts(document.getElementById('pipelineChart'), {
        chart: { type: 'bar', height: 250, stacked: true, toolbar: { show: false }, foreColor: '#94a3b8' },
        series: [
            { name: 'Upcoming', data: [12, 18, 8, 15, 10, 20] },
            { name: 'Completed', data: [8, 12, 5, 10, 7, 14] }
        ],
        xaxis: { categories: ['Jan-Feb', 'Mar-Apr', 'May-Jun', 'Jul-Aug', 'Sep-Oct', 'Nov-Dec'], labels: { style: { fontSize: '11px' } } },
        colors: ['#6366f1', '#22c55e'],
        legend: { position: 'bottom', fontSize: '11px', labels: { colors: '#94a3b8' } },
        grid: { borderColor: '#334155' },
        tooltip: { theme: 'dark' }
    });
    charts.pipeline.render();

    /* Transaction Velocity (Line) */
    charts.velocity = new ApexCharts(document.getElementById('velocityChart'), {
        chart: { type: 'line', height: 250, toolbar: { show: false }, foreColor: '#94a3b8' },
        series: [{ name: 'Transactions', data: [45, 52, 38, 61, 48, 55, 42, 58, 51, 63, 47, 56] }],
        xaxis: { categories: months, labels: { style: { fontSize: '11px' } } },
        colors: ['#f59e0b'],
        stroke: { curve: 'smooth', width: 2 },
        fill: { type: 'solid', opacity: .1 },
        markers: { size: 4, colors: ['#f59e0b'] },
        grid: { borderColor: '#334155' },
        tooltip: { theme: 'dark' }
    });
    charts.velocity.render();
}

/* ===== DATA TABLE ===== */
function generateTransactions() {
    txData = [];
    var accounts = ['CIB-1001', 'HSBC-2002', 'QNB-3003', 'AAIB-4004'];
    var types = ['Transfer', 'Payment', 'Deposit', 'Withdrawal', 'Fee'];
    var descs = ['Client payment - CISCO', 'Vendor payment - Venue', 'Transfer to savings', 'Salary disbursement', 'Service fee charge', 'Interest credit', 'Tax payment', 'Refund processing'];
    var statuses = ['Completed', 'Pending', 'Completed', 'Completed', 'Completed', 'Pending'];
    for (var i = 0; i < 25; i++) {
        var d = new Date(2026, randBetween(0,5), randBetween(1,28));
        var debit = Math.random() > 0.5 ? randBetween(10000, 500000) : 0;
        var credit = debit === 0 ? randBetween(10000, 500000) : 0;
        txData.push({
            date: d.toISOString().slice(0,10),
            account: accounts[randBetween(0,3)],
            type: types[randBetween(0,4)],
            desc: descs[randBetween(0,7)],
            debit: debit,
            credit: credit,
            balance: randBetween(100000, 5000000),
            status: statuses[randBetween(0,5)]
        });
    }
    txData.sort(function(a,b) { return b.date.localeCompare(a.date); });
    renderTable(txData);
}

function renderTable(data) {
    var body = document.getElementById('txBody');
    body.innerHTML = data.map(function(t) {
        var cls = t.status === 'Completed' ? 'status-ok' : 'status-pending';
        return '<tr><td>' + t.date + '</td><td>' + t.account + '</td><td>' + t.type + '</td><td>' + t.desc + '</td><td>' + (t.debit ? t.debit.toLocaleString() : '-') + '</td><td>' + (t.credit ? t.credit.toLocaleString() : '-') + '</td><td>' + t.balance.toLocaleString() + '</td><td><span class="' + cls + '">' + t.status + '</span></td></tr>';
    }).join('');
}

/* ===== SEARCH ===== */
document.addEventListener('DOMContentLoaded', function() {
    var search = document.getElementById('txSearch');
    if (search) {
        search.addEventListener('input', function() {
            var q = this.value.toLowerCase();
            var filtered = txData.filter(function(t) {
                return t.date.indexOf(q) !== -1 || t.account.toLowerCase().indexOf(q) !== -1 || t.type.toLowerCase().indexOf(q) !== -1 || t.desc.toLowerCase().indexOf(q) !== -1 || t.status.toLowerCase().indexOf(q) !== -1;
            });
            renderTable(filtered);
        });
    }
});

/* ===== EXPORT TABLE CSV ===== */
function exportTable() {
    var headers = ['Date','Account','Type','Description','Debit','Credit','Balance','Status'];
    var rows = txData.map(function(t) {
        return [t.date, t.account, t.type, '"' + t.desc + '"', t.debit, t.credit, t.balance, t.status];
    });
    var csv = '\uFEFF' + headers.join(',') + '\n' + rows.map(function(r) { return r.join(','); }).join('\n');
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    a.download = 'transactions_' + new Date().toISOString().slice(0,10) + '.csv';
    a.click();
}

/* ===== PERIOD SWITCH ===== */
function setPeriod(period, btn) {
    document.querySelectorAll('.chip').forEach(function(c) { c.classList.remove('active'); });
    btn.classList.add('active');
    var data = { monthly: [120,190,170,250,210,280,260,310,290,340,320,380], quarterly: [480,780,880,1040], yearly: [3200,3500,3800,4100,4500,4850] };
    var labels = { monthly: months, quarterly: ['Q1','Q2','Q3','Q4'], yearly: ['2021','2022','2023','2024','2025','2026'] };
    charts.revenue.updateOptions({ xaxis: { categories: labels[period] } });
    charts.revenue.updateSeries([{ data: data[period] }]);
}

/* ===== REFRESH ===== */
function refreshAll() {
    Object.keys(charts).forEach(function(k) { if (charts[k] && charts[k].destroy) charts[k].destroy(); });
    charts = {};
    loadKPI();
    initCharts();
    generateTransactions();
}

/* ===== PDF EXPORT ===== */
function exportPDF() {
    var el = document.getElementById('dashboardContent');
    html2pdf().from(el).set({ margin: [5,5,5,5], filename: 'dashboard.pdf', html2canvas: { scale: 2, useCORS: true }, jsPDF: { orientation: 'landscape', unit: 'mm', format: 'a4' } }).save();
}

/* ===== FULLSCREEN ===== */
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        if (document.exitFullscreen) document.exitFullscreen();
    }
}

/* ===== REPORT MODAL ===== */
function openReport() {
    document.getElementById('reportModal').classList.add('open');
}

function closeReport() {
    document.getElementById('reportModal').classList.remove('open');
}

function generatePreview() {
    var preview = document.getElementById('reportPreview');
    var type = document.getElementById('reportType').value;
    var titles = { financial: 'Financial Summary', events: 'Event Performance', bank: 'Bank Reconciliation', client: 'Client Analysis' };
    var tableData = {
        financial: [{label:'Total Revenue',val:'EGP 4,850,000'},{label:'Total Expenses',val:'EGP 3,200,000'},{label:'Net Profit',val:'EGP 1,650,000'},{label:'Gross Margin',val:'34.0%'}],
        events: [{label:'Active PNRs',val:'72'},{label:'Completed (YTD)',val:'45'},{label:'Avg Budget',val:'EGP 850,000'},{label:'Top Client',val:'CISCO (84 events)'}],
        bank: [{label:'Total Balance',val:'EGP 2,100,000'},{label:'CIB EGP',val:'EGP 1,200,000'},{label:'HSBC USD',val:'$450,000'},{label:'QNB EGP',val:'EGP 350,000'}],
        client: [{label:'Total Clients',val:'48'},{label:'Active Clients',val:'32'},{label:'Avg Revenue/Client',val:'EGP 101,042'},{label:'Top Client Share',val:'42%'}]
    };
    var rows = tableData[type] || tableData.financial;
    var html = '<h3 style="margin-bottom:12px;color:var(--ih-text)">' + titles[type] + '</h3>';
    html += '<table class="preview-table" style="width:100%"><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>';
    rows.forEach(function(r) { html += '<tr><td>' + r.label + '</td><td style="font-weight:600">' + r.val + '</td></tr>'; });
    html += '</tbody></table>';
    preview.innerHTML = html;
}

function exportReportPDF() {
    var preview = document.getElementById('reportPreview');
    html2pdf().from(preview).set({ margin: [10,10,10,10], filename: 'report.pdf', html2canvas: { scale: 2, useCORS: true } }).save();
}

/* ===== CLOSE MODAL ON OVERLAY CLICK ===== */
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) closeReport();
});

/* ===== INIT ===== */
document.addEventListener('DOMContentLoaded', function() {
    loadKPI();
    initCharts();
    generateTransactions();
});
