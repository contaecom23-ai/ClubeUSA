# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação.
> O agente NÃO age em itens desta lista sem aprovação explícita.

---

## 🚨 D-001 — [2026-09-16] UM PR PARA MERGEAR — fim do acúmulo de 30 PRs

**Contexto:** O agente abriu 30 PRs desde 2026-08-18. Nenhum foi mergeado. Cada rodada criava
novo PR, acumulando mais confusão. Isso foi um erro de processo — identificado, corrigido agora.

Este PR (`consolidado/fase-0.2-0.3`) substitui todos os anteriores. Contém apenas o que
**funciona hoje sem nenhuma configuração extra**:
- `GET /i/{code}` — referral redirect (Fase 0.2) ✅ sem DB, sem email, sem nada
- `GET /admin/analytics` — analytics básico (Fase 0.3) ✅ lê tabelas existentes
- ROADMAP.md e DECISOES.md atualizados

**Pergunta:** Você pode mergear apenas o PR `consolidado/fase-0.2-0.3` e fechar os demais #70–#99?

**Ação concreta (5 minutos):**
1. Abrir: https://github.com/contaecom23-ai/ClubeUSA/pulls
2. Mergear o PR `consolidado/fase-0.2-0.3` (o mais recente, sem conflitos)
3. Fechar os demais 30 PRs (botão "Close pull request" em cada um, ou usar a URL do PR antigo)
4. Pronto — o agente continua daqui com a base limpa

**O que NÃO está neste PR (virá depois):**
- Email confirmation (Fase 0.1) — aguardando D-002 (provedor)
- Deal urgency, influencer tiers, empregos, moradia — Fase 1.x, depois da Fase 0

**Status:** PENDENTE — ação do dono

---

## D-002 — [2026-09-16] Provedor de email para confirmação (Fase 0.1)

**Contexto:** Fase 0.1 exige email confirmado. O código backend está pronto no PR #98, mas precisa
de um provedor de email real para funcionar em produção.

**Pergunta:** Qual provedor de email usar?

**Opções:**

- **A) Resend (resend.com)** — plano free: 3.000 emails/mês
  - Pros: free tier generoso, API simples, sem cartão de crédito para começar
  - Cons: startup relativamente nova (fundada 2022)
  - Custo: $0 até 3k/mês → $20/mês depois

- **B) SendGrid** — plano free: 100 emails/dia
  - Pros: mais estabelecido, boa reputação de entrega
  - Cons: free tier limitado (100/dia), setup mais burocrático
  - Custo: $0 até 100/dia → $19.95/mês depois

- **C) AWS SES**
  - Pros: custo muito baixo em escala ($0.10/1000 emails)
  - Cons: requer conta AWS, sandbox mode por padrão, setup mais complexo

- **D) Adiar — usar só WhatsApp/OTP por enquanto**
  - Pros: zero setup, já funciona
  - Cons: Fase 0.1 incompleta; sem canal de backup além do WhatsApp

**Recomendação:** **Opção A (Resend)**. Free tier suficiente para os primeiros 1.000 usuários,
setup em 10 minutos. Para ativar: criar conta em resend.com, obter API key, adicionar
`RESEND_API_KEY` nas env vars do Render.

**Status:** PENDENTE

---

## D-003 — [2026-09-16] Deploy — app ainda não está em produção

**Contexto:** O código está no repositório mas o app não foi deployado. O `render.yaml` está
configurado para Render.com mas as variáveis de ambiente precisam ser configuradas manualmente.

**Variáveis necessárias para o deploy:**
```
SUPABASE_URL=          # painel Supabase → Settings → API
SUPABASE_SERVICE_KEY=  # painel Supabase → Settings → API (service_role)
SECRET_KEY=            # python -c "import secrets; print(secrets.token_urlsafe(32))"
ZAPI_INSTANCE=         # painel Z-API
ZAPI_TOKEN=            # painel Z-API
ZAPI_CLIENT_TOKEN=     # painel Z-API
STRIPE_SECRET_KEY=     # painel Stripe (pode ser test key por enquanto)
STRIPE_WEBHOOK_SECRET= # criar webhook no Stripe → seu-app.onrender.com/billing/webhook
STRIPE_VIP_PRICE_ID=   # criar produto VIP no Stripe ($4.99/mês)
APP_URL=               # https://seu-app.onrender.com
ENVIRONMENT=production
```

**Pergunta:** Você já tem essas chaves? Posso ajudar a verificar o deploy após configurar.

**Status:** PENDENTE

---

## D-004 — [2026-09-16] Próximas features após merge do PR consolidado

**Contexto:** Após o merge de D-001, a Fase 0.1 (email confirmation) é o próximo passo.
Mas ela está bloqueada por D-002. As alternativas enquanto D-002 não resolve:

**Opção A:** Pular para Fase 1.1 (PROMOÇÕES/ACHADOS com urgência — campo `expires_at`)
- Valor imediato para usuários, não depende de email

**Opção B:** Completar Fase 0.1 primeiro (email), depois Fase 1.1
- Mais correto pela sequência, mas dependente de D-002

**Recomendação:** Resolva D-002 (5 minutos no resend.com) e depois D-003 (deploy).
Com o app em produção, Fase 0.1 e Fase 1.1 podem andar em paralelo.

**Status:** PENDENTE — aguarda D-001 e D-002

---

*Atualizado em: 2026-09-16*
