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

### [2026-08-24] Triagem de 27 PRs abertos (nenhum mesclado desde jul/2026)

**Contexto:**
O repositório acumulou 27 PRs abertos sem nenhum merge desde julho de 2026. O Claude está criando PRs 3×/dia mas ninguém faz review/merge. O ROADMAP.md estava congelado no estado de 23/06/2026 (antes de todo esse trabalho). Isso bloqueia toda evolução do produto — novas features ficam empilhadas em branches sem nunca chegar na main.

**Pergunta:**
Você quer fechar os PRs duplicados listados abaixo e mergear os restantes na ordem recomendada?

**PRs para FECHAR (duplicatas — o trabalho está em outros PRs mais recentes):**
- #3, #4, #5 — versões antigas de auth/cadastro (substituídas por #46 e #62)
- #14 — analytics duplicado
- #53 — duplicata de forum/news
- #59, #60 — duplicatas de produto rastreado
- #64 — duplicata menor de alertas

**Ordem de merge recomendada (do mais fundamental ao mais específico):**
1. **#56** — CI/workflow (habilita validação automática de todos os outros)
2. **#9** — segurança/deps base
3. **#46** — auth 0.1 (base de tudo; único não-draft nesta camada)
4. **#62** — consolida fases 0.2+0.3 (referral + analytics)
5. **#54, #57, #58** — fase 1.1–1.3 (deals, busca, influenciadores)
6. **#61, #63** — fase 1.4–1.5 (empregos, moradia)
7. **#67** — fase 1.6 consolidada (rastreador de preço)
8. **#65** — melhorias de admin
9. **#12, #16, #19, #20** — PRs de suporte (testes, migrations, etc.)

**Recomendação:** Fechar os 8 duplicatas primeiro (ação de baixo risco), depois mergear na ordem acima — um por vez, verificando CI em cada etapa.

**Status:** PENDENTE

---

### [2026-08-24] Preço do plano Business Premium (Fase 2.1)

**Contexto:**
A Fase 2.1 implementa assinatura premium para empresas brasileiras no diretório. O ROADMAP original dizia "$10–30/mês". É necessário definir o preço exato e criar o Price no Stripe antes de ativar em produção.

**Pergunta:**
Qual o preço mensal do plano Business Premium? E qual o diferencial que justifica esse preço vs. listagem gratuita?

**Opções:**
- **$9.99/mês** — entrada agressiva, menor barreira, bom para primeiros 50 clientes; margem menor
- **$19.99/mês** — meio-termo; cobre custos + pequena margem; benchmark competitivo no mercado imigrante
- **$29.99/mês** — topo do range original; requer diferencial claro (destaque no topo, badge verificado, leads diretos)

**Recomendação:** Começar com **$19.99/mês** + trial de 30 dias. Após 50 clientes, avaliar elasticidade de preço. Diferenciais para o premium: aparece antes das gratuitas no diretório, badge "Premium", dados de contato visíveis no diretório público.

**Ação necessária:** Criar Price no Stripe Dashboard e configurar `STRIPE_BUSINESS_PRICE_ID` no ambiente de produção.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-24*
