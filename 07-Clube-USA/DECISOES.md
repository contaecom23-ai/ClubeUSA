# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ BLOQUEIO CRÍTICO — Leia este item primeiro

### [2026-07-19] TRIAGEM ATUALIZADA: 27 PRs abertos, nada mergeado — 7ª vez notificando

**Contexto:** Hoje é 2026-07-19. O agente roda 3x/dia desde ~2026-07-11 e gerou 27 PRs. Nenhum foi mergeado. Esta run NÃO criou PR novo porque reconhece o bloqueio. **O loop de duplicatas retomará em runs futuras enquanto o main não tiver nenhum merge.** A implementação completa já existe — Fases 0.1 a 1.5 codificadas. O único obstáculo é você apertar "Merge" nos PRs abaixo na ordem indicada.

**Novidade desta run:** PR #27 (`feature/fase-0.1-cadastro-email`, criado 2026-07-18) é a versão mais recente e melhor de Fase 0.1. Substituí PR #18 como recomendado. Diferenças: access token de 1h (mais seguro) + adaptador de email com 3 drivers (log/Resend/SendGrid) + frontend mais completo.

**Pergunta:** Quais PRs fechar e em que ordem mergear?

**Recomendação do Claude — plano em 3 passos:**

---

#### PASSO 1 — FECHAR duplicatas (16 PRs) — pode fazer agora

Feche com motivo "Superseded by PR #27":

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
| #18 | `claude/fase-0-cadastro-auth` | Fechar (superseded por PR #27, mais seguro) |
| #22 | `feat/fase-0.1-cadastro-auth` | Fechar |
| #23 | `feature/fase-0.1-cadastro` | Fechar |
| #24 | `claude/fase-0-cadastro-perfil-email` | Fechar |
| #25 | `feat/fase-0-1-cadastro-auth` | Fechar |
| #26 | `claude/fase-0-1-cadastro` | Fechar |

---

#### PASSO 2 — MERGEAR em ordem (11 PRs que ficam)

Merge na ordem abaixo — cada um pode depender do anterior no main:

| Ordem | PR | O que entrega |
|---|---|---|
| 1 | **#21** (este PR) | Atualiza DECISOES.md + ROADMAP.md no main com este plano |
| 2 | **#27** `feature/fase-0.1-cadastro-email` | **Fase 0.1** — cadastro, login, perfil, email confirmado (melhor versão) |
| 3 | **#9** `claude/fase-0-security-polish` | Security polish: headers HTTP, senha forte real |
| 4 | **#3** `claude/fase-0.2-referral` | **Fase 0.2** — referral rastreável |
| 5 | **#4** `claude/fase-0.3-analytics` | **Fase 0.3** — analytics básico |
| 6 | **#5** `claude/fase-0.4-valid-registration` | **Fase 0.4** — cadastro válido + anti-fraude |
| 7 | **#12** `claude/fase-1.1-promocoes` | **Fase 1.1** — promoções/achados |
| 8 | **#14** `claude/fase-1.2-busca-zip` | **Fase 1.2** — busca por ZIP + raio |
| 9 | **#16** `claude/fase-1.3-influenciadores` | **Fase 1.3** — influenciadores pago por resultado |
| 10 | **#19** `claude/fase-1.4-empregos` | **Fase 1.4** — board de empregos |
| 11 | **#20** `claude/fase-1.5-moradia` | **Fase 1.5** — moradia/roommates |

> **Aviso real:** PRs #3–#20 foram criados sem 0.1 no main. Podem ter conflitos de schema/imports. Se houver conflito ao mergear, me informe e resolvo em 1 ciclo.

---

#### PASSO 3 — Depois de mergear PR #27, me diga e eu continuo

Com 0.1 no main posso: integrar email transacional real (ver decisão abaixo), rodar a migration no Supabase, e avançar pelo ROADMAP em ordem. **Enquanto o main não tiver nenhum merge, o agente continuará reconhecendo o bloqueio e não criará novos PRs — mas também não avança.**

**Status:** PENDENTE — aguardando ação do dono

---

## Decisões Pendentes

### [2026-07-11] Provedor de email transacional

**Contexto:** A Fase 0.1 (PR #27) está pronta. O fluxo de verificação de email funciona em modo `log` (imprime no terminal). Para produção precisa de um provedor real.

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

**Contexto:** O backend (PR #27) está pronto para deploy mas precisa de variáveis de ambiente reais. Todas documentadas em `07-Clube-USA/backend/.env.example`.

**O que preciso:**
- `SUPABASE_URL` — ex: `https://xyzxyz.supabase.co`
- `SUPABASE_SERVICE_ROLE_KEY` — de Project Settings → API → service_role
- `JWT_SECRET` — posso gerar: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- `APP_BASE_URL` — domínio final (ex: `https://clubeusa.com`)

**Ação:** Com essas informações, rodo a migration `001_users.sql` no Supabase e o sistema fica live.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-19 | Histórico: 20 PRs (2026-07-12) → 24 (2026-07-14) → 25 (2026-07-16) → 26 (2026-07-17) → 26 (2026-07-18) → 27 (2026-07-18 noite, PR #27 é o melhor 0.1) → 27 (2026-07-19, nenhum novo — agente em modo bloqueio)*
