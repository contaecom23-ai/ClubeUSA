# Clube USA — Setup pendente (pós-migration)

O banco Supabase já está criado e todas as migrations já rodaram (21 tabelas, projeto "clube usa", ref `susnhkgrejvyhdhoyeev`). Falta só isto:

## 1. Copiar as chaves do Supabase para o `.env` local

Painel já está aberto em: Settings → API Keys → aba "Legacy anon, service_role API keys"

Copie os valores dos botões **Copy** de `anon` e `service_role` e cole em `07-Clube-USA/clubeusa/.env`:

```
SUPABASE_URL=https://susnhkgrejvyhdhoyeev.supabase.co
SUPABASE_ANON_KEY=<cole aqui>
SUPABASE_SERVICE_KEY=<cole aqui>
```

## 2. Gerar chaves de segurança novas

No terminal, dentro de `07-Clube-USA/clubeusa`:

```bash
python utils/security.py
```

Cole a saída (`ENCRYPTION_KEY` e `JWT_SECRET`) no `.env`.

## 3. Criar o serviço no Render

1. https://render.com → New → Blueprint
2. Conectar o repositório Git do projeto
3. Apontar para `07-Clube-USA/clubeusa/render.yaml`
4. Isso cria automaticamente 2 serviços: `clubeusa-api` (web) e `clubeusa-scheduler` (worker)
5. No painel do Render, preencher o grupo de variáveis `clubeusa-secrets`:
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` (mesmas do passo 1)
   - `ENCRYPTION_KEY`, `JWT_SECRET` (do passo 2)
   - `ADMIN_SECRET` (defina uma senha forte)
   - `APP_URL` (a URL pública que o Render vai gerar, ex: `https://clubeusa-api.onrender.com`)
   - **`ZAPI_INSTANCE`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN`** — **SEMPRE obrigatórios**, independente do MESSENGER. O OTP de login é enviado por WhatsApp individual via Z-API. Sem isto, o app aceita cadastro mas nenhum usuário consegue fazer login (recebem "código enviado" mas o código nunca chega).
   - `MESSENGER` = `telegram` ou `zapi` — controla o canal de broadcast de deals/notícias (grupos). Não afeta o OTP.
     - Se `telegram`: preencher `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_PT`, `TELEGRAM_CHANNEL_ES`
     - Se `zapi`: usa os grupos WhatsApp configurados no Z-API (não precisa de Telegram)
   - **Deixar em branco os campos `STRIPE_*`** — não estamos usando Stripe por enquanto

## 4. Ativar membros VIP manualmente (sem Stripe)

Como não tem Stripe conectado, nenhum membro vira VIP sozinho. Para liberar o rastreador de produtos e outras features pagas para alguém que pagou por fora (Pix, etc.):

1. Supabase → Table Editor → tabela `members`
2. Encontrar a linha do membro (por `phone_hash` ou `email_hash` — os dados reais são criptografados, então talvez precise consultar via `phone_enc`/`email_enc` decodificado pelo backend, ou usar o painel admin do próprio Clube USA se já tiver essa função)
3. Editar o campo `plan` para `vip`

## 5. Teste de ponta a ponta

Depois de tudo configurado:
1. Acessar a URL do Render (`APP_URL`)
2. Testar cadastro/login de membro
3. Testar rastrear um produto (Amazon) e ver se aparecem ofertas + cupons
4. Testar fórum e notícias
