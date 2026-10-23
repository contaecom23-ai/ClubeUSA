# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ BLOQUEIO CRÍTICO — LEIA ISTO PRIMEIRO

### [2026-10-23] D-001: PARALISIA DE MERGE — O projeto está parado

**Contexto:**
- O Claude roda 3x/dia desde ~junho/2026 criando PRs.
- O dono **não mergeu nenhum PR** em ~5 meses.
- Hoje há **30+ PRs abertos**, muitos duplicando o mesmo trabalho (Fase 0.1 aparece em ≥10 PRs diferentes).
- A branch `main` ainda tem o ROADMAP de junho/2026 com **0 tarefas concluídas**.
- Continuar criando PRs sem merge é **contraproducente**: acumula ruído, não avança o produto.

**O que o Claude está fazendo errado (honestidade técnica):**
Ao criar novo PR a cada run sem verificar se o anterior foi merged, o Claude entra em loop. Este PR é o último até você agir.

**Pergunta:** Você vai revisar e mergear ao menos UM PR agora para desbloquear o projeto?

**Ação recomendada (ordem):**
1. **Mergear PR #125** — "feat(fase-0): CONSOLIDADA 0.1+0.2+0.3+0.4 ✅ PRONTO PARA MERGE"
   - Cobre Fases 0.1+0.2+0.3+0.4 de uma vez
   - Substitui ~15 PRs duplicados
   - Depois de mergear #125, feche os PRs #115, #117, #119, #121, #123, #127, #128, #129, #130, #132, #133, #134 (todos fazem a mesma coisa)
2. **Mergear PR #135** — fix de segurança (proxy headers + OTP timing-safe)
3. Fechar todos os demais PRs de docs (#111, #112, #114, #118, #122, #124, #126, #131, #136, #137, #138) — são relatórios de status, não código

**Depois disso:** O Claude retoma na Fase 1.1 (Promoções/Achados), sem duplicar nada.

**Se você NÃO quer mais PRs automáticos:** Diga para desativar o schedule. É uma decisão válida.

**Status:** PENDENTE — aguardando ação do dono

---

## Decisões Pendentes (secundárias — resolver depois do D-001)

### [2026-10-23] D-002: Email transacional (para envio de confirmação de email)

**Contexto:** A Fase 0.1 exige envio de email de confirmação. Precisa de um provider (Resend, SendGrid, AWS SES).

**Pergunta:** Qual provider usar e qual conta/chave configurar?

**Opções:**
- **Resend** (recomendado para início): gratuito até 3000 emails/mês, fácil integração. Exige conta + API key.
- **SendGrid**: plano grátis 100/dia. Mais complexo.
- **AWS SES**: barato em escala, mas precisa verificação de domínio e conta AWS.

**Recomendação:** Resend. Criar conta em resend.com, gerar API key, configurar `RESEND_API_KEY` no ambiente.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-23*
