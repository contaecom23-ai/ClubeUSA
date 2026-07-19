/**
 * Camada de comunicação com a API Clube USA.
 * O BASE_URL deve apontar para onde o backend FastAPI está rodando.
 * Em produção, substituir pela URL real (sem trailing slash).
 */
const BASE_URL = window.CLUBE_API_URL || "http://localhost:8000";

// ── Token storage ────────────────────────────────────────────────────────────
const Auth = {
  setTokens(access, refresh) {
    sessionStorage.setItem("access_token", access);
    sessionStorage.setItem("refresh_token", refresh);
  },
  getAccess() { return sessionStorage.getItem("access_token"); },
  getRefresh() { return sessionStorage.getItem("refresh_token"); },
  clear() {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
  },
  isLoggedIn() { return !!this.getAccess(); },
};

// ── HTTP helper ──────────────────────────────────────────────────────────────
async function apiCall(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };

  const token = Auth.getAccess();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    const msg = data.detail || "Erro desconhecido. Tente novamente.";
    throw new Error(Array.isArray(msg) ? msg.map(e => e.msg).join("; ") : msg);
  }

  return data;
}

// ── Auth API ─────────────────────────────────────────────────────────────────
const ClubeAPI = {
  async register(email, password, fullName) {
    return apiCall("/auth/register", {
      method: "POST",
      body: { email, password, full_name: fullName },
    });
  },

  async login(email, password) {
    const data = await apiCall("/auth/login", {
      method: "POST",
      body: { email, password },
    });
    Auth.setTokens(data.access_token, data.refresh_token);
    return data;
  },

  async verifyEmail(tokenHash, type = "email") {
    return apiCall("/auth/verify-email", {
      method: "POST",
      body: { token_hash: tokenHash, type },
    });
  },

  async resendVerification(email) {
    return apiCall("/auth/resend-verification", {
      method: "POST",
      body: { email },
    });
  },

  async getProfile() {
    return apiCall("/users/me");
  },

  async updateProfile(fields) {
    return apiCall("/users/me", { method: "PATCH", body: fields });
  },

  logout() {
    Auth.clear();
    window.location.href = "/login.html";
  },
};

// ── UI helpers ───────────────────────────────────────────────────────────────
function showAlert(id, msg, type = "error") {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `alert ${type} show`;
}

function hideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.className = "alert";
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading ? "Aguarde..." : btn.dataset.label;
}

function requireAuth() {
  if (!Auth.isLoggedIn()) window.location.href = "/login.html";
}
