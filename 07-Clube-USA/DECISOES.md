# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## ⚠️ AÇÃO URGENTE — verificado em 2026-10-07

**O projeto tem 40+ PRs sem merge desde agosto de 2026.**  
**Uma única ação desbloqueia tudo:** merge do PR #125.

👉 **[Abrir PR #125 para merge](https://github.com/contaecom23-ai/ClubeUSA/pull/125)**

O PR #125 está **limpo** (sem conflitos), código revisado, testes incluídos. Cobre Fases 0.1–0.4 completas e substitui ~15 PRs duplicadas.

**Nota 2026-10-07:** Uma sessão autônoma criou o PR #127 depois do #125 cobrindo só a Fase 0.1 — é duplicata desnecessária. Pode fechar o #127.

---

## D-001: Merge PR #125 — Fases 0.1–0.4 completas

**Data:** 2026-10-06  
**Última verificação:** 2026-10-07  
**Status:** 🔴 PENDENTE — aguardando ação do dono

**Contexto:**
O projeto tem 40+ pull requests abertos, nenhum mergeado desde agosto de 2026. O PR #125 (criado 2026-10-03) foi inspecionado em profundidade por duas sessões independentes e está pronto para merge.

**O que PR #125 entrega:**
- **Fase 0.1** — Confirmação de email (token SHA-256, TTL 24h, SMTP + STARTTLS)
- **Fase 0.2** — URL de referral rastreável `/i/{code}` (ex: clubeusa.com/i/joao)
- **Fase 0.3** — Analytics admin: funil de conversão + crescimento diário
- **Fase 0.4** — Anti-fraude: máx 3 cadastros por IP nas últimas 24h

**O que o Claude verificou (2026-10-07):**
- ✅ `mergeable_state: clean` — sem conflitos com main
- ✅ Security headers middleware implementado
- ✅ Rate limiting por IP (5 req/min auth, 60 req/min geral)
- ✅ CORS restrito a origens conhecidas em produção
- ✅ Stripe webhook com verificação HMAC obrigatória
- ✅ OTP armazenado no Supabase com TTL 10 min (não em memória)
- ✅ Token de email como SHA-256 apenas (nunca plaintext)
- ✅ Endpoints admin protegidos por `require_admin`
- ✅ Validação Pydantic em todos os inputs
- ✅ Nenhum segredo hardcoded — tudo via env var
- ✅ Migrações SQL idempotentes

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

## D-004: PR #127 é duplicata do PR #125 — fechar?

**Data:** 2026-10-07  
**Status:** 🟡 INFORMAÇÃO (não bloqueia nada)

**Contexto:** Uma sessão autônoma de 2026-10-06 criou o PR #127 cobrindo apenas a Fase 0.1 (email verification), sem perceber que o PR #125 já cobre 0.1+0.2+0.3+0.4 de forma mais completa. O PR #127 é uma duplicata.

**Recomendação:** Fechar PR #127 sem merge após mergear PR #125.

---

## Como usar este arquivo

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, chaves externas, direção estratégica), ele registra aqui e avança para outra tarefa. Revise 1x/dia.

---

*Atualizado em: 2026-10-07*
