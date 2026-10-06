# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## ⚠️ AÇÃO URGENTE — verificado em 2026-10-06 22:09 UTC

**O projeto está travado há 4+ meses com 30+ PRs sem merge.**
**Uma única ação desbloqueia tudo: merge deste PR (#125).**

👉 **[Abrir PR #125 para merge](https://github.com/contaecom23-ai/ClubeUSA/pull/125)**

Este PR está **limpo** (sem conflitos com main), tem testes, cobre Fases 0.1–0.4 completas
e substitui ~15 PRs duplicadas. Verificado pelo Claude em 2026-10-06.

---

## D-001: Merge PR #125 — Fases 0.1–0.4 completas

**Data:** 2026-10-03 | **Último check:** 2026-10-06
**Status:** 🔴 PENDENTE — aguardando ação do dono

**O que este PR entrega:**
- **Fase 0.1** — Confirmação de email (token SHA-256, TTL 24h, SMTP + STARTTLS)
- **Fase 0.2** — URL de referral rastreável `/i/{code}` (ex: clubeusa.com/i/joao)
- **Fase 0.3** — Analytics admin: funil de conversão + crescimento diário
- **Fase 0.4** — Anti-fraude: máx 3 cadastros por IP nas últimas 24h

**Verificação do Claude (2026-10-06):**
- ✅ `mergeable_state: clean` — sem conflitos com main
- ✅ Tokens de email armazenados como SHA-256 (nunca plaintext)
- ✅ SMTP usa STARTTLS, env var `ENVIRONMENT=production` ativa envios reais
- ✅ Endpoints admin protegidos por `require_admin`
- ✅ Rate limit cobre endpoints novos
- ✅ Migrações SQL idempotentes (seguras para reexecutar)
- ✅ 15+ testes cobrindo confirmação de email, email service e analytics
- ✅ Isolamento multi-tenant: dados acessíveis apenas pelo dono (user_id do token)

**Como fazer o merge (5 minutos):**
1. Abra https://github.com/contaecom23-ai/ClubeUSA/pull/125
2. Role até o final e clique em **"Merge pull request"**
3. Execute as 2 migrações SQL no painel do Supabase (SQL Editor):
   - `07-Clube-USA/clubeusa/db/email_confirmation_migration.sql`
   - `07-Clube-USA/clubeusa/db/fase0_complementar_migration.sql`
4. Pronto — Fases 0.1–0.4 estarão no main

**Por que o Claude não pode fazer isso sozinho:**
Regra de segurança explícita: Claude não faz merge direto em main. Requer revisão humana.

**Impacto de continuar sem agir:**
- Cada sessão cria mais 1–2 PRs duplicadas sem avançar o produto real
- Código de produção no main ainda está em versão de junho/2026
- Custo de tokens sendo gasto em loop sem resultado real

---

## D-002: Configuração de ambiente de produção

**Data:** 2026-10-03 | **Status:** 🔴 PENDENTE

O código está completo. Para funcionar em produção, configure estas variáveis no
painel do serviço de hospedagem (Railway, Render, Fly.io, etc.):

| Variável | Como obter |
|---|---|
| `SUPABASE_URL` | Painel Supabase → Project Settings → API |
| `SUPABASE_SERVICE_KEY` | Painel Supabase → Project Settings → API (service_role key) |
| `JWT_SECRET` | Gere: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ENCRYPTION_KEY` | Gere: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `STRIPE_SECRET_KEY` | Painel Stripe → Developers → API Keys |
| `STRIPE_WEBHOOK_SECRET` | Painel Stripe → Webhooks → signing secret |
| `STRIPE_VIP_PRICE_ID` | Painel Stripe → Products → ID do preço VIP |
| `ZAPI_INSTANCE` | Painel Z-API → sua instância |
| `ZAPI_TOKEN` | Painel Z-API → token da instância |
| `ZAPI_CLIENT_TOKEN` | Painel Z-API → client token |
| `SMTP_HOST` | Ex: `smtp.sendgrid.net` |
| `SMTP_PORT` | `587` (STARTTLS) |
| `SMTP_USER` | Ex: `apikey` (SendGrid) |
| `SMTP_PASS` | Chave SMTP do provedor |
| `FROM_EMAIL` | Ex: `noreply@clubeusa.com` |
| `APP_URL` | Ex: `https://clubeusa.com` |
| `ENVIRONMENT` | `production` |

**Pergunta:** O app está deployado em algum serviço? Essas variáveis estão configuradas?

---

## D-003: Auth principal — WhatsApp OTP ou Email+Senha?

**Data:** 2026-10-06 | **Status:** 🟡 NÃO BLOQUEIA O MERGE

**Situação atual:** Auth via WhatsApp OTP (Z-API). Este PR ADICIONA email de
confirmação como camada extra de verificação — não substitui o OTP.

**Para o futuro:** Quer manter WhatsApp como auth principal ou migrar para email+senha?
**Recomendação:** Manter WhatsApp OTP por ora — penetração de 95%+ no público
brasileiro. Email serve para confirmação de conta e recuperação.

---

## D-004: Próximos passos após merge do PR #125

**Data:** 2026-10-06 | **Status:** 🟡 PARA DEPOIS DO MERGE

Após Fase 0 estar no main, o próximo passo é **Fase 1.1 — PROMOÇÕES/ACHADOS**
(carro-chefe da plataforma). Ela já está implementada no branch
`feat/fase-1.1-promocoes-comunidade` (PR #113). Verificar esse PR em seguida.

O roadmap completo está em `07-Clube-USA/ROADMAP.md` neste branch.

---

## Como usar este arquivo

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, chaves
externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra
aqui e avança para outra tarefa. Revise 1x/dia.

---

*Atualizado em: 2026-10-06*
