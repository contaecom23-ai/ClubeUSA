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

**Contexto:** O builder autônomo abriu 30+ PRs desde junho/2026. Nenhum foi mergeado. Cada sessão cria novos PRs porque o código da main não reflete as features desenvolvidas. O projeto está bloqueado: features de Fase 0 (cadastro com email, referral redirect) ainda não chegaram à produção.

**Pergunta:** Como desbloqueamos o fluxo de merge?

**PRs prioritários para merge (menor risco primeiro):**

| PR/Branch | O que tem | Risco |
|-----------|-----------|-------|
| #115 | Email confirm (0.1) + referral redirect (0.2) | Baixo |
| feat/fase-1.3-influencer-tiers | Tiers influenciadores | Mínimo (zero migration) |
| #109 | Analytics /admin/analytics/growth (0.3) | Baixo (só leitura) |
| #104 | Cadastro válido + anti-fraude IP (0.4) | Médio |

**Opções:**
- **A. Você mergeia os 4 acima agora** (~30min): desbloqueia o projeto imediatamente
- **B. Dar permissão ao Claude para mergear PRs zero-risk** (sem migration, não-destrutivo): acelera com sua aprovação uma vez
- **C. Continuar como está**: builder cria PRs, nada chega à produção — não recomendado

**Recomendação:** Opção A. Todos são seguros e fundamentais.

**Status:** PENDENTE

---

### [2026-09-28] D-006 — Comissões e teto de orçamento para influenciadores (Fase 1.3)

**Contexto:**
O sistema de tier de influenciadores está implementado (`/member/influencer`, `/admin/influencers`).
Tiers: Parceiro (≥50), Embaixador (≥250), Hall da Fama (≥1000).
O que falta: quanto pagar por cada indicação válida.

**Pergunta:**
Qual o valor de comissão por cadastro válido e qual o teto mensal por influenciador?

**Opções:**

**Opção A — Comissão fixa baixa, sem teto:**
- $0.50–$1.00 por cadastro válido
- Prós: simples, escala automaticamente
- Contras: sem controle de custo

**Opção B — Comissão em escala por tier, com teto mensal:**
- Parceiro: $0.50/cadastro, teto $50/mês
- Embaixador: $0.75/cadastro, teto $200/mês
- Hall da Fama: $1.00/cadastro, sem teto
- Bônus mensal opcional: $50 para o 1º do ranking
- Prós: controle de custo, incentivo a crescer de tier
- Contras: mais complexo de comunicar

**Opção C — Crédito em plataforma (não dinheiro):**
- Pontos que dão VIP gratuito ou descontos
- Prós: custo zero real; bom para fase inicial
- Contras: menos motivador para influenciadores sérios

**Recomendação:** Começar com **Opção C** (VIP gratuito) para os primeiros 50 influenciadores. Testar engajamento. Migrar para Opção B quando tiver receita recorrente.

**Para ativar a Fase 1.3 completa, responda:**
1. Modelo de recompensa (A, B ou C)?
2. Teto de gastos mensais com influenciadores?
3. Canal de pagamento (Venmo/Zelle/PayPal/Stripe) se for A ou B?

**Status:** PENDENTE — resposta do dono necessária para completar Fase 1.3.

---

### [2026-09-28] D-007 — Provider de email para confirmação (Fase 0.1)

**Contexto:** A Fase 0.1 implementa confirmação de email. O código abstrai o envio (Resend > SMTP > log-dev). Em produção, um provider é obrigatório.

**Pergunta:** Qual provider de email usar?

**Opções:**
- **Resend** (recomendado): grátis até 3.000 emails/mês; API simples; requer domínio verificado
- **Sendgrid**: grátis até 100/dia — limite apertado para lançamento
- **SMTP Gmail**: gratuito mas com riscos de spam e limite 500/dia

**Recomendação:** Resend. Criar conta em resend.com → verificar domínio `clubeusa.com` → setar `RESEND_API_KEY` e `EMAIL_FROM=noreply@clubeusa.com` no Render (~30 min).

**Status:** PENDENTE

---

### [2026-09-15] D-003 — O app está deployado? (crítico)

**Contexto:**
Todo o código é inútil sem deployment. `render.yaml` existe mas não há confirmação de que o app está rodando em produção.

**Para responder:**
1. URL de produção? (ex: https://clubeusa.onrender.com)
2. Variáveis de ambiente configuradas? (SUPABASE_URL, SECRET_KEY, ZAPI_INSTANCE, etc.)
3. Schema SQL aplicado no Supabase?

**Status:** PENDENTE — bloqueador crítico.

---

*Atualizado em: 2026-09-28*
