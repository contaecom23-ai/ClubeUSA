# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## Decisões Pendentes

### D-001 [2026-09-30] PARALISIA DE MERGE — ação humana bloqueando o projeto

**Contexto:**
Este aviso foi registrado em PRs: #69, #72, #73, #74, #76, #77, #79, #81, #111, #114, #118 e agora em 2026-09-30. O branch `main` está congelado desde 2026-06-23. Há agora **31 PRs abertos** com código real implementado, nenhum mergeado. Abrir mais PRs sem merge só aumenta a dívida.

O agente NÃO vai criar mais PRs de feature enquanto esse bloqueio existir — tudo de Fases 0.1 a 1.4 já tem PR pronto.

**Pergunta objetiva:**
Qual PR você quer mergear primeiro?

**Ordem de merge recomendada (10 PRs — ~5 minutos no total):**

1. **PR #110** `fix(security)` — correções críticas de segurança — vem primeiro
2. **PR #103** `test(api)` — 48 testes de cobertura
3. **PR #121** `feat(0.1+0.2)` — email confirmation + link /i/{code} *(supersede #115, #117, #106, #102, #75)*
4. **PR #109** `feat(0.3)` — analytics de crescimento
5. **PR #104** `feat(0.4)` — cadastro válido + anti-fraude
6. **PR #113** `feat(1.1)` — Promoções/Achados submit comunitário
7. **PR #65**  `feat(1.2)` — busca por ZIP + raio
8. **PR #116** `feat(1.3)` — influencer tier tracking
9. **PR #120** `feat(1.4)` — Empregos — API de vagas *(adicionado 2026-09-29)*
10. **PR #68**  `feat(2.1)` — diretório de empresas + assinatura Stripe

Após esses 10, feche os PRs duplicados antigos (não mergear):
#119, #118, #117, #115, #114, #112, #111, #106, #102, #81, #80, #79, #78, #77, #76, #75, #74, #73, #72, #71, #70, #69, #67, #66

**Se um PR tiver conflito:** o GitHub mostra exatamente onde. Me peça um guia passo a passo se precisar.

**Status:** PENDENTE — aguardando decisão do dono

---

### D-002 [2026-09-28] Provider de email para confirmação

**Contexto:**
A feature de confirmação de email (Fase 0.1, PR #121) precisa de um provider real em produção.

**Pergunta:** Qual provider de email usar?

**Opções:**
- **Resend** (resend.com) — grátis até 3k emails/mês, API simples. Variável: `RESEND_API_KEY`
- **SendGrid** — grátis até 100/dia. Variável: `SENDGRID_API_KEY`
- **SMTP próprio** (Gmail/Zoho/etc). Variáveis: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`

**Recomendação:** Resend — setup em 5 minutos, zero custo para os primeiros 1.000 usuários.

**Ação:** Criar conta em resend.com → verificar domínio clubeusa.com → adicionar `RESEND_API_KEY` no Render.

**Status:** PENDENTE

---

*Atualizado em: 2026-09-30*
