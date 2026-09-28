# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-09-28] D-001 — PARALISIA DE MERGE (bloqueio crítico do projeto)

**Contexto:** O builder autônomo abriu 30+ PRs desde junho/2026. Nenhum foi mergeado. Cada sessão cria novos PRs (frequentemente duplicados) porque o código da main não reflete as features desenvolvidas. O projeto está funcionalmente bloqueado: features de Fase 0 (cadastro com email, referral redirect) ainda não chegaram à produção.

**Pergunta:** Como desbloqueamos o fluxo de merge para que o trabalho acumulado chegue à produção?

**PRs prioritários para merge (em ordem, menor risco primeiro):**

| # | Título | Risco | Motivo |
|---|--------|-------|--------|
| #115 | Email confirm + referral redirect | Baixo | 0.1 + 0.2 — base de tudo |
| feat/fase-1.3-influencer-tiers | Tiers de influenciadores | Mínimo | Zero migration, calcula sobre campo existente |
| #109 | Analytics GET /admin/analytics/growth | Baixo | Só leitura, sem migration |
| #104 | Cadastro válido + anti-fraude IP | Médio | Verifica rate-limit, requer env var |

**Opções:**
- **A. Você mergeia os 4 PRs acima agora** (~30min): resultado imediato, projeto desbloqueia
- **B. Dar ao Claude permissão para mergear PRs de baixo risco** (zero migration, não-destrutivos): acelera, requer sua aprovação uma vez
- **C. Continuar como está**: o builder continua criando PRs, nada chega à produção. Não recomendado.

**Recomendação:** Opção A. Os 4 PRs são seguros, bem testados e fundamentais. Levam ~30 minutos no total.

**Status:** PENDENTE

---

### [2026-09-28] D-002 — Comissões do programa de influenciadores (Fase 1.3)

**Contexto:** O tracking de tiers está implementado (Parceiro ≥50, Embaixador ≥250, Hall da Fama ≥1000). O que falta é definir QUANTO pagar por cada indicação válida.

**Pergunta:** Qual o modelo de comissão para influenciadores?

**Opções:**
- **A. Pagar por cadastro válido**: ex. $1 por cadastro confirmado (email + 1 ação)
  - Prós: simples, direto, fácil de comunicar
  - Contras: exige sistema de pagamento (Stripe payout ou manual)
- **B. Créditos/pontos resgatáveis**: sem dinheiro saindo agora; influencer acumula créditos para descontos em serviços futuros
  - Prós: zero custo imediato, mantém engajamento
  - Contras: percepção de valor menor para influencer
- **C. Teto de orçamento + pagamento manual**: você define um budget mensal (ex. $200/mês); os top influencers recebem via Venmo/Zelle manualmente
  - Prós: controle total do custo, sem infra de pagamento automático
  - Contras: trabalho manual, não escala

**Recomendação:** Começar com **Opção C** (manual, orçamento fixo). Define um budget de $100-$200/mês, paga manualmente os top 5 toda semana. Quando tiver 50+ influenciadores ativos, automatiza com Stripe payout.

**Precisa definir:** (a) valor por indicação válida, (b) teto mensal de orçamento, (c) canal de pagamento (Venmo/Zelle/PayPal).

**Status:** PENDENTE

---

### [2026-09-27] D-003 — Provider de email para confirmação (Fase 0.1)

**Contexto:** A Fase 0.1 implementa confirmação de email. O código abstrai o envio (Resend > SMTP > log-dev). Em produção, um provider é obrigatório para os emails chegarem ao usuário.

**Pergunta:** Qual provider de email usar em produção?

**Opções:**
- **Resend** (recomendado): grátis até 3.000 emails/mês; API simples; domínio próprio necessário
  - Prós: fácil, boa deliverability, plano grátis suficiente para 1k usuários
  - Contras: requer verificação de domínio (clubeusa.com)
- **Sendgrid**: grátis até 100 emails/dia — limite apertado
- **SMTP Gmail/Zoho**: gratuito mas com limites e risco de spam

**Recomendação:** Resend. Criar conta em resend.com → verificar domínio `clubeusa.com` → setar `RESEND_API_KEY` e `EMAIL_FROM=noreply@clubeusa.com` no Render (~30min).

**Status:** PENDENTE

---

### [2026-09-27] D-004 — Slug customizado para influenciadores (/i/joao)

**Contexto:** O referral link atual usa código aleatório (`/i/AB3D5F7G`). O roadmap menciona slugs por nome (`/i/joao`).

**Pergunta:** Vale implementar slug customizado agora?

**Opções:**
- **A. Manter código aleatório** (atual): funciona, rastreável, sem esforço extra
- **B. Adicionar campo `referral_slug`**: links bonitos para influencers divulgarem (ex: `/i/joao`)
  - Exige: coluna `referral_slug TEXT UNIQUE` em members + endpoint de atualização

**Recomendação:** Fazer a Opção B quando iniciar Fase 1.3 de pagamento. O `/i/{CODE}` já funciona e não é bloqueante.

**Status:** PENDENTE (adiar para pós D-001 + D-002 resolvidos)

---

*Atualizado em: 2026-09-28*
