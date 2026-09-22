# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## 🚨 D-005 — URGENTE: 31 PRs sem merge — projeto parado (2026-09-22)

**Data:** 2026-09-22
**Contexto:** O agente rodou ~100 vezes desde julho/2026 e produziu 31 PRs abertos cobrindo
todas as fases do roadmap até a 2.1. Nenhum PR foi mergeado. O main branch está idêntico
ao de julho — nenhuma feature chegou ao usuário.

**Estado atual em main:**
- Auth via WhatsApp OTP (Z-API) — funcional
- Deals, referral schema, leaderboard, Stripe, forum, news, assistant — funcional
- Email confirmado, referral /i/{code}, analytics, cadastro válido, empregos, moradia,
  influencer tiers, assinatura de empresas — **tudo implementado em PRs, NADA em produção**

**Code review concluído hoje (2026-09-22):** PR #106 (email confirmação, Fase 0.1)
foi auditado linha a linha. Resultado: **SEGURO PARA MERGE**.
- Token SHA-256 no banco, raw nunca armazenado ✅
- RLS ativo na tabela de tokens ✅
- Sem SQL injection, sem open redirect, sem vazamento de PII ✅
- 12 testes passando incluindo isolamento multi-tenant ✅

**Ordem recomendada de merge (menor risco primeiro):**

| Prioridade | PR | Fase | Risco | Estado |
|------------|----|------|-------|--------|
| 1 | #101 | Docs (DECISOES+ROADMAP) | Mínimo | Clean, não-draft |
| 2 | #106 | 0.1 Email confirmação | Baixo | Clean, revisado ✅ |
| 3 | #102 | 0.2 Referral /i/{code} | Baixo | Clean |
| 4 | #104 | 0.4 Cadastro válido | Baixo | Clean |
| 5 | #97  | 1.1 Deal urgency | Baixo | Clean |
| 6 | #96  | 1.3 Influencer tiers | Médio | Draft |
| 7 | #93  | 1.4 Empregos | Médio | Draft |
| 8 | #94  | 1.5 Moradia | Médio | Draft |
| 9 | #105 | 2.1 Assinatura empresas | Médio | Draft |

**Para cada grupo com múltiplos PRs duplicados:** Merge apenas o mais recente
(listado acima), fechar os demais.

**O que acontece se não houver ação:**
- PRs ficam divergindo de main → conflitos crescentes → retrabalho
- Nenhuma feature chega ao usuário
- O agente continua criando PRs redundantes a cada ciclo

**Ação necessária:** Merge ou close de PRs — começa pelo #101 (só docs, 2 arquivos, 5 min).

**Status:** PENDENTE — decisão e ação do dono

---

## D-004 — Qual auth usar? WhatsApp OTP ou Email+Senha?

**Data:** 2026-09-22
**Contexto:** Main usa WhatsApp OTP (Z-API obrigatório). A Fase 0.1 adicionou email
confirmado como **complemento** (não substituto) — o usuário ainda entra pelo WhatsApp,
mas pode vincular e confirmar um e-mail. Isso resolve a questão sem reescrever o auth.

**Recomendação:** Manter WhatsApp OTP como auth principal + email como campo confirmado
de perfil (Fase 0.1). Não mudar o auth agora.

**Status:** RESOLVIDO — email é complemento, não substituto

---

## D-003 — Serviço de e-mail SMTP para Fase 0.1

**Data:** 2026-09-22
**Contexto:** Implementação do email já está no PR #106. Precisa de config de SMTP.

**Opções (custo zero para os primeiros 1.000 usuários):**
- **Mailgun** — 100 e-mails/dia grátis, SMTP padrão
- **Resend.com** — 3.000/mês grátis, API moderna, boa DX
- **SendGrid** — 100/dia grátis

**Recomendação:** Resend.com (3.000/mês grátis, fácil de configurar).

**Configurar no deploy:**
```
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=<api-key>
SMTP_FROM=noreply@clubeusa.com
```

**Status:** PENDENTE — dono configura env vars após merge do PR #106

---

## D-002 — Deploy em produção

**Data:** 2026-09-22
**Contexto:** `render.yaml` configurado, mas o app nunca foi deployado.

**Bloqueador real:** Merge dos PRs (D-005) vem antes do deploy.

**Após merge:** Render.com — conectar o repo, configurar as env vars, deploy automático.
Env vars obrigatórias: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SECRET_KEY`,
`ZAPI_INSTANCE`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN`.

**Status:** PENDENTE — requer merge primeiro (D-005)

---

## D-001 — Credenciais externas necessárias

**Data:** 2026-09-22

| Serviço | Env var | Obrigatório? |
|---------|---------|-------------|
| Supabase | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | SIM |
| Segredo JWT | `SECRET_KEY` | SIM (gerar com `openssl rand -hex 32`) |
| Z-API (WhatsApp) | `ZAPI_INSTANCE`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN` | Para auth |
| Stripe | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_VIP_PRICE_ID` | Para pagamentos |
| SMTP | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` | Para email (Fase 0.1) |

**Status:** PENDENTE — dono configura no painel do Render

---

*Atualizado em: 2026-09-22*
