# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

Formato de cada entrada:

```
### [DATA] Título da decisão
**Contexto:** ...
**Pergunta:** ...
**Opções:**
- Opção A: prós / contras
- Opção B: prós / contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## Decisões Pendentes

---

### [2026-09-15] D-006: Fase 1.3 — Comissões e teto de orçamento para influenciadores ⚠️

**Contexto:**
O sistema de tier de influenciadores está implementado (`/member/influencer`, `/admin/influencers`).
A infraestrutura de rastreamento funciona com os dados já existentes (referral_count por OTP verificado).
Tiers: Parceiro (≥50), Embaixador (≥250), Hall da Fama (≥1000).

O que FALTA para o produto estar completo é: quanto pagar por cadastro válido.
Isso exige uma decisão de negócio e tem custo real — por isso está aqui.

**Pergunta:**
Qual o valor de comissão por cadastro válido e qual o teto mensal por influenciador?

**Opções:**

**Opção A — Comissão fixa baixa, sem teto:**
- $0.50–$1.00 por cadastro válido (OTP verificado)
- Sem teto — paga tudo que entregar
- Prós: simples, escala automaticamente
- Contras: sem controle de custo; se viral, pode ser caro

**Opção B — Comissão em escala por tier, com teto mensal:**
- Parceiro: $0.50/cadastro, teto $50/mês
- Embaixador: $0.75/cadastro, teto $200/mês
- Hall da Fama: $1.00/cadastro, sem teto
- Bônus mensal opcional: $50 para o 1º do ranking
- Prós: controle de custo, incentivo a crescer de tier
- Contras: mais complexo de comunicar

**Opção C — Crédito em plataforma (não dinheiro):**
- Pontos que dão acesso VIP gratuito ou descontos
- Prós: custo zero real; bom para fase inicial
- Contras: menos motivador para influenciadores sérios

**Recomendação:** Começar com Opção C (pontos/VIP gratuito) para os primeiros 50 influenciadores,
testar se funciona, depois migrar para Opção B quando tiver receita de assinatura.

**Para ativar a Fase 1.3 completa, responda:**
1. Qual é o modelo de recompensa (A, B ou C)?
2. Se A ou B: tem conta bancária/Stripe para pagamentos a terceiros configurada?
3. Qual é o teto de gastos mensais com influenciadores agora?

**Status:** PENDENTE — resposta do dono necessária para completar Fase 1.3.

---

### [2026-09-15] D-001: Auth — email vs. telefone (herdado de main não-mergeado)

**Contexto:**
Várias PRs tentaram adicionar confirmação de email (PRs #75, #84, #85, #87).
O código atual em main usa WhatsApp OTP como auth primária.

**Pergunta:** A plataforma é telefone-first (recomendado) ou email obrigatório?

**Recomendação:** Telefone-first agora (OTP WhatsApp = já funciona). Email opcional.
"Cadastro válido" = OTP verificado + ≥1 ação real.

**Status:** PENDENTE

---

### [2026-09-15] D-003: O app está deployado? (crítico)

**Contexto:**
Todo o código é inútil sem deployment. `render.yaml` existe mas não há confirmação de que
o app está rodando em produção.

**Para responder:**
1. URL de produção? (ex: https://clubeusa.onrender.com)
2. Variáveis de ambiente configuradas? (SUPABASE_URL, SECRET_KEY, ZAPI_INSTANCE, etc.)
3. Schema SQL aplicado no Supabase?

**Status:** PENDENTE — bloqueador crítico.

---

### [2026-09-15] D-004: 30+ PRs sem merge — o que fazer?

**Contexto:**
Existem 30+ PRs abertas desde agosto 2026, nenhuma mergeada em main.
O app em main está desatualizado. Cada novo PR aumenta o risco de conflito.

**Ação sugerida (30 min do dono):**
1. Merge PR #95 (docs, zero risco)
2. Merge PR #88 (JWT TTL fix, baixo risco)
3. Merge PR #92 (Fase 0.2 + 0.3 redirect + analytics)
4. Merge esta PR (#96)
5. Fechar PRs antigas como "Obsoleto"

**Status:** PENDENTE — ação do dono necessária.

---

*Atualizado em: 2026-09-15*
