// Thin API client — talks only to FastAPI backend, never directly to Supabase.
const API_BASE = "http://localhost:8000";
const TOKEN_KEY = "clubeusa_token";

const api = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (t) => localStorage.setItem(TOKEN_KEY, t),
  clearToken: () => localStorage.removeItem(TOKEN_KEY),

  isLoggedIn: () => !!localStorage.getItem(TOKEN_KEY),

  async request(path, { method = "GET", body, auth = false } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth) {
      const token = api.getToken();
      if (!token) { api.redirectToLogin(); return; }
      headers["Authorization"] = `Bearer ${token}`;
    }
    const resp = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      const msg = data.detail || "Erro inesperado. Tente novamente.";
      throw new Error(Array.isArray(msg) ? msg.map(e => e.msg).join("; ") : msg);
    }
    return data;
  },

  redirectToLogin: () => { window.location.href = "/login.html"; },
  redirectToProfile: () => { window.location.href = "/profile.html"; },
};
