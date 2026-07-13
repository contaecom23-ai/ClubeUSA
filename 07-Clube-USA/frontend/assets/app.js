/* Clube USA — utilitários de frontend */

const API = '';  // mesmo origin; ajuste se backend estiver em outro domínio

// ── Auth helpers ──────────────────────────────────────────────────────────────

const Auth = {
  save(tokens) {
    localStorage.setItem('cu_access', tokens.access_token);
    localStorage.setItem('cu_refresh', tokens.refresh_token);
  },
  clear() {
    localStorage.removeItem('cu_access');
    localStorage.removeItem('cu_refresh');
  },
  getAccess()  { return localStorage.getItem('cu_access'); },
  getRefresh() { return localStorage.getItem('cu_refresh'); },
  isLoggedIn() { return !!Auth.getAccess(); },
};

// ── HTTP helpers ──────────────────────────────────────────────────────────────

async function apiFetch(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  const token = Auth.getAccess();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(API + path, { ...opts, headers });

  if (res.status === 401 && Auth.getRefresh()) {
    // Tentar renovar o token
    const refreshed = await fetch(API + '/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: Auth.getRefresh() }),
    });
    if (refreshed.ok) {
      Auth.save(await refreshed.json());
      headers['Authorization'] = `Bearer ${Auth.getAccess()}`;
      return fetch(API + path, { ...opts, headers });
    } else {
      Auth.clear();
      window.location.href = '/login.html';
      return;
    }
  }

  return res;
}

// ── UI helpers ────────────────────────────────────────────────────────────────

function showAlert(id, msg, type = 'error') {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `alert alert-${type} show`;
  el.textContent = msg;
}

function hideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.className = 'alert';
}

function setLoading(btnId, on) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = on;
  btn.classList.toggle('loading', on);
}

function getField(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : '';
}

// ── Logout ────────────────────────────────────────────────────────────────────

async function logout() {
  const refresh = Auth.getRefresh();
  if (refresh) {
    await apiFetch('/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refresh }),
    }).catch(() => {});
  }
  Auth.clear();
  window.location.href = '/login.html';
}

// ── Guard: redirecionar se não autenticado ────────────────────────────────────

function requireAuth() {
  if (!Auth.isLoggedIn()) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}
