# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.
> Atualizado a cada run. Você revisa 1×/dia.

---

## 🚨 URGENTE — O projeto está parado há 13 dias

O builder autônomo roda 3×/dia mas **não avança** porque nenhum PR foi mergeado desde 2026-08-09.

### O que você precisa fazer (30 minutos):

**Passo 1 — Mergear estes 2 PRs (prioridade máxima):**
- **PR #62** (`feat/consolida-0.2-0.3-seguranca`) — completa referral redirect + analytics + anti-fraude + segurança webhook. "MERGE ESTE PRIMEIRO".
- **PR #56** (`ci/pytest-workflow`) — CI automático de testes nos PRs futuros.

**Passo 2 — Fechar estes PRs como desatualizados** (botão "Close pull request" sem mergear):
- PR #3, #4, #5, #9, #12, #14, #16, #19, #20 — Fase 0–1, julho, branches antigas e desatualizadas
- PR #46 — email auth (Sistema B descartado — System A já está em main)
- PR #51, #53, #54, #57, #58, #59, #60, #61 — supersedidos ou cobertos pelo PR #62

**Passo 3 — Responder às perguntas abaixo** (para o builder saber como continuar).

---

## Decisões Pendentes

---

### [2026-08-22] Sistema de autenticação — WhatsApp OTP confirmado?

**Contexto:**
O código já em `main` usa **WhatsApp OTP** (Sistema A):
- Registro por telefone → OTP de 6 dígitos via WhatsApp → JWT válido por 7 dias
- Sem senha, sem email obrigatório (email é opcional no cadastro)
- Alinhado com o público: imigrantes brasileiros, WhatsApp é onipresente
- Já implementa: auth, perfil, referral, deals, price tracker, Stripe VIP, painel admin

PR #46 propunha email + senha (Sistema B) mas **nunca entrou em main** e está desatualizado.

**Pergunta:** Você confirma o Sistema A (WhatsApp OTP) como base definitiva da plataforma?

**Opções:**
- **A — Sim, WhatsApp OTP (RECOMENDADO):** Plataforma pode ir ao ar em dias. Claude fecha PR #46 e avança para Fase 1.2+.
- **B — Não, quero email + senha:** Claude precisa migrar o código atual. Estimativa: +2–3 semanas.

**Recomendação:** Opção A. WhatsApp OTP é mais simples para o usuário final e alinhado com o hábito do público. Sem senha para recuperar, sem spam de email de confirmação.

**Status:** PENDENTE

---

### [2026-08-22] Deploy — a plataforma está rodando em algum servidor?

**Contexto:**
O código em `main` está pronto para produção mas não há evidência de deploy. Sem isso, zero usuários reais podem testar.

Variáveis necessárias: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SECRET_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_VIP_PRICE_ID`, `ZAPI_INSTANCE`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN`.

**Pergunta:** A plataforma está deployada?

**Opções:**
- **A — Sim:** Informe a URL. Claude faz health check e valida o sistema.
- **B — Não:** Claude escreve o guia completo de setup no Render.com (~$7/mês, suficiente para os primeiros 1.000 usuários). Setup manual de ~45 min.

**Recomendação:** Opção B se ainda não foi feito. O Render.com tem plano free que aguenta o início.

**Status:** PENDENTE

---

### [2026-08-22] Supabase — banco de dados criado e schema rodado?

**Contexto:**
O schema SQL está em `07-Clube-USA/clubeusa/db/`. Precisa ser rodado no Supabase para criar as tabelas. Sem isso, todas as chamadas ao banco falham.

**Pergunta:** Você já tem projeto Supabase para o Clube USA com as tabelas criadas?

**Opções:**
- **A — Sim:** Compartilhe os valores `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`. Claude configura e testa.
- **B — Não:** Claude escreve o passo-a-passo completo. Free tier do Supabase é suficiente para os primeiros 10.000 usuários.

**Status:** PENDENTE

---

## Log de runs automáticos

| Data | Ação | Resultado |
|------|------|-----------|
| 2026-08-22 | Leu main.py completo, confirmou estado real, atualizou ROADMAP + DECISOES | PR #64 aberto |
| 2026-08-21 | Criou PR #62 (consolida 0.2+0.3+segurança) e PR #63 (testes) | Sem merge |
| 2026-08-20 | Diagnóstico completo, 4 bloqueios documentados no PR #60 | Sem merge |
| 2026-08-14 | Admin branch documentou loop de 50 PRs, PR #48 aberto | PR #48 não mergeado |
| 2026-08-09 | Loop detectado, primeiro alerta | Sem ação do dono |

---

*Atualizado em: 2026-08-22*
