# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ BLOQUEIO CRÍTICO — Leia este item primeiro

### [2026-07-17] TRIAGEM ATUALIZADA: 26 PRs abertos, nada mergeado, loop de duplicatas ativo

**Contexto:** As runs automáticas continuam criando PRs novos porque o `main` ainda mostra todo o ROADMAP como `[ ]` — sem nenhum merge, o agente não tem como saber o que já foi feito. Desde a última triage (2026-07-16, 25 PRs), mais 1 PR de Fase 0.1 foi criado (#26). **O loop só para quando você mergear ao menos o PR #18 (Fase 0.1) no main.**

**Pergunta:** Quais PRs fechar e em que ordem mergear?

**Recomendação do Claude — plano em 3 passos:**

---

#### PASSO 1 — FECHAR duplicatas (14 PRs) — pode fazer agora

Feche com motivo "Superseded by PR #18":

| PR | Branch | Ação |
|---|---|---|
| #1 | `claude/fase-0-cadastro-email` | Fechar |
| #2 | `claude/fase-0.1-cadastro-perfil-email` | Fechar |
| #6 | `claude/fase-0.1-cadastro-email-confirmado` | Fechar |
| #7 | `feat/fase-0.1-cadastro-perfil-email` | Fechar |
| #8 | `claude/sync-main-docs-estado-atual` | Fechar (superseded por PR #21) |
| #10 | `claude/fix-workflow-yaml-e-docs-main` | Fechar (superseded por PR #21) |
| #11 | `feat/fase-0.1-cadastro-perfil` | Fechar |
| #13 | `claude/fase-0-cadastro-perfil` | Fechar |
| #15 | `claude/fase-0-cadastro` | Fechar |
| #17 | `feature/fase-0-1-cadastro` | Fechar |
| #22 | `feat/fase-0.1-cadastro-auth` | Fechar (adicionado após triage anterior) |
| #23 | `feature/fase-0.1-cadastro` | Fechar (adicionado após triage anterior) |
| #24 | `claude/fase-0-cadastro-perfil-email` | Fechar (adicionado após triage anterior) |
| #25 | `feat/fase-0-1-cadastro-auth` | Fechar (adicionado após triage anterior) |
| #26 | `claude/fase-0-1-cadastro` | Fechar (adicionado após triage 2026-07-17) |

---

#### PASSO 2 — MERGEAR em ordem (11 PRs que ficam)

Merge na ordem abaixo — cada um pode depender do anterior no main:

| Ordem | PR | O que entrega |
|---|---|---|
| 1 | **#21** (este PR) | Atualiza DECISOES.md + ROADMAP.md no main com este plano |
| 2 | **#18** `claude/fase-0-cadastro-auth` | **Fase 0.1** — cadastro, login, perfil, confirmação de email |
| 3 | **#9** `claude/fase-0-security-polish` | Security polish: headers HTTP, senha forte real |
| 4 | **#3** `claude/fase-0.2-referral` | **Fase 0.2** — referral rastreável |
| 5 | **#4** `claude/fase-0.3-analytics` | **Fase 0.3** — analytics básico |
| 6 | **#5** `claude/fase-0.4-valid-registration` | **Fase 0.4** — cadastro válido + anti-fraude |
| 7 | **#12** `claude/fase-1.1-promocoes` | **Fase 1.1** — promoções/achados |
| 8 | **#14** `claude/fase-1.2-busca-zip` | **Fase 1.2** — busca por ZIP + raio |
| 9 | **#16** `claude/fase-1.3-influenciadores` | **Fase 1.3** — influenciadores pago por resultado |
| 10 | **#19** `claude/fase-1.4-empregos` | **Fase 1.4** — board de empregos |
| 11 | **#20** `claude/fase-1.5-moradia` | **Fase 1.5** — moradia/roommates |

> **Aviso real:** PRs #3–#20 foram criados sem 0.1 no main. Provavelmente funcionam standalone, mas pode haver conflitos de schema/imports. Se houver conflito ao mergear, me informe e resolvo.

---

#### PASSO 3 — Depois de mergear PR #18, me diga e eu continuo

Com 0.1 no main posso: integrar email transacional real (ver decisão abaixo), rodar a migration no Supabase, e avançar pelo ROADMAP em ordem. **Enquanto o main não tiver nenhum merge, o agente continuará criando PRs duplicados a cada run.**

**Status:** PENDENTE — aguardando ação do dono

---

## Decisões Pendentes

### [2026-07-11] Provedor de email transacional

**Contexto:** A Fase 0.1 (PR #18) está pronta. O fluxo de verificação de email funciona em modo `log` (imprime no terminal). Para produção precisa de um provedor real.

**Pergunta:** Qual provedor usar para envio de emails transacionais?

| Provedor | Custo | Facilidade | Recomendo? |
|---|---|---|---|
| **Resend** (resend.com) | Free até 3k/mês, depois $20/mês | Muito fácil — 1 API key, SDK Python | Sim |
| **SendGrid** | Free até 100/dia, depois $19,95/mês | Médio — mais configuração | Aceitável |
| **AWS SES** | ~$0,10 por 1k emails | Barato em escala, mas setup complexo | Para depois dos 100k |
| **Mailgun** | Free 100/dia (3 meses trial) | Médio | Aceitável |

**Recomendação:** Resend — zero custo para os primeiros 3k emails/mês, integração em 10 min. Para ativar: crie conta em resend.com, gere uma API key, adicione como secret `RESEND_API_KEY` no repositório. Eu integro no próximo ciclo.

**Status:** PENDENTE

---

### [2026-07-11] Credenciais do Supabase + domínio da app

**Contexto:** O backend (PR #18) está pronto para deploy mas precisa de variáveis de ambiente reais. Todas documentadas em `07-Clube-USA/backend/.env.example`.

**O que preciso:**
- `SUPABASE_URL` — ex: `https://xyzxyz.supabase.co`
- `SUPABASE_SERVICE_ROLE_KEY` — de Project Settings → API → service_role
- `JWT_SECRET` — posso gerar: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- `APP_BASE_URL` — domínio final (ex: `https://clubeusa.com`)

**Ação:** Com essas informações, rodo a migration `001_users.sql` no Supabase e o sistema fica live.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-17*
