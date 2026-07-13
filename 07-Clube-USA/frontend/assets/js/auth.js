/**
 * Auth helpers shared across all pages.
 * Reads API_URL from window.APP_CONFIG set inline in each HTML page.
 */

const API = window.APP_CONFIG?.api_url || "http://localhost:8000";

// ── Storage ──────────────────────────────────────────────────────────────────

function saveTokens(accessToken, refreshToken) {
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
}

function getAccessToken() {
  return localStorage.getItem("access_token");
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

// ── API helpers ──────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const url = `${API}${path}`;
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getAccessToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(url, { ...options, headers });

  if (resp.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${getAccessToken()}`;
      return fetch(url, { ...options, headers });
    }
    clearTokens();
    redirectToLogin();
    return resp;
  }
  return resp;
}

async function tryRefresh() {
  const rt = localStorage.getItem("refresh_token");
  if (!rt) return false;
  try {
    const resp = await fetch(`${API}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!resp.ok) return false;
    const data = await resp.json();
    saveTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

function redirectToLogin() {
  if (!window.location.pathname.endsWith("login.html")) {
    window.location.href = "login.html";
  }
}

// ── Auth guards ──────────────────────────────────────────────────────────────

function requireAuth() {
  if (!getAccessToken()) redirectToLogin();
}

function redirectIfLoggedIn() {
  if (getAccessToken()) window.location.href = "profile.html";
}

// ── UI helpers ───────────────────────────────────────────────────────────────

function showAlert(el, message, type = "error") {
  el.textContent = message;
  el.className = `alert alert-${type} show`;
}

function hideAlert(el) {
  el.className = "alert";
}

function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.textContent = loading ? "Aguarde..." : btn.dataset.label;
}

// ── Register ─────────────────────────────────────────────────────────────────

async function handleRegister(e) {
  e.preventDefault();
  const form = e.target;
  const alert = document.getElementById("alert");
  const btn = form.querySelector("button[type=submit]");

  hideAlert(alert);
  setLoading(btn, true);

  try {
    const resp = await fetch(`${API}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: form.email.value.trim(),
        password: form.password.value,
        full_name: form.full_name.value.trim(),
      }),
    });

    const data = await resp.json();
    if (!resp.ok) {
      const detail = data.detail;
      const msg = typeof detail === "string" ? detail : (detail?.[0]?.msg || "Erro ao cadastrar");
      showAlert(alert, msg, "error");
    } else {
      showAlert(alert, data.message, "success");
      form.reset();
    }
  } catch {
    showAlert(alert, "Erro de conexao. Tente novamente.", "error");
  } finally {
    setLoading(btn, false);
  }
}

// ── Login ─────────────────────────────────────────────────────────────────────

async function handleLogin(e) {
  e.preventDefault();
  const form = e.target;
  const alert = document.getElementById("alert");
  const btn = form.querySelector("button[type=submit]");

  hideAlert(alert);
  setLoading(btn, true);

  try {
    const resp = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: form.email.value.trim(),
        password: form.password.value,
      }),
    });

    const data = await resp.json();
    if (!resp.ok) {
      showAlert(alert, data.detail || "Email ou senha incorretos", "error");
    } else {
      saveTokens(data.access_token, data.refresh_token);
      window.location.href = "profile.html";
    }
  } catch {
    showAlert(alert, "Erro de conexao. Tente novamente.", "error");
  } finally {
    setLoading(btn, false);
  }
}

// ── Confirm email ─────────────────────────────────────────────────────────────

async function handleConfirmEmail() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  const statusEl = document.getElementById("status");

  if (!token) {
    showAlert(statusEl, "Token nao encontrado na URL.", "error");
    return;
  }

  try {
    const resp = await fetch(`${API}/auth/confirm-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    const data = await resp.json();
    if (resp.ok) {
      showAlert(statusEl, data.message + " Voce ja pode fazer login.", "success");
    } else {
      showAlert(statusEl, data.detail || "Erro ao confirmar email.", "error");
    }
  } catch {
    showAlert(statusEl, "Erro de conexao.", "error");
  }
}

// ── Logout ────────────────────────────────────────────────────────────────────

function logout() {
  clearTokens();
  window.location.href = "login.html";
}
