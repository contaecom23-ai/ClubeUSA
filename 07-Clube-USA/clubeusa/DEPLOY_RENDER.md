# Deploy do Clube USA no Render

Sobe 2 serviços a partir do `render.yaml`: a **API + site** (web) e o
**scheduler de deals** (worker). Banco (Supabase) e Stripe já são nuvem.

## Pré-requisitos
- Repositório no GitHub (já está: `gersonmence-max/projetos-claude`).
- Conta no Render (https://render.com).
- Projeto Supabase criado com o schema aplicado (ver abaixo).
- Conta Stripe com o produto VIP criado (ver abaixo).

## 1. Preparar o banco (Supabase)
No SQL Editor do Supabase, execute em ordem:
1. `db/schema.sql`
2. `db/rpc_functions.sql`
3. `db/stripe_migration.sql`
4. Demais migrations conforme necessidade (`news_forum_migration.sql`,
   `price_alerts_migration.sql`, `otp_migration.sql`, `product_tracker_migration.sql`).

## 2. Criar o produto VIP no Stripe
1. Stripe Dashboard (modo **Teste** primeiro) > Products > **Add product**.
2. Nome: `Clube USA VIP`. Preço: **$4.99/mês** (recurring, monthly).
3. Copie o **Price ID** (`price_...`) → será o `STRIPE_VIP_PRICE_ID`.
4. Em Developers > API keys, copie a **Secret key** (`sk_test_...`).

## 3. Subir no Render
1. Dashboard > **New > Blueprint**.
2. Conecte o repositório e aponte para `07-Clube-USA/clubeusa/render.yaml`.
3. O Render detecta os 2 serviços + o grupo de variáveis `clubeusa-secrets`.
4. Preencha **todas** as variáveis `sync:false` no painel (nunca no git):
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`
   - `ENCRYPTION_KEY`, `JWT_SECRET`, `ADMIN_SECRET` (gere com `python utils/security.py`)
   - `STRIPE_SECRET_KEY`, `STRIPE_VIP_PRICE_ID`
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_PT`, `TELEGRAM_CHANNEL_ES`
     (ou as `ZAPI_*` se `MESSENGER=zapi`)
   - `APP_URL` → deixe em branco no primeiro deploy; preencha após o passo 4.
5. Deploy. A API sobe em `https://clubeusa-api.onrender.com` (ou seu domínio).

## 4. Fechar o laço da URL
1. Copie a URL pública da API (do serviço `clubeusa-api`).
2. Atualize a variável `APP_URL` no grupo com essa URL e redeploy.

## 5. Registrar o webhook do Stripe
1. Stripe > Developers > Webhooks > **Add endpoint**.
2. URL: `https://SUA_URL/billing/webhook`
3. Eventos: `checkout.session.completed`, `customer.subscription.deleted`,
   `invoice.payment_failed`.
4. Copie o **Signing secret** (`whsec_...`) → variável `STRIPE_WEBHOOK_SECRET`
   no Render e redeploy.

## 6. Testar o checkout (ponta a ponta)
1. Acesse o site, cadastre-se e faça login (fluxo OTP).
2. Perfil > **Assinar VIP** → redireciona pro checkout do Stripe.
3. Cartão de teste: `4242 4242 4242 4242`, validade futura, CVC qualquer.
4. Após pagar, o Stripe chama o webhook → `plan` vira `vip` no Supabase.
5. Confira: o badge muda para ⭐ VIP e o perfil mostra o card de gerenciar.

## Notas
- **Worker exige plano pago** no Render (Background Workers). A API web roda no
  free, mas hiberna após inatividade (primeira requisição fica lenta).
- Se ainda não for usar o scanner de deals, você pode suspender o serviço
  `clubeusa-scheduler` e subir só a API.
- Estado de runtime do scanner (`dealscanner2/data/`) é efêmero no Render;
  a fonte de verdade dos deals/membros é o Supabase.
