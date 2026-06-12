(function () {
  'use strict';

  function getToken() {
    return localStorage.getItem('token');
  }

  function apiHeaders() {
    const h = { 'Content-Type': 'application/json' };
    const t = getToken();
    if (t) h['Authorization'] = 'Bearer ' + t;
    return h;
  }

  async function apiFetch(url, opts) {
    opts = opts || {};
    opts.headers = { ...apiHeaders(), ...(opts.headers || {}) };
    const res = await fetch(url, opts);
    if (res.status === 401 && !url.includes('/auth/login')) {
      localStorage.removeItem('token');
      window.location.href = '/auth/login';
      return null;
    }
    return res;
  }

  async function checkAuth() {
    if (!getToken()) {
      if (!window.location.pathname.startsWith('/auth/')) {
        window.location.href = '/auth/login';
      }
      return;
    }
    try {
      const res = await apiFetch('/auth/me');
      if (res && res.ok) {
        const user = await res.json();
        document.querySelectorAll('.user-name').forEach(el => el.textContent = user.full_name || user.user_id);
      }
    } catch (_) {}
  }

  function pollBridgeStatus() {
    const el = document.getElementById('bridge-status');
    if (!el) return;
    async function poll() {
      try {
        const res = await fetch('/api/v1/bridge/status');
        const data = await res.json();
        const configured = data.bio_erp_configured;
        el.innerHTML = configured
          ? '<span class="badge bg-success">Bridge Connected</span>'
          : '<span class="badge bg-warning text-dark">Bridge Standalone</span>';
      } catch (_) {
        el.innerHTML = '<span class="badge bg-danger">Bridge Offline</span>';
      }
    }
    poll();
    setInterval(poll, 30000);
  }

  document.addEventListener('DOMContentLoaded', function () {
    checkAuth();
    pollBridgeStatus();
  });

  window.EventCore = { getToken, apiFetch, checkAuth };
})();
