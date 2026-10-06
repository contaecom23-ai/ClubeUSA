# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## ⚠️ AÇÃO URGENTE — 2026-10-06

**O projeto está travado há meses com 40+ PRs sem merge.**  
**Uma única ação desbloqueia tudo:** merge do PR #125.

👉 **[Abrir PR #125 para merge](https://github.com/contaecom23-ai/ClubeUSA/pull/125)**

O PR #125 está **limpo** (sem conflitos), tem testes, cobre Fases 0.1–0.4 completas e substitui ~15 PRs duplicadas.

---

## D-001: Merge PR #125 — Fases 0.1–0.4 completas

**Data:** 2026-10-06  
**Status:** 🔴 PENDENTE — aguardando ação do dono

**Contexto:**
O projeto tem 40+ pull requests abertos, nenhum mergeado desde agosto de 2026. A sessão mais recente verificou o código do PR #125 (criado 2026-10-03) e ele está pronto.

**O que PR #125 entrega:**
- **Fase 0.1** — Confirmação de email (token SHA-256, TTL 24h, SMTP + STARTTLS)
- **Fase 0.2** — URL de referral rastreável `/i/{code}` (ex: clubeusa.com/i/joao)
- **Fase 0.3** — Analytics admin: funil de conversão + crescimento diário
- **Fase 0.4** — Anti-fraude: máx 3 cadastros por IP nas últimas 24h

**O que o Claude verificou (2026-10-06):**
- ✅ `mergeable_state: clean` — sem conflitos com main
- ✅ Tokens armazenados como SHA-256 (nunca plaintext)
- ✅ SMTP usa STARTTLS, env var `ENVIRONMENT=production` ativa envios reais
- ✅ Endpoints admin protegidos por `require_admin`
- ✅ Rate limit existente cobre novo endpoint
- ✅ Migrações SQL idempotentes (podem ser executadas múltiplas vezes)
- ✅ 15+ testes cobrindo fluxo de confirmação, email service e analytics

**Pergunta:**  
Você pode fazer merge do PR #125 agora?

**Como fazer (5 minutos):**
1. Abra https://github.com/contaecom23-ai/ClubeUSA/pull/125
2. Role até o final e clique em **"Merge pull request"**
3. Execute as 2 migrações SQL no painel do Supabase:
   - `07-Clube-USA/clubeusa/db/email_confirmation_migration.sql`
   - `07-Clube-USA/clubeusa/db/fase0_complementar_migration.sql`
4. Pronto — as Fases 0.1–0.4 estarão no main

**Recomendação:**  
Faça merge DESTE PR (docs/decisoes-2026-10-06) primeiro — é apenas este arquivo.  
Depois, PR #125 — é o código das 4 fases.

---

## D-002: Configuração de ambiente de produção

**Data:** 2026-10-06  
**Status:** 🔴 PENDENTE

**Variáveis obrigatórias para o app funcionar em produção:**

| Variável | Onde configurar |
|---|---|
| `SUPABASE_URL` | Painel Supabase → Project Settings → API |
| `SUPABASE_SERVICE_KEY` | Painel Supabase → Project Settings → API |
| `JWT_SECRET` | Gere com: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ENCRYPTION_KEY` | Gere com: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `STRIPE_SECRET_KEY` | Painel Stripe → Developers → API Keys |
| `STRIPE_WEBHOOK_SECRET` | Painel Stripe → Webhooks |
| `STRIPE_VIP_PRICE_ID` | Painel Stripe → Products |
| `ZAPI_INSTANCE` | Painel Z-API |
| `ZAPI_TOKEN` | Painel Z-API |
| `SMTP_HOST` | Ex: smtp.sendgrid.net |
| `SMTP_USER` | Ex: apikey |
| `SMTP_PASS` | Chave SMTP do provedor |
| `FROM_EMAIL` | Ex: noreply@clubeusa.com |
| `APP_URL` | Ex: https://clubeusa.com |
| `ENVIRONMENT` | `production` |

**Pergunta:** O app está deployado e essas variáveis estão configuradas?

---

## D-003: Auth principal — WhatsApp OTP ou Email+Senha?

**Data:** 2026-10-06  
**Status:** 🟡 PENDENTE (não bloqueia PR #125)

**Situação atual:** Auth via WhatsApp OTP (Z-API). PR #125 ADICIONA email de confirmação como segunda camada, não substitui o OTP. Não precisa decidir agora.

**Pergunta para o futuro:** Quer manter WhatsApp como auth principal ou migrar para email+senha?  
**Recomendação:** Manter WhatsApp OTP por ora — penetração de 95%+ no público brasileiro. Email serve como recuperação de conta.

---

## Como usar este arquivo

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, chaves externas, direção estratégica), ele registra aqui e avança para outra tarefa. Revise 1x/dia.

---

*Atualizado em: 2026-10-06*
