# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas
de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica,
qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ DIAGNÓSTICO CRÍTICO — 2026-10-25

**Estado real do projeto hoje:**
- `main` branch: contém a API do dealscanner (pré-existente), mas **ZERO** funcionalidades
  da Fase 0 (cadastro por email, referral, analytics, validação) foram mescladas.
- PRs abertos: **~35 PRs**, quase todos implementando a mesma coisa (confirmação de email
  Fase 0.1). Nenhum foi mergeado em meses.
- Resultado: o agente roda 3x/dia, cria novo PR, o PR nunca é aprovado, o agente não avança,
  repete. **Loop improdutivo.**

**Causa raiz:** O projeto está bloqueado por falta de merge de PRs, não por falta de código.
Existe código suficiente para avançar — ele só não entrou na `main`.

---

## Decisões Pendentes

---

### D-001 [2026-10-25] — DESBLOQUEIO URGENTE: qual PR mergear

**Contexto:**
Há ~35 PRs abertos, com múltiplas implementações das mesmas features (Fase 0.1, 0.2, 0.3, 0.4).
O agente autônomo não pode fazer merge — isso é prerrogativa do dono.
Enquanto nenhum PR entrar na `main`, o agente continuará criando PRs duplicados.

**Pergunta:** Qual PR você vai mergear para desbloquear o projeto?

**PRs candidatos (do mais completo para o mais recente):**

| PR | Branch | Cobertura | Status |
|----|--------|-----------|--------|
| [#125](https://github.com/contaecom23-ai/ClubeUSA/pull/125) | feat/fase-0-CONSOLIDADA | **0.1 + 0.2 + 0.3 + 0.4** (tudo Fase 0) | Aberto |
| [#144](https://github.com/contaecom23-ai/ClubeUSA/pull/144) | feature/0.1-email-confirmation | 0.1 apenas | Aberto (mais recente) |
| [#141](https://github.com/contaecom23-ai/ClubeUSA/pull/141) | claude/fase-0.3-analytics-0.4-validacao | 0.3 + 0.4 | Aberto |

**Opções:**

- **Opção A — Mergear PR #125 (RECOMENDADA):** Cobre toda a Fase 0 de uma vez.
  - Pros: um merge desbloqueia tudo; fecha as 4 primeiras tarefas do roadmap.
  - Contras: PR mais antigo, pode ter pequenas divergências de estilo com os mais recentes.
  - Ação extra necessária: fechar manualmente os ~30 outros PRs duplicados como "superseded".

- **Opção B — Mergear PR #144 depois #141:** Dois merges, funcionalidades mais recentes.
  - Pros: código mais novo.
  - Contras: dois merges + ainda precisa fechar os ~30 PRs restantes.

- **Opção C — Fechar todos os PRs e recomeçar do zero:** Só faz sentido se o código estiver muito desatualizado.
  - Não recomendado — o código dos PRs está bom tecnicamente.

**Recomendação do Claude:** **Opção A — Merge PR #125.**
É o PR mais completo, foi criado especificamente para resolver esse deadlock.
Após o merge, o agente pode avançar para Fase 1.1 (Promoções/Achados).

**Status:** PENDENTE ← **AÇÃO DO DONO NECESSÁRIA**

---

### D-002 [2026-10-25] — Limpeza de PRs após merge

**Contexto:**
Após mergear um PR da Fase 0, restam ~30+ PRs abertos que implementam as mesmas features
e se tornam obsoletos. Eles criam ruído no repositório.

**Pergunta:** Você quer que o agente feche os PRs obsoletos automaticamente após o merge?

**Opções:**

- **Opção A — Claude fecha os PRs duplicados automaticamente** após o merge do PR escolhido.
  - Pros: repositório limpo; o agente pode identificar quais são duplicatas.
  - Contras: ação irreversível (PRs fechados podem ser reabertos mas é ruído).

- **Opção B — Você fecha manualmente os PRs que quiser.**
  - Pros: controle total.
  - Contras: trabalho manual.

**Recomendação:** Opção A — após confirmar o merge do PR escolhido em D-001,
o Claude fecha os PRs duplicados na próxima execução.

**Status:** PENDENTE ← aguarda resolução de D-001

---

### D-003 [2026-10-25] — Escopo do agente autônomo (frequência vs. valor)

**Contexto:**
O agente roda 3x/dia. Enquanto o projeto está bloqueado por merge paralysis, cada execução
cria um PR duplicado sem valor. Isso não é culpa da configuração — é uma consequência de PRs
nunca serem mergeados.

**Pergunta:** Após o merge inicial, quer ajustar a frequência do agente?

**Opções:**

- **Opção A — Manter 3x/dia:** Faz sentido quando o projeto está avançando normalmente.
- **Opção B — Reduzir para 1x/dia:** Menos PRs, mas menos progresso.
- **Opção C — Pausar o agente até você mergear D-001:** Evita mais duplicatas enquanto o bloqueio não é resolvido.

**Recomendação:** Opção C temporariamente — pause a execução automática até o merge
de D-001 ser feito. Depois retome em 1x/dia enquanto você acompanha de perto.
Volte a 3x/dia quando o ritmo de merge estiver saudável (1 merge por semana ou mais).

**Status:** PENDENTE — sua decisão

---

## Decisões Concluídas

*(nenhuma ainda)*

---

*Atualizado em: 2026-10-25 — por agente autônomo*
