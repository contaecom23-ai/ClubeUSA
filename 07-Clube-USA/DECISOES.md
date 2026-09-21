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

### [2026-09-21] D-001 — ⚠️ CRÍTICO: 100+ PRs abertos sem merge (paralisia total)
**Contexto:** Há mais de 100 PRs abertos aguardando merge desde junho/2026. Nenhum foi mesclado. O produto em `main` não reflete nenhuma das features desenvolvidas. Claude continua construindo novos PRs, mas a dívida de merge só cresce.
**Pergunta:** Você pode fazer merge dos PRs e começar a usar as features em produção?
**Recomendação:** Urgente. Sugerido:
1. Merge **PR #100** (consolidado 0.2+0.3) → fecha ~30 PRs de uma vez
2. Merge **PR #104** (Fase 0.4 anti-fraude por IP)
3. Merge **PR #103** (48 testes de cobertura)
4. Merge **PR #65** (Fase 1.2 ZIP search) — ou substituir pelo novo PR desta sessão
5. Fechar como STALE os demais duplicados (PRs #3-#99 exceto os acima)
**Status:** PENDENTE

---

### [2026-09-21] D-002 — Fase 2.1: preço dos planos empresariais
**Contexto:** PR atual (feat/fase-2.1-business-subscription) cria dois planos: `basic` e `premium`. O ROADMAP diz "$10–30/mês". Você precisa criar os produtos/preços no Stripe Dashboard e configurar as env vars.
**Pergunta:** Qual é o preço final dos planos Basic e Premium? E quais são os benefícios de cada tier?
**Opções:**
- **A:** Basic $10/mês (listagem simples) / Premium $30/mês (destaque + analytics)
- **B:** Basic $15/mês / Premium $49/mês (mais margem, menos volume)
- **C:** Outro modelo de precificação
**Ação necessária:**
1. Criar produtos no Stripe Dashboard
2. Copiar os Price IDs para `.env`:
   - `STRIPE_BUSINESS_BASIC_PRICE_ID=price_xxx`
   - `STRIPE_BUSINESS_PREMIUM_PRICE_ID=price_yyy`
**Recomendação:** Opção A. Preço de entrada baixo para adoção rápida, upgrade natural quando o valor for provado.
**Status:** PENDENTE

---

### [2026-09-21] D-003 — Fase 2.1: aprovação de empresas — manual ou automática?
**Contexto:** Empresas registradas ficam com `status=pending` até aprovação admin. O endpoint `POST /admin/businesses/{id}/approve` ativa a empresa.
**Pergunta:** Aprovação manual (padrão atual) ou automática após verificação básica?
**Opções:**
- **A (atual):** Manual — admin revisa cada empresa antes de ativar. Mais controle, não escala.
- **B:** Auto-aprovação após 24h se nenhuma flag de fraude for detectada. Escala melhor.
- **C:** Auto-aprovação imediata para planos pagos (Stripe confirmou pagamento = confiança suficiente).
**Recomendação:** Opção C para fase de lançamento — empresas que pagam têm incentivo real, risco de fraude é baixo. Mudar para A se houver abuso.
**Status:** PENDENTE

---

*Atualizado em: 2026-09-21*
