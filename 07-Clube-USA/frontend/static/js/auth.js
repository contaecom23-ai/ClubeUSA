/* Shared auth utilities — no external dependencies */

const API = "";  // Same origin; change to full URL if backend is on a different port/domain

function getToken() {
  return sessionStorage.getItem("cu_token");
}

function setToken(token) {
  sessionStorage.setItem("cu_token", token);
}

function clearToken() {
  sessionStorage.removeItem("cu_token");
  sessionStorage.removeItem("cu_user");
}

function getUser() {
  try { return JSON.parse(sessionStorage.getItem("cu_user") || "null"); } catch { return null; }
}

function setUser(user) {
  sessionStorage.setItem("cu_user", JSON.stringify(user));
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = "/login.html";
    return false;
  }
  return true;
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(API + path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw Object.assign(new Error(data.detail || "Erro desconhecido"), { status: res.status, data });
  }
  return data;
}

function showAlert(el, msg, type = "error") {
  el.textContent = msg;
  el.className = `alert alert-${type} show`;
}

function hideAlert(el) {
  el.className = "alert";
}
