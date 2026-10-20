# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⛔ BLOQUEIO CRÍTICO — AÇÃO URGENTE DO DONO

### [2026-10-20] Paralisia de PRs — o projeto está parado há meses

**Contexto:**
O builder autônomo roda 3x/dia há meses. Em cada ciclo, como não encontra nenhuma PR mergeada, reimplementa as mesmas features e abre novas PRs. Resultado: **30+ PRs abertos, nenhum mergeado na main**. As features estão prontas no código (FASE 0.1, 0.2, 0.3, 0.4 — tudo implementado), mas a main está no estado inicial de 2026-06-23.

**Estado atual:**
- Main: código de junho/2026, ROADMAP sem nada marcado, este DECISOES.md vazio
- PRs abertos: ~30, a maioria implementando as mesmas coisas
- FASE 0.1 (email confirmation): implementada em 8+ branches diferentes
- FASE 0.2 (referral links): implementada em 4+ branches
- FASE 0.3 (analytics): implementada em 3+ branches

**Pergunta:**
Você precisa mergear PRs para desbloquear o projeto. Qual PR você quer mergear primeiro?

**Opções:**

**A) PR #125 — CONSOLIDADA (RECOMENDADO)**
Branch: `feat/fase-0-CONSOLIDADA`
Conteúdo: Fase 0.1 + 0.2 + 0.3 + 0.4 em um PR só, substituindo os ~15 PRs duplicados anteriores.
Pró: Um merge desbloquearia toda a Fase 0.
Contra: É um PR grande (~1.000 linhas). Revisar leva mais tempo.

**B) PR #132 — só email (Fase 0.1)**
Branch: `feature/fase-0.1-email-auth`
Pró: Menor, mais fácil de revisar.
Contra: Não avança Fase 0.2/0.3/0.4.

**C) Fechar todos os PRs e recomeçar do zero com supervisão**
Pró: Estado limpo.
Contra: Perde todo o trabalho acumulado; o builder vai recriar tudo.

**Recomendação do Claude:**
Opção A. O PR #125 é o mais completo e foi criado especificamente para consolidar o trabalho duplicado. Se preferir revisar aos poucos, comece pela Opção B e merge os outros em sequência.

**Ação concreta:**
1. Acesse: https://github.com/contaecom23-ai/ClubeUSA/pull/125
2. Revise o diff
3. Faça merge (botão verde "Merge pull request")
4. Repita para os próximos PRs

**O que acontece se você não agir:**
O builder continuará criando PRs duplicados indefinidamente. Não há nada de novo que ele possa construir sem que o código existente entre na main primeiro.

**Status:** PENDENTE — aguardando merge manual do dono

---

### [2026-10-20] Provedor de email transacional

**Contexto:** FASE 0.1 implementa confirmação de email. Precisa de um provedor.

**Opções:**
- **A) Resend** (recomendado): free 3k emails/mês, setup 10 min, `RESEND_API_KEY` no Render
- **B) SendGrid**: free 100/dia. Mais burocrático.
- **C) AWS SES**: $0.10/1k, melhor em escala, mais setup inicial.

**Recomendação:** Opção A (Resend). Sem lock-in; trivial migrar depois.

**Ação:** Criar conta em resend.com → verificar domínio `clubeusa.com` → setar `RESEND_API_KEY` no Render.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-20*
