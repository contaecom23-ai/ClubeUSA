// Clube USA — shared auth utilities
const API = window.CLUBE_API_URL || "http://localhost:8000";

function showMsg(el, text, type) {
  el.textContent = text;
  el.className = `msg ${type} show`;
}

function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.textContent = loading ? "Aguarde..." : btn.dataset.label;
}

function saveTokens(access, refresh) {
  localStorage.setItem("cu_access", access);
  localStorage.setItem("cu_refresh", refresh);
}

function getAccessToken() {
  return localStorage.getItem("cu_access");
}

function clearTokens() {
  localStorage.removeItem("cu_access");
  localStorage.removeItem("cu_refresh");
}

async function apiFetch(path, opts = {}) {
  const token = getAccessToken();
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...opts, headers });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

async function tryRefresh() {
  const rt = localStorage.getItem("cu_refresh");
  if (!rt) return false;
  const { ok, data } = await apiFetch("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: rt }),
  });
  if (ok) { saveTokens(data.access_token, data.refresh_token); return true; }
  clearTokens();
  return false;
}
