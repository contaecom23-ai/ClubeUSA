# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 D-001 — [2026-09-16] PARALISIA DE MERGE — 29 PRs sem revisão desde 18/ago

**Contexto:** O agente abriu 29 PRs desde 2026-08-18. Nenhum foi revisado nem mergeado. O código na `main` tem 4 semanas de defasagem. Tudo que foi construído (email confirmation, referral /i/{code}, analytics, deal urgency, influencer tiers, empregos, moradia) está em PRs órfãos que nunca chegaram a produção. A cada rodada o agente está criando PRs sobre uma base desatualizada, acumulando dívida técnica sem entregar valor.

**Pergunta:** Como você quer resolver os 29 PRs acumulados?

**Opções:**

- **A) Mergear em lote — fechar todos os PRs antigos, mergear os 4 mais recentes em ordem:**
  - Fechar PRs #69 a #94 (velhos, substituídos)
  - Mergear em ordem: #95 → #96 → #97 → #98
  - Pros: entrega tudo o que foi construído; base atualizada
  - Cons: requer sua atenção por ~30 minutos; pode ter conflitos

- **B) Fechar tudo e reiniciar do zero:**
  - Fechar todos os 29 PRs
  - O agente faz uma única PR consolidada com as features mais críticas
  - Pros: base limpa, sem conflitos acumulados
  - Cons: perde trabalho já feito (testado, revisável)

- **C) Manter o fluxo atual (abrir PRs, você mergeará quando puder):**
  - Pros: nenhum esforço imediato
  - Cons: o problema piora a cada rodada; mais PRs, mais conflitos, mais dívida

**Recomendação:** **Opção A**. Leva 30 minutos hoje e desbloqueia o projeto. Os 4 PRs mais recentes (#95–#98) são os mais completos e substituem todos os anteriores.

**Ordem de merge sugerida:**
1. PR #95 — triage docs (ROADMAP + DECISOES)
2. PR #96 — deal urgency (Fase 1.1)
3. PR #97 — influencer tiers (Fase 1.3)
4. PR #98 — email confirmation + referral /i/{code} (Fases 0.1 + 0.2)

**Status:** PENDENTE — **ação obrigatória do dono**

---

## D-002 — [2026-09-16] Provedor de email para confirmação (Fase 0.1)

**Contexto:** A Fase 0.1 exige "email confirmado". A autenticação primária usa WhatsApp/OTP (já funciona). Email confirmado é necessário como canal de backup e para validar "cadastro válido" na Fase 0.4. O código para o fluxo de confirmação já está no PR #98, mas precisa de um provedor de email real para funcionar em produção.

**Pergunta:** Qual provedor de email você quer usar para enviar emails de confirmação?

**Opções:**

- **A) Resend (resend.com)** — plano free: 3.000 emails/mês, API simples, fácil setup
  - Pros: free tier generoso, excelente developer experience, sem cartão de crédito
  - Cons: menos conhecido, startup relativamente nova
  - Custo: $0 até 3k emails/mês, depois $20/mês

- **B) SendGrid (sendgrid.com)** — plano free: 100 emails/dia
  - Pros: mais estabelecido, boa reputação de entrega
  - Cons: free tier muito limitado (100/dia = 3k/mês máximo), setup mais burocrático
  - Custo: $0 até 100/dia, depois $19.95/mês

- **C) AWS SES** — $0.10 por 1000 emails
  - Pros: custo muito baixo em escala, confiável
  - Cons: requer conta AWS, setup mais complexo, sandbox mode por padrão
  - Custo: $0.10/1000 emails (mínimo prático: $1–5/mês)

- **D) Adiar email confirmation** — usar só phone/OTP por agora
  - Pros: zero setup, zero custo, já funciona
  - Cons: Fase 0.1 tecnicamente incompleta; sem backup de comunicação além de WhatsApp

**Recomendação:** **Opção A (Resend)**. Free tier suficiente para os primeiros 1.000 usuários, setup em 10 minutos, sem cartão de crédito. Para ativar: criar conta em resend.com, obter API key, adicionar `RESEND_API_KEY` nas variáveis de ambiente do Render.

**Status:** PENDENTE

---

## D-003 — [2026-09-16] Deploy — app não está em produção

**Contexto:** O código está no repositório mas o app não está deployado. O `render.yaml` está configurado para Render.com, mas as variáveis de ambiente necessárias (Supabase, Stripe, Z-API) precisam ser configuradas manualmente no painel do Render.

**Pergunta:** Você já tem as contas e chaves necessárias? O deploy pode ser feito agora?

**Variáveis necessárias para o deploy:**
```
SUPABASE_URL=          # painel Supabase → Settings → API
SUPABASE_SERVICE_KEY=  # painel Supabase → Settings → API (service_role)
SECRET_KEY=            # gerar: python -c "import secrets; print(secrets.token_urlsafe(32))"
ZAPI_INSTANCE=         # painel Z-API
ZAPI_TOKEN=            # painel Z-API
ZAPI_CLIENT_TOKEN=     # painel Z-API
STRIPE_SECRET_KEY=     # painel Stripe (pode ser test key por enquanto)
STRIPE_WEBHOOK_SECRET= # criar webhook no Stripe apontando para https://<seu-app>.onrender.com/billing/webhook
STRIPE_VIP_PRICE_ID=   # criar produto VIP no Stripe ($4.99/mês)
APP_URL=               # https://<seu-app>.onrender.com
ENVIRONMENT=production
```

**Recomendação:** Se você tem todas essas chaves, o deploy pode ser feito agora. Conecte o repositório no Render, configure as variáveis e deploye. O agente pode ajudar a verificar se está tudo OK após o deploy.

**Status:** PENDENTE

---

## D-004 — [2026-09-16] Estratégia de comunicação com o agente

**Contexto:** O agente roda 3x/dia de forma autônoma mas não tem como saber se você leu as notificações anteriores. Todos os DECISOES.md anteriores estão em PRs não mergeados — você talvez nunca tenha visto nenhum deles.

**Pergunta:** Como você quer se comunicar com o agente sobre prioridades e decisões?

**Opções:**
- **A)** Você mergeará os PRs periodicamente (1x/semana) e o agente continua o fluxo atual
- **B)** Você quer receber um resumo por WhatsApp ao invés de abrir o GitHub
- **C)** Você quer dar feedback diretamente no chat antes do próximo ciclo

**Recomendação:** Sem comunicação regular, o agente continuará abrindo PRs no vácuo. Mesmo que seja 5 minutos por semana para aprovar/rejeitar, isso desbloquearia o projeto.

**Status:** PENDENTE

---

*Atualizado em: 2026-09-16*
