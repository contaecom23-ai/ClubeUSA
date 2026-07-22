/**
 * Clube USA — cliente de API + helpers de autenticação.
 * Tokens armazenados em localStorage. Em produção, considerar httpOnly cookies.
 */

const API_BASE = window.CLUBE_USA_API_URL || "http://localhost:8000";

// ── Storage ────────────────────────────────────────────────────────────────

const storage = {
  setTokens(access, refresh) {
    localStorage.setItem("cu_access", access);
    localStorage.setItem("cu_refresh", refresh);
  },
  getAccess() { return localStorage.getItem("cu_access"); },
  getRefresh() { return localStorage.getItem("cu_refresh"); },
  clear() {
    localStorage.removeItem("cu_access");
    localStorage.removeItem("cu_refresh");
  },
  isLoggedIn() { return !!this.getAccess(); },
};

// ── HTTP ───────────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}, retry = true) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = storage.getAccess();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (resp.status === 401 && retry) {
    // Tentar refresh silencioso
    const refreshed = await tryRefresh();
    if (refreshed) return apiFetch(path, options, false);
    storage.clear();
    redirectToLogin();
    return null;
  }

  return resp;
}

async function tryRefresh() {
  const rt = storage.getRefresh();
  if (!rt) return false;
  try {
    const resp = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!resp.ok) return false;
    const data = await resp.json();
    storage.setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// ── Auth API ───────────────────────────────────────────────────────────────

const auth = {
  async register(email, password, fullName) {
    const resp = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    return { ok: resp.ok, data: await resp.json(), status: resp.status };
  },

  async login(email, password) {
    const resp = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await resp.json();
    if (resp.ok) {
      storage.setTokens(data.access_token, data.refresh_token);
    }
    return { ok: resp.ok, data, status: resp.status };
  },

  async logout() {
    const rt = storage.getRefresh();
    if (rt) {
      await apiFetch("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: rt }),
      }).catch(() => {});
    }
    storage.clear();
    redirectToLogin();
  },
};

// ── User API ───────────────────────────────────────────────────────────────

const users = {
  async me() {
    const resp = await apiFetch("/api/me");
    if (!resp) return null;
    return resp.ok ? resp.json() : null;
  },

  async updateProfile(profile) {
    const resp = await apiFetch("/api/me/profile", {
      method: "PUT",
      body: JSON.stringify(profile),
    });
    if (!resp) return { ok: false, data: null };
    return { ok: resp.ok, data: await resp.json() };
  },
};

// ── Navigation ─────────────────────────────────────────────────────────────

function redirectToLogin() {
  if (!window.location.pathname.includes("login")) {
    window.location.href = "/login.html";
  }
}

function requireAuth() {
  if (!storage.isLoggedIn()) {
    redirectToLogin();
    return false;
  }
  return true;
}

// ── UI Helpers ─────────────────────────────────────────────────────────────

function showAlert(elementId, message, type = "error") {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = message;
  el.className = `alert alert-${type} show`;
}

function hideAlert(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.className = "alert";
}

function setLoading(btnId, spinnerId, loading) {
  const btn = document.getElementById(btnId);
  const spinner = document.getElementById(spinnerId);
  if (btn) btn.disabled = loading;
  if (spinner) spinner.className = loading ? "spinner show" : "spinner";
}
