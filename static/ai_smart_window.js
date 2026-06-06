/**
 * IHE-ERP AI Smart Window v1.0
 * Embeddable widget for all ERP forms
 * Usage: <script src="/static/ai_smart_window.js" data-context="Event Form"></script>
 */
(function() {
  'use strict';
  
  const CONFIG = {
    apiEndpoint: '/api/ai/ask',
    position: 'bottom-right',
    theme: 'dark',
    autoOpen: false,
    context: document.currentScript?.getAttribute('data-context') || 'ERP'
  };

  const style = document.createElement('style');
  style.textContent = `
    .ai-sw { position:fixed; bottom:24px; right:24px; width:380px; max-height:600px; 
      background:#1e293b; border:1px solid #334155; border-radius:16px; 
      box-shadow:0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(99,102,241,0.3);
      display:flex; flex-direction:column; overflow:hidden; z-index:9999;
      font-family:'Segoe UI',system-ui,sans-serif; transition:all 0.3s; }
    .ai-sw.collapsed { width:56px; height:56px; border-radius:50%; }
    .ai-sw.collapsed .ai-sw-h,.ai-sw.collapsed .ai-sw-b,.ai-sw.collapsed .ai-sw-i { display:none; }
    .ai-sw-h { display:flex; align-items:center; gap:10px; padding:14px 16px;
      background:linear-gradient(135deg,#6366f1,#8b5cf6); cursor:pointer; }
    .ai-sw-o { width:28px; height:28px; border-radius:50%;
      background:radial-gradient(circle at 30% 30%,#a5b4fc,#6366f1);
      box-shadow:0 0 12px rgba(99,102,241,0.3); animation:aiOrb 2s ease-in-out infinite; }
    @keyframes aiOrb { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.15);opacity:.8} }
    .ai-sw-t { flex:1; font-weight:600; font-size:14px; color:white; letter-spacing:.3px; }
    .ai-sw-s { width:8px; height:8px; border-radius:50%; background:#22c55e;
      box-shadow:0 0 6px #22c55e; animation:aiStat 3s ease-in-out infinite; }
    @keyframes aiStat { 0%,100%{opacity:1} 50%{opacity:.4} }
    .ai-sw-x { background:none; border:none; color:white; font-size:18px; cursor:pointer;
      width:28px; height:28px; display:flex; align-items:center; justify-content:center;
      border-radius:6px; transition:background .2s; }
    .ai-sw-x:hover { background:rgba(255,255,255,.15); }
    .ai-sw-b { flex:1; overflow-y:auto; padding:12px; display:flex; flex-direction:column; gap:10px; min-height:200px; }
    .ai-sw-b::-webkit-scrollbar { width:4px; }
    .ai-sw-b::-webkit-scrollbar-thumb { background:#334155; border-radius:2px; }
    .ai-sw-m { max-width:90%; padding:10px 14px; border-radius:12px; font-size:13px; line-height:1.5; animation:aiMsg .3s ease-out; }
    @keyframes aiMsg { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
    .ai-sw-m.u { align-self:flex-end; background:#6366f1; color:white; border-bottom-right-radius:4px; }
    .ai-sw-m.b { align-self:flex-start; background:#0f172a; border:1px solid #334155; border-bottom-left-radius:4px; color:#e2e8f0; }
    .ai-sw-c { display:flex; flex-wrap:wrap; gap:6px; padding:0 4px; }
    .ai-sw-p { background:rgba(99,102,241,.15); border:1px solid rgba(99,102,241,.3);
      color:#a5b4fc; padding:5px 12px; border-radius:20px; font-size:11px;
      cursor:pointer; transition:all .2s; white-space:nowrap; }
    .ai-sw-p:hover { background:rgba(99,102,241,.3); border-color:#6366f1; }
    .ai-sw-i { padding:12px; border-top:1px solid #334155; display:flex; gap:8px; align-items:flex-end; }
    .ai-sw-in { flex:1; background:#0f172a; border:1px solid #334155; border-radius:10px;
      padding:10px 14px; color:#e2e8f0; font-size:13px; resize:none; min-height:40px;
      max-height:100px; outline:none; font-family:inherit; }
    .ai-sw-in:focus { border-color:#6366f1; }
    .ai-sw-sn { width:40px; height:40px; border-radius:10px;
      background:linear-gradient(135deg,#6366f1,#8b5cf6); border:none; color:white;
      cursor:pointer; display:flex; align-items:center; justify-content:center;
      transition:transform .2s; flex-shrink:0; }
    .ai-sw-sn:hover { transform:scale(1.05); }
    .ai-sw-ctx { position:absolute; top:-10px; left:16px; background:#f59e0b; color:#1e293b;
      font-size:10px; font-weight:700; padding:2px 10px; border-radius:10px;
      text-transform:uppercase; letter-spacing:.5px; }
  `;
  document.head.appendChild(style);

  const container = document.createElement('div');
  container.className = 'ai-sw';
  container.id = 'aiSmartWindow';
  container.innerHTML = `
    <div class="ai-sw-ctx">${CONFIG.context}</div>
    <div class="ai-sw-h" onclick="aiToggle()">
      <div class="ai-sw-o"></div>
      <span class="ai-sw-t">IHE AI</span>
      <div class="ai-sw-s"></div>
      <button class="ai-sw-x" onclick="event.stopPropagation();aiToggle()">\u2212</button>
    </div>
    <div class="ai-sw-b" id="aiSwBody"></div>
    <div class="ai-sw-i">
      <textarea class="ai-sw-in" id="aiSwInput" placeholder="Ask AI..." rows="1" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();aiSend()}"></textarea>
      <button class="ai-sw-sn" onclick="aiSend()">\u2794</button>
    </div>
  `;
  document.body.appendChild(container);

  let collapsed = false;
  const body = document.getElementById('aiSwBody');
  const input = document.getElementById('aiSwInput');

  window.aiToggle = function() {
    collapsed = !collapsed;
    container.classList.toggle('collapsed', collapsed);
    container.querySelector('.ai-sw-x').textContent = collapsed ? '+' : '\u2212';
  };

  window.aiSend = async function(text) {
    const msg = text || input.value.trim();
    if (!msg) return;
    if (!text) input.value = '';
    
    addMsg(msg, true);
    showTyping();
    
    try {
      const res = await fetch(CONFIG.apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: msg, context: CONFIG.context })
      });
      const data = await res.json();
      hideTyping();
      addMsg(data.answer || data.response || 'No response from AI engine.', false);
    } catch (err) {
      hideTyping();
      addMsg('⚠ AI service unavailable. Check connection or try again.', false);
    }
  };

  function addMsg(text, isUser) {
    const m = document.createElement('div');
    m.className = 'ai-sw-m ' + (isUser ? 'u' : 'b');
    m.innerHTML = text;
    body.appendChild(m);
    body.scrollTop = body.scrollHeight;
  }

  function showTyping() {
    const t = document.createElement('div');
    t.className = 'ai-sw-m b';
    t.id = 'aiSwTyping';
    t.innerHTML = '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#94a3b8;margin:0 2px;animation:aiOrb 1.4s infinite"></span><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#94a3b8;margin:0 2px;animation:aiOrb 1.4s .2s infinite"></span><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#94a3b8;margin:0 2px;animation:aiOrb 1.4s .4s infinite"></span>';
    body.appendChild(t);
    body.scrollTop = body.scrollHeight;
  }

  function hideTyping() {
    const t = document.getElementById('aiSwTyping');
    if (t) t.remove();
  }

  addMsg('Welcome to <strong>' + CONFIG.context + '</strong>. How can I assist you today?', false);

  document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === '/') { e.preventDefault(); aiToggle(); }
  });
})();
