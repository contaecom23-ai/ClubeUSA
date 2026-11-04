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

### [2026-11-04] D-001 — PARALISIA DE MERGE: 155+ PRs abertos, nenhum merged

**Contexto:**
O builder autônomo roda 3x/dia desde ~junho de 2026. Em cada rodada, ele lê o ROADMAP no main, vê as tarefas `[ ]`, implementa e abre PR. Como **nenhum PR foi merged ao main**, o ROADMAP nunca atualiza e o builder refaz o mesmo trabalho indefinidamente.

Resultado em 04/11/2026: **155 PRs abertos**, todos com código real, mas 100% duplicados por feature. O projeto tem código funcional bloqueado em branches mortas. Cada rodada do builder continua adicionando mais PRs ao pile — ele detectou o bloqueio, documentou em PRs #151, #149, #114, #111, #81 e ainda não houve ação.

**Pergunta objetiva:**
O que você quer que o builder faça enquanto os PRs não são merged?

---

**Estado atual — PRs mais limpos por feature (mergear estes, nesta ordem):**

| Prioridade | Feature | PR | Título |
|---|---|---|---|
| 1 | CI/pytest | #56 | feat: GitHub Actions + pytest |
| 2 | **Fase 0.1** email confirm | #46 | feat: Fase 0.1 — Cadastro + email confirmado |
| 3 | **Fase 0.2** referral /i/{code} | #52 | feat(0.2): referral rastreável |
| 4 | **Fase 0.3** analytics | #55 | feat(0.3): analytics básico |
| 5 | **Fase 0.4** cadastro válido | #58 | feat(0.4): cadastro válido + anti-fraude |
| 6 | **Fase 1.1** promoções | #12 | feat(1.1): PROMOÇÕES/ACHADOS |
| 7 | **Fase 1.2** busca ZIP | #14 | feat(1.2): busca por ZIP + raio |
| 8 | **Fase 1.3** influenciadores | #16 | feat(1.3): pago por resultado |
| 9 | **Fase 1.4** empregos | #19 | feat(1.4): empregos — board de vagas |
| 10 | **Fase 1.5** moradia | #20 | feat(1.5): moradia — quartos/roommates |

> **Nota:** PRs mais recentes para a mesma feature (ex: #153 sobre Fase 0.1) têm código duplicado e podem ser fechados como "stale" após mergear os da tabela acima.

---

**Opções:**

- **Opção A — Você mergeia os PRs da tabela acima** (recomendado):
  - Merge na ordem listada (CI primeiro para validar os demais)
  - Pode haver conflitos leves; resolva em favor do PR mais recente
  - Prós: projeto avança, builder para de duplicar, código chega ao main
  - Contras: ~1–2h para revisar e resolver conflitos

- **Opção B — Pausa o builder** (enquanto resolve os PRs com calma):
  - Cancele o cron "Clube USA Builder" em Claude Code → Settings → Scheduled Tasks
  - Resolve os PRs no seu ritmo, reative o cron depois
  - Prós: para de acumular duplicatas agora
  - Contras: sem progresso autônomo durante a pausa

- **Opção C — Fecha todos os PRs e reinicia do zero** (opção nuclear):
  - Fecha os 155 PRs como "stale"
  - Builder retoma da Fase 0.1 com código limpo e sem conflitos
  - Prós: repo limpo
  - Contras: perde meses de trabalho feito (reconstruível, mas leva tempo)

**Recomendação do Claude:** **Opção A**. O trabalho já está feito e testado. O esforço para mergear 10 PRs é muito menor que o custo de meses de código jogado fora. Comece pelo #56 (CI) e #46 (Fase 0.1).

**Se não conseguir mergear por conflitos:** me diga qual PR deu conflito (escreva no chat) — posso criar uma versão limpa que aplica direto sobre o main atual sem conflito.

**Status:** PENDENTE — aguardando decisão do dono

---

*Atualizado em: 2026-11-04*
