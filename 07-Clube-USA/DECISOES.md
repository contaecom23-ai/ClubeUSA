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

### [2026-11-08] D-001 — MERGE PARALYSIS: 165 PRs abertos, nenhum merged

**Contexto:**
O builder autônomo roda 3x/dia e cria PRs corretamente, mas nenhum foi revisado/merged desde o início do projeto. Resultado: `main` está estagnado no estado inicial (pré-Fase 0), e cada execução reimplementa as mesmas features em novas branches.

**Estado atual do main:**
- Fase 0.1 (email): ❌ não merged (10+ PRs tentaram, o mais recente é #165)
- Fase 0.2 (referral /i/code): ❌ não merged (PR #157 está pronto)
- Fase 0.3 (analytics growth): ❌ não merged (PR #109)
- Fase 0.4 (cadastro válido): ❌ não merged (PR #104)
- Fase 1.1 (promoções): ❌ não merged (PR #113)

**O único PR NÃO-DRAFT (pronto para merge sem revisão extra):** PR #110 — 3 correções de segurança.

**Pergunta:**
Você quer revisar e mergear os PRs? Ou prefere uma abordagem diferente (ex: dar permissão para fazer merge direto em main)?

**Opções:**

**Opção A — Você revisa e mergeou manualmente (recomendado)**
Prós: processo correto, você mantém controle, PRs estão bem documentados
Contras: requer sua ação; sem isso o projeto não avança
Merge sugerido nesta ordem:
1. PR #110 (security fixes — único não-draft, merge fácil)
2. PR #165 (email verification — mais recente, baseado no main atual)
3. PR #157 (referral redirect)
4. PR #109 (analytics growth)
5. PR #104 (cadastro válido)
Depois disso: fechar os ~160 PRs duplicados mais antigos.

**Opção B — Squash: builder cria 1 PR com tudo de Fase 0 completo**
Prós: 1 review, 1 merge para fechar a Fase 0 inteira
Contras: PR maior, mais difícil de revisar; requer sua aprovação explícita aqui
Para ativar: responda "sim, crie um PR de Fase 0 completo"

**Opção C — Conceder permissão de merge direto**
Recomendação: NÃO. Merge sem revisão humana é risco real para produção.

**Minha recomendação:** Opção A. Comece pelo PR #110 (5 minutos de review). Depois PR #165. São os dois mais limpos e urgentes.

**Status:** PENDENTE — aguardando ação do dono

---

*Atualizado em: 2026-11-08*
