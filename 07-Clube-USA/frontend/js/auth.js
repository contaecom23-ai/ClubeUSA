// Gerencia sessão Supabase no lado do cliente
// SUPABASE_URL e SUPABASE_ANON_KEY são injetados pela página HTML
// (anon key é segura no client — não tem acesso admin)

const SUPABASE_URL = window.__SUPABASE_URL__ || "";
const SUPABASE_ANON_KEY = window.__SUPABASE_ANON_KEY__ || "";

let _sb = null;

function getSupabase() {
  if (!_sb) {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
      throw new Error("Supabase não configurado. Defina window.__SUPABASE_URL__ e window.__SUPABASE_ANON_KEY__.");
    }
    _sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return _sb;
}

async function signUp(fullName, email, password) {
  const { data, error } = await getSupabase().auth.signUp({
    email,
    password,
    options: {
      data: { full_name: fullName },
      // URL para redirecionar após confirmação de email
      emailRedirectTo: window.location.origin + "/verify-email.html",
    },
  });
  return { data, error };
}

async function signIn(email, password) {
  const { data, error } = await getSupabase().auth.signInWithPassword({ email, password });
  return { data, error };
}

async function signOut() {
  await getSupabase().auth.signOut();
  window.location.href = "/login.html";
}

async function getSession() {
  const { data } = await getSupabase().auth.getSession();
  return data.session;
}

async function getAccessToken() {
  const session = await getSession();
  return session?.access_token || null;
}

// Redireciona para login se não estiver autenticado
async function requireAuth(redirectTo = "/login.html") {
  const session = await getSession();
  if (!session) {
    window.location.href = redirectTo;
    return null;
  }
  return session;
}

// Redireciona para perfil se já estiver autenticado
async function redirectIfAuthenticated(to = "/profile.html") {
  const session = await getSession();
  if (session) {
    window.location.href = to;
  }
}
