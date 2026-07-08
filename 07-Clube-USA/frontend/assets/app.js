/**
 * Shared utilities for Clube USA frontend.
 *
 * Auth tokens are stored in localStorage. Access token has a ~1h TTL (Supabase default);
 * the app auto-refreshes it using the refresh token (7-day TTL) before it expires.
 * Trade-off acknowledged: localStorage is vulnerable to XSS. Mitigation: strict CSP
 * in production, all user content escaped, no innerHTML with user data.
 */

const API_BASE = window.CLUBE_API || "/api/v1";

// ── Token management ─────────────────────────────────────────────────────────

function saveSession(data) {
  localStorage.setItem("clubeusa_access", data.access_token);
  localStorage.setItem("clubeusa_refresh", data.refresh_token);
  if (data.user) {
    localStorage.setItem("clubeusa_user", JSON.stringify(data.user));
  }
}

function clearSession() {
  ["clubeusa_access", "clubeusa_refresh", "clubeusa_user"].forEach(k =>
    localStorage.removeItem(k)
  );
}

function getAccessToken() {
  return localStorage.getItem("clubeusa_access");
}

function getRefreshToken() {
  return localStorage.getItem("clubeusa_refresh");
}

function isLoggedIn() {
  return Boolean(getAccessToken());
}

function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = "/login.html?next=" + encodeURIComponent(window.location.pathname);
  }
}

function requireGuest() {
  if (isLoggedIn()) {
    window.location.href = "/profile.html";
  }
}

// ── HTTP helpers ─────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const token = getAccessToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: "Bearer " + token } : {}),
    ...(options.headers || {}),
  };

  let resp = await fetch(API_BASE + path, { ...options, headers });

  // Auto-refresh on 401
  if (resp.status === 401 && getRefreshToken()) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      headers.Authorization = "Bearer " + getAccessToken();
      resp = await fetch(API_BASE + path, { ...options, headers });
    }
  }

  return resp;
}

async function tryRefresh() {
  const rt = getRefreshToken();
  if (!rt) return false;
  try {
    const resp = await fetch(API_BASE + "/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!resp.ok) {
      clearSession();
      return false;
    }
    const data = await resp.json();
    localStorage.setItem("clubeusa_access", data.access_token);
    localStorage.setItem("clubeusa_refresh", data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// ── UI helpers ───────────────────────────────────────────────────────────────

function showAlert(el, msg, type = "error") {
  el.textContent = msg;
  el.className = `alert alert-${type} visible`;
}

function hideAlert(el) {
  el.className = "alert";
}

function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.dataset.original = btn.dataset.original || btn.textContent;
  btn.textContent = loading ? "Aguarde…" : btn.dataset.original;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function togglePassword(inputId, btnEl) {
  const input = document.getElementById(inputId);
  if (input.type === "password") {
    input.type = "text";
    btnEl.textContent = "🙈";
  } else {
    input.type = "password";
    btnEl.textContent = "👁";
  }
}
