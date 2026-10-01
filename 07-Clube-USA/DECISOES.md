# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## ESTADO CRÍTICO — 2026-10-01

Este projeto está em **paralisia de merge há 99 dias** (desde 2026-06-23). O agente continuou criando PRs conforme as instruções, mas sem nenhum merge, o main ficou congelado e a fila acumulou.

**Resultado:** 31 PRs abertos, features 0.1–1.4 implementadas e testadas em branches, nenhuma em produção. Múltiplas duplicatas da mesma feature (ex: feature 0.1 tem 4 PRs separados: #75, #106, #115, #121).

O agente está suspendendo a criação de novas PRs de feature até a D-001 ser resolvida.

---

## Decisões Pendentes

### D-001 [2026-10-01] PARALISIA DE MERGE — ação humana urgente

**Histórico:** Registrado em PRs #69, #72, #73, #74, #76, #77, #79, #81, #111, #114, #118. Sem resolução.

**Situação atual:**
O `main` tem o app base (landing page + API completa com auth, deals, Stripe, Supabase). Features completas vivem em branches:

| PR | Feature | Estado |
|---|---|---|
| #110 | fix(security): 3 correções críticas | PRONTO, não-draft |
| #103 | test: 48 testes de cobertura | PRONTO |
| #121 | feat: email confirmation (0.1) + /i/{code} (0.2) | PRONTO |
| #119 | feat: analytics básico (0.3) | PRONTO |
| #104 | feat: cadastro válido + anti-fraude (0.4) | PRONTO |
| #113 | feat: Promoções/Achados (1.1) | PRONTO |
| #116 | feat: influencer tiers (1.3) | PRONTO |
| #120 | feat: Empregos (1.4) | PRONTO |

**Pergunta objetiva para o dono:**
Você quer que eu:

**Opção A:** Você mergeia os PRs na ordem acima (começa pelo #110) e o agente continua a partir daí.
- Pró: código funcional entra em produção, base para crescer
- Contra: exige ~30 minutos de revisão sua agora

**Opção B:** Você fecha todos os PRs antigos e pede um PR único e limpo de tudo.
- Pró: revisão mais simples (1 PR vs 8)
- Contra: os PRs já têm código testado; reconstruir em 1 PR é trabalho extra

**Opção C:** O agente para completamente e aguarda instrução explícita sua.
- Pró: não acumula mais PRs
- Contra: projeto fica parado

**Recomendação:** Opção A. Comece pelo PR #110 (segurança, crítico). Se travar em algum conflito, me chame.

**Ordem de merge recomendada:**
1. PR #110 — segurança (não-draft, pronto para merge)
2. PR #103 — testes
3. PR #121 — email confirmation + referral (supersede #75, #106, #115, #117, #112)
4. PR #119 — analytics (supersede #109)
5. PR #104 — cadastro válido
6. PR #113 — promoções
7. PR #116 — influencer tiers
8. PR #120 — empregos

**PRs para fechar (duplicatas/supersedidos):**
#69, #70, #71, #72, #73, #74, #75, #76, #77, #78, #79, #80, #81, #102, #106, #109, #111, #112, #114, #115, #117, #118

**Status:** PENDENTE — aguardando decisão do dono

---

### D-002 [2026-09-28] Provider de email para confirmação (Fase 0.1)

**Contexto:** PR #121 implementa email confirmation mas precisa de provider real em produção.

**Opções:**
- **Resend** (resend.com) — grátis 3k emails/mês, API simples. Variável: `RESEND_API_KEY`
- **SendGrid** — grátis 100/dia. Variável: `SENDGRID_API_KEY`
- **SMTP** (Gmail/Zoho). Variáveis: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`

**Recomendação:** Resend — setup em 5 minutos, zero custo para os primeiros 1.000 usuários.

**Ação:** Criar conta em resend.com → verificar domínio clubeusa.com → adicionar `RESEND_API_KEY` no Render.

**Status:** PENDENTE (depende de D-001 ser resolvida primeiro)

---

*Atualizado em: 2026-10-01*
