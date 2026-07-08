/**
 * Clube USA — Configuração do Frontend
 *
 * TODO (antes de lançar):
 *  1. Substitua SUPABASE_URL e SUPABASE_ANON_KEY pelos valores do seu projeto:
 *     https://app.supabase.com > Settings > API
 *
 *  2. Substitua API_BASE_URL pela URL do backend FastAPI em produção.
 *
 *  3. Configure no Supabase Dashboard:
 *     Authentication > URL Configuration
 *       Site URL:     https://clubeusa.com
 *       Redirect URLs: https://clubeusa.com/verify-email.html
 *
 * A SUPABASE_ANON_KEY é pública por design (protegida por RLS no banco).
 * NUNCA coloque a service_role key aqui.
 */
const CONFIG = {
  supabaseUrl: 'https://YOUR-PROJECT-ID.supabase.co',
  supabaseAnonKey: 'YOUR-SUPABASE-ANON-KEY',
  apiBaseUrl: 'http://localhost:8000',
};
