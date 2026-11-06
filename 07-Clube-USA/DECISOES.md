# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, a pergunta, opções com prós/contras e recomendação.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Decisões Pendentes

---

### [2026-11-06] D-001 — BLOQUEIO CRÍTICO: 158 PRs sem merge, projeto parado há 5 meses

**Contexto:**
O sistema automatizado (Claude rodando 3x/dia) criou 158 pull requests desde junho/2026. NENHUM foi merged para a branch `main`. Resultado: o código de produção em `main` está parado no estado de junho/2026, com auth via OTP WhatsApp mas SEM confirmação de email, SEM referral rastreável, SEM analytics. As features existem em PRs mas são invisíveis para usuários reais.

**Situação atual de main:**
- Auth: OTP via WhatsApp (Z-API) — funciona, mas depende de Z-API configurado
- Deals: sistema básico presente
- Fase 0.1 (email confirm): NÃO em main — existe em ~10 PRs diferentes
- Fase 0.2 (referral): NÃO em main — existe em ~5 PRs diferentes
- Fase 0.3 (analytics): NÃO em main — existe em 1 PR
- Fase 0.4 (cadastro válido): NÃO em main

**Pergunta:**
Qual dos PRs existentes você quer mergear AGORA para desbloquear o projeto?

**Recomendação do Claude — merge nesta ordem:**

1. **PR #153** `feat(fase-0.1): confirmação de email — Fase 0.1 completa` (2026-11-02)
   — mais recente e mais completo para email confirm
   — URL: https://github.com/contaecom23-ai/ClubeUSA/pull/153

2. **PR #157** `feat(fase-0.2): referral redirect rastreável com atribuição completa` (2026-11-05)
   — mais recente para referral
   — URL: https://github.com/contaecom23-ai/ClubeUSA/pull/157

3. **PR #158** `fix(security): 3 correções auditadas em main` (2026-11-05)
   — correções de segurança: PII em logs, OTP timing, CSP
   — URL: https://github.com/contaecom23-ai/ClubeUSA/pull/158

**Ação mínima para desbloquear:** Mergear APENAS o PR #153 já coloca email confirmation em produção e marca Fase 0.1 como concluída.

**Aviso honesto:** Existem múltiplos PRs para a mesma feature (ex: 10 versões de email confirm). Apenas os listados acima são os mais recentes; os mais antigos podem ser fechados sem perda.

**Status:** PENDENTE

---

### [2026-11-06] D-002 — Continuar criando PRs sem merge faz sentido?

**Contexto:**
Rodando 3x/dia durante 5 meses, o sistema criou 158 PRs sem um único merge. Cada run adiciona ~1 PR novo à pilha. A razão do backlog cresce mais rápido que é possível de revisar individualmente.

**Pergunta:**
Como quer que o sistema opere enquanto o merge paralysis persiste?

**Opções:**

- **A) Continuar como está** — sistema cria PRs, você revisa quando puder.
  - Pró: nenhuma mudança necessária da sua parte agora
  - Contra: a pilha continuará crescendo; PRs mais antigos ficam obsoletos e precisam de cleanup

- **B) Pausar criação de novas features** — Claude só cria PRs de segurança/bug fix até você fazer o primeiro merge.
  - Pró: para de acumular PRs redundantes; mais fácil de retomar
  - Contra: projeto não avança

- **C) Mudar modelo: Claude commita direto na main (sem PR)** — mais rápido, sem revisão.
  - Pró: projeto avança imediatamente
  - Contra: sem revisão humana; risco maior de erros em produção; contrário às regras atuais

- **D) Fechar todos os PRs abertos e recomeçar do zero** — cleanup completo, novo ciclo limpo.
  - Pró: repositório limpo; mais fácil de revisar
  - Contra: você perde o histórico das implementações (mas o código pode ser recuperado dos branches)

**Recomendação:** Opção B até você mergear pelo menos PR #153 e #157. Depois retomar com criação normal de PRs.

**Status:** PENDENTE

---

## Histórico de Decisões

*(nenhuma aprovada/rejeitada ainda)*

---

*Atualizado em: 2026-11-06*
