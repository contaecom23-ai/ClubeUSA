// Cliente para a API FastAPI do Clube USA
// Injeta automaticamente o token JWT do Supabase em cada requisição

const API_BASE = window.__API_BASE__ || "http://localhost:8000";

async function apiFetch(path, options = {}) {
  const token = await getAccessToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    // Token expirado — redireciona para login
    window.location.href = "/login.html";
    return null;
  }

  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body?.detail || `Erro ${res.status}`;
    throw new Error(detail);
  }
  return body;
}

async function getProfile() {
  return apiFetch("/api/profile");
}

async function updateProfile(data) {
  return apiFetch("/api/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}
