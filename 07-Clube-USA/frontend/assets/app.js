/**
 * Clube USA — utilitários compartilhados
 *
 * API_BASE: sobrescrito por config.js em produção.
 * Tokens: access_token e refresh_token em localStorage.
 * Rotas públicas: index, login, register, confirm.
 */

const API_BASE = window.API_BASE || "http://localhost:8000";

// ── Token storage ─────────────────────────────────────────────────────────────

const Auth = {
  save(tokens) {
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    localStorage.setItem("expires_at", Date.now() + tokens.expires_in * 1000);
  },
  getAccess()  { return localStorage.getItem("access_token"); },
  getRefresh() { return localStorage.getItem("refresh_token"); },
  isLoggedIn() { return !!Auth.getAccess(); },
  clear() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("expires_at");
  },
  logout() { Auth.clear(); window.location.href = "login.html"; },
};

// ── API helper ────────────────────────────────────────────────────────────────

async function apiRequest(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };

  if (options.auth) {
    const token = Auth.getAccess();
    if (!token) { Auth.logout(); return; }
    headers["Authorization"] = "Bearer " + token;
  }

  const resp = await fetch(API_BASE + path, {
    method: options.method || "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  // Token expirado: tenta refresh automático
  if (resp.status === 401 && options.auth) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      headers["Authorization"] = "Bearer " + Auth.getAccess();
      const retry = await fetch(API_BASE + path, {
        method: options.method || "GET",
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
      });
      return { ok: retry.ok, status: retry.status, data: await retry.json() };
    } else {
      Auth.logout();
      return;
    }
  }

  let data;
  try { data = await resp.json(); } catch { data = {}; }
  return { ok: resp.ok, status: resp.status, data };
}

async function tryRefresh() {
  const rt = Auth.getRefresh();
  if (!rt) return false;
  try {
    const resp = await fetch(API_BASE + "/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!resp.ok) return false;
    const tokens = await resp.json();
    Auth.save(tokens);
    return true;
  } catch { return false; }
}

// ── UI helpers ────────────────────────────────────────────────────────────────

function showAlert(el, message, type = "danger") {
  el.className = `alert alert-${type}`;
  el.textContent = message;
  el.style.display = "block";
}

function hideAlert(el) { el.style.display = "none"; }

function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.textContent = loading ? "Aguarde..." : btn.dataset.label;
}

// ── Auth guard (páginas protegidas) ──────────────────────────────────────────

function requireAuth() {
  if (!Auth.isLoggedIn()) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}

// ── Parse hash tokens (usado na tela de confirmação) ─────────────────────────

function parseHashTokens() {
  const hash = window.location.hash.substring(1);
  const params = new URLSearchParams(hash);
  const access_token  = params.get("access_token");
  const refresh_token = params.get("refresh_token");
  const expires_in    = parseInt(params.get("expires_in") || "3600", 10);
  const error         = params.get("error_description") || params.get("error");
  return { access_token, refresh_token, expires_in, error };
}
