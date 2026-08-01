// API client — Clube USA
// Todas as chamadas passam por aqui para centralizar auth e tratamento de erros.

const API_BASE = window.CLUBE_API_BASE || "http://localhost:8000";

const TOKEN_KEY  = "cusa_access";
const REFRESH_KEY = "cusa_refresh";

// --- Token storage (localStorage — aceitável para SPA simples) ---
const auth = {
  getAccess:  ()  => localStorage.getItem(TOKEN_KEY),
  getRefresh: ()  => localStorage.getItem(REFRESH_KEY),
  setTokens:  (a, r) => {
    localStorage.setItem(TOKEN_KEY, a);
    localStorage.setItem(REFRESH_KEY, r);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
  isLoggedIn: () => !!localStorage.getItem(TOKEN_KEY),
};

// --- Fetch wrapper com refresh automático ---
async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const token = auth.getAccess();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let resp = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // Token expirado? Tenta refresh uma vez
  if (resp.status === 401 && auth.getRefresh()) {
    const refreshed = await _tryRefresh();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${auth.getAccess()}`;
      resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
    } else {
      auth.clear();
      window.location.href = "/login.html";
      return null;
    }
  }

  return resp;
}

async function _tryRefresh() {
  try {
    const resp = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: auth.getRefresh() }),
    });
    if (!resp.ok) return false;
    const data = await resp.json();
    auth.setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// --- Helpers para erro humanizado ---
async function apiError(resp) {
  try {
    const body = await resp.json();
    return body.detail || "Erro desconhecido.";
  } catch {
    return `Erro ${resp.status}.`;
  }
}

// --- API calls ---
const api = {
  register: (data) =>
    apiFetch("/auth/register", { method: "POST", body: JSON.stringify(data) }),

  login: async (email, password) => {
    const resp = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    if (resp && resp.ok) {
      const data = await resp.json();
      auth.setTokens(data.access_token, data.refresh_token);
    }
    return resp;
  },

  confirmEmail: (token) =>
    apiFetch(`/auth/confirm-email?token=${encodeURIComponent(token)}`),

  logout: async () => {
    const rt = auth.getRefresh();
    if (rt) {
      await apiFetch("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: rt }),
      }).catch(() => {});
    }
    auth.clear();
    window.location.href = "/login.html";
  },

  getMe: () => apiFetch("/users/me"),

  updateMe: (data) =>
    apiFetch("/users/me", { method: "PUT", body: JSON.stringify(data) }),
};

// Exporta para uso nos scripts inline
window.api   = api;
window.auth  = auth;
window.apiError = apiError;
