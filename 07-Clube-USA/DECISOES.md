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

### [2026-11-02] D-001 — PARALISIA DE MERGE: 153 PRs abertos, nenhum merged

**Contexto:**
O builder autônomo roda 3x/dia desde ~junho de 2026. Em cada rodada, ele lê o ROADMAP no main, vê as tarefas marcadas `[ ]`, implementa, abre PR. Como **nenhum PR foi merged ao main**, o ROADMAP nunca é atualizado, e o builder refaz o mesmo trabalho indefinidamente.

Resultado em 02/11/2026: **153 PRs abertos**, todos com código real e testado, mas 100% duplicados por feature. O projeto tem código funcional bloqueado em branches mortas.

**Pergunta:**
O que você quer que o builder faça enquanto os PRs não são merged?

**Estado atual — PRs mais maduros por feature (recomendo mergear estes):**

| Feature | PR recomendado | Data | Título |
|---|---|---|---|
| **Fase 0.1** email confirm | #46 | 2026-08-05 | "feat: Fase 0.1 — Cadastro + perfil mínimo + email confirmado [MERGEAR ESTE]" |
| **Fase 0.2** referral /i/{code} | #52 | 2026-08-17 | "feat(0.2): referral rastreável — /i/{code} redirect + captura automática" |
| **Fase 0.3** analytics | #55 | 2026-08-18 | "feat(0.3): analytics básico — funil, crescimento diário, engajamento" |
| **Fase 0.4** cadastro válido | #58 | 2026-08-19 | "feat(0.4): cadastro valido verificavel + anti-fraude (email descartável)" |
| **Fase 1.1** promoções | #12 | 2026-07-07 | "feat(1.1): PROMOÇÕES/ACHADOS — carro-chefe da plataforma" |
| **Fase 1.2** busca por ZIP | #14 | 2026-07-08 | "feat(1.2): busca de promoções por ZIP + raio 1-50 milhas" |
| **Fase 1.3** influenciadores | #16 | 2026-07-09 | "feat(1.3): programa de influenciadores pago por resultado" |
| **Fase 1.4** empregos | #19 | 2026-07-11 | "feat(1.4): empregos — board de vagas com seed manual + filtro ZIP/raio" |
| **Fase 1.5** moradia | #20 | 2026-07-12 | "feat(1.5): moradia — quartos, roommates e casas com seed manual + filtro ZIP" |
| **CI/pytest** | #56 | 2026-08-18 | "ci: workflow de testes automáticos (pytest) nos PRs" |
| **Fix security** | #61 | 2026-08-21 | "fix(security): verificar client-token Z-API no webhook" |

**Opções:**

- **Opção A — Você mergeia os PRs da tabela acima** (recomendado):
  - Merge na ordem: CI (#56) → 0.1 (#46) → 0.2 (#52) → 0.3 (#55) → 0.4 (#58) → 1.x
  - Pode haver conflitos leves (mesmo arquivo tocado em PRs diferentes); resolva favor do PR mais recente
  - Prós: projeto avança, builder para de duplicar, código chega ao main
  - Contras: ~1h do seu tempo para revisar e resolver conflitos

- **Opção B — Pausa o builder** (se quiser resolver os conflitos com calma):
  - Cancela o cron "Clube USA - Builder Autônomo (3x/dia)" em Claude Code → Settings → Scheduled Tasks
  - Resolve os PRs no seu ritmo
  - Reactive o cron quando quiser que o builder retome
  - Prós: para de acumular duplicatas agora
  - Contras: projeto fica sem progresso autônomo durante a pausa

- **Opção C — Fecha todos os PRs e inicia do zero** (opção nuclear):
  - Fecha os 153 PRs como "stale"
  - Builder retoma da Fase 0.1 com código limpo sem conflito
  - Prós: repo limpo
  - Contras: perde meses de trabalho já feito (embora tudo seja reconstruível)

**Recomendação do Claude:** **Opção A**. O trabalho já está feito e testado. O esforço para mergear ~10 PRs é bem menor que o custo de meses de código jogado fora. Comece pelo #56 (CI) e #46 (Fase 0.1) — são os mais críticos.

**Status:** PENDENTE — aguardando decisão do dono

---

*Atualizado em: 2026-11-02*
