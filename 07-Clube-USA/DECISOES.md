# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## 🚨 SITUAÇÃO ATUAL (2026-10-23)

### O que existe hoje (código em `main`)
O código base está completo e pronto para deploy. Dono empurrou o app completo diretamente para `main` em 2026-08-18. O que **já funciona**:
- Cadastro + perfil + auth via OTP WhatsApp
- Sistema de referral (links únicos, atribuição)
- Deals/promoções com curadoria admin
- Rastreador de preço multi-marketplace (Amazon/Walmart/BestBuy) + cupons + alertas
- Plano VIP via Stripe
- Painel admin completo
- Forum + News + Assistente IA

### O que foi adicionado neste PR (2026-10-23)
- Analytics básico (Fase 0.3): tracking de eventos, `/admin/analytics`
- Status de cadastro válido (Fase 0.4): `/member/validation-status`

### O que FALTA (código pendente)
- Email confirmado (0.1): depende de SMTP ativo (D-003 abaixo)
- ZIP search (1.2): pode ser desenvolvido sem bloqueio de infra
- Influenciadores (1.3), Empregos (1.4), Moradia (1.5): podem ser desenvolvidos

### Os 90+ PRs anteriores
PRs de runs anteriores (claude/fase-0.1-*, claude/fase-0.2-*, etc.) foram construídos sobre uma versão antiga do `main` e são **incompatíveis** com o código atual. Recomendação: fechá-los com mensagem "superseded by current main codebase".

---

## ⚡ AÇÃO NECESSÁRIA DO DONO (prioridade)

### Passo 1 — Configurar infraestrutura (único bloqueio real para 1º usuário)

| Item | Custo | Tempo |
|------|-------|-------|
| Criar projeto Supabase: https://supabase.com | Grátis | 5 min |
| Rodar migration `07-Clube-USA/clubeusa/db/schema.sql` + `analytics_migration.sql` no Supabase SQL Editor | Grátis | 5 min |
| Configurar email transacional: Resend.com (https://resend.com) — grátis até 3.000/mês | $0 | 10 min |
| Deploy backend no Render (https://render.com) ou Railway (https://railway.app) | $0–$5/mês | 15 min |
| Criar `.env` com as credenciais (use `.env.example` como base) | — | 5 min |

### Passo 2 — Configurar variáveis de ambiente

```
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=seu-service-role-key
SUPABASE_JWT_SECRET=seu-jwt-secret
JWT_SECRET=gerar com: python utils/security.py
ENCRYPTION_KEY=gerar com: python utils/security.py
STRIPE_SECRET_KEY=sua-chave-stripe (se quiser VIP)
STRIPE_WEBHOOK_SECRET=seu-webhook-secret
STRIPE_VIP_PRICE_ID=seu-price-id
ZAPI_INSTANCE=sua-instancia (para WhatsApp OTP)
ZAPI_TOKEN=seu-token
ZAPI_CLIENT_TOKEN=seu-client-token
ADMIN_API_KEY=gerar aleatório (para endpoints admin)
APP_URL=https://seu-dominio.com
ENVIRONMENT=production
```

### Passo 3 — Fechar PRs obsoletos

Acessar https://github.com/contaecom23-ai/ClubeUSA/pulls e fechar todos os PRs de branches `claude/fase-0.*` e `claude/fase-1.*` anteriores. São incompatíveis com o código atual.

---

## Decisões Técnicas Pendentes

### [2026-07-03 | atualizado 2026-10-23] D-002: Supabase

**Status:** PENDENTE — bloqueante para deploy

**Ação:** Criar projeto em https://supabase.com e coletar:
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`

---

### [2026-07-03 | atualizado 2026-10-23] D-003: Email transacional

**Status:** PENDENTE — bloqueante para email confirmation (Fase 0.1)

**Recomendação:** Resend.com — grátis até 3.000/mês, integra direto no Supabase (Settings > Auth > SMTP). Suficiente para os primeiros 6+ meses.

---

### [2026-07-03 | atualizado 2026-10-23] D-004: Hospedagem do backend

**Recomendação:** Render.com plano free (tem cold start de ~50s) ou Railway $5/mês (sem cold start).

**Status:** PENDENTE

---

### [2026-07-03 | atualizado 2026-10-23] D-005: Domínio

**Recomendação:** `clubeusa.com` no Cloudflare Registrar (~$12/ano).

**Status:** PENDENTE

---

### [2026-10-23] D-013: Próxima feature a implementar após merge deste PR

**Contexto:** Com analytics + validation-status implementados, as opções para a próxima rodada são:

**Opções:**
- **A — Fase 0.1 conclusão (email confirmation):** Adiciona token de confirmação de email + endpoint `/auth/email/confirm`. Depende de D-003 (SMTP) para enviar o email, mas o código pode ser escrito antes.
- **B — Fase 1.2 ZIP search:** Adiciona tabela `zip_codes` com seed das 200 principais cidades com comunidade brasileira + endpoint `GET /promotions?zip=33101&radius_miles=5`. Independente de infra externa.
- **C — Fase 1.4 Empregos:** Tabela `jobs` + admin CRUD + `GET /jobs` com filtro ZIP/raio. Seed de 10-20 vagas curadas. Independente de infra externa.

**Recomendação:** Opção B (ZIP search) — maior impacto para tração, não depende de nenhuma decisão pendente, e habilita tanto 1.2 quanto 1.4 e 1.5.

**Status:** PENDENTE — decidir qual feature implementar na próxima rodada

---

*Atualizado em: 2026-10-23 — Situação real documentada; PR com analytics + validation-status criado; próxima decisão de feature registrada em D-013.*
