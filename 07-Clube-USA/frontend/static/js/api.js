/**
 * Clube USA — API client
 * Centraliza chamadas ao backend. Tokens armazenados em sessionStorage
 * (escolha intencional para MVP: melhor que localStorage, mas não tão
 * seguro quanto httpOnly cookie — trade-off documentado para 1k usuários).
 */

const API_BASE = (typeof API_URL !== 'undefined') ? API_URL : 'http://localhost:8000';

const TOKEN_KEY = 'clubeusa_access';
const REFRESH_KEY = 'clubeusa_refresh';

export const Auth = {
  setTokens(access, refresh) {
    sessionStorage.setItem(TOKEN_KEY, access);
    sessionStorage.setItem(REFRESH_KEY, refresh);
  },
  clearTokens() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
  },
  getAccess() { return sessionStorage.getItem(TOKEN_KEY); },
  getRefresh() { return sessionStorage.getItem(REFRESH_KEY); },
  isLoggedIn() { return !!this.getAccess(); },
};

async function _request(method, path, body = null, auth = false) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const token = Auth.getAccess();
    if (!token) throw new Error('Não autenticado');
    headers['Authorization'] = `Bearer ${token}`;
  }

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, opts);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data.detail || data.message || 'Erro desconhecido';
    throw new Error(msg);
  }
  return data;
}

export const API = {
  register: (body) => _request('POST', '/api/auth/register', body),
  confirmEmail: (token) => _request('POST', '/api/auth/confirm-email', { token }),
  login: async (body) => {
    const data = await _request('POST', '/api/auth/login', body);
    Auth.setTokens(data.access_token, data.refresh_token);
    return data;
  },
  logout: async () => {
    const refresh = Auth.getRefresh();
    if (refresh) {
      await _request('POST', '/api/auth/logout', { refresh_token: refresh }).catch(() => {});
    }
    Auth.clearTokens();
  },
  getProfile: () => _request('GET', '/api/profile/me', null, true),
  updateProfile: (body) => _request('PUT', '/api/profile/me', body, true),
};
