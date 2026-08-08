// Clube USA — utilitários compartilhados do frontend
const API_URL = window.CLUBE_USA_API_URL || "http://localhost:8000";

const Auth = {
  getToken() { return localStorage.getItem("cu_token"); },
  setToken(t) { localStorage.setItem("cu_token", t); },
  clear() { localStorage.removeItem("cu_token"); },
  isLoggedIn() { return !!this.getToken(); },
};

async function apiCall(method, path, body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = Auth.getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, detail: data.detail || "Erro desconhecido." };
  return data;
}

function showAlert(el, msg, type = "error") {
  el.textContent = msg;
  el.className = `alert alert-${type} show`;
}

function hideAlert(el) {
  el.className = "alert";
}

function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.textContent = loading ? "Aguarde..." : btn.dataset.label;
}

// Redireciona para login se não estiver autenticado
function requireAuth() {
  if (!Auth.isLoggedIn()) {
    window.location.href = "/login.html";
  }
}

// Redireciona para perfil se já estiver autenticado
function redirectIfAuth() {
  if (Auth.isLoggedIn()) {
    window.location.href = "/profile.html";
  }
}
