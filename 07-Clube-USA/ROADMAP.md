# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> **Atualizado em: 2026-09-02** — estado reflete o que existe no código de `main`.

---

## REGRAS DE SEGURANÇA (obrigatórias em toda feature)

- Auth global: toda rota exige token válido; rotas públicas explícitas e mínimas.
- Multi-tenant: todo dado isolado por `user_id` vindo SEMPRE do servidor (token), nunca do cliente.
- RLS no Supabase como endgame; até lá, acesso só server-side com `service_role`.
- Segredos sempre via env var, nunca hardcoded.
- Rate-limit em login e registro; tokens com TTL curto (7 dias).
- Queries parametrizadas; escape de XSS; CORS restrito; headers de segurança ativos.
- Webhooks externos com verificação de assinatura HMAC + anti-replay.

---

## ESTADO REAL DO PROJETO (2026-09-02)

> O código em `main` tem substancialmente mais features do que os checkboxes abaixo indicam.
> O bloqueio **não é falta de código** — é falta de deploy. Veja DECISOES.md → D-001.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [~] **0.1** Cadastro + perfil mínimo + **phone OTP confirmado** ← implementado via Telegram/Z-API OTP; spec dizia "email confirmado" mas a estratégia mudou para phone. PR #54/#75 adicionam email como canal alternativo. **Decisão do dono necessária — ver D-003.**
- [x] **0.2** Sistema de REFERRAL rastreável — `referral_code` único por membro, `/member/referral` endpoint, atribuição automática no cadastro, leaderboard `/member/leaderboard`, UTM tracking. **Implementado no código de `main`.**
- [~] **0.3** Analytics básico — `/admin/metrics` existe (contagens básicas). Analytics de funil/crescimento diário está em PRs #55/#67 (sem merge).
- [ ] **0.4** Definição de "cadastro válido" verificável (confirmação + ≥1 ação real) + anti-fraude (email descartável, bot detection). PR #58 aberto, sem merge.

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [~] **1.1** PROMOÇÕES/ACHADOS — `/member/deals` e `/admin/deals` (curadoria, approve/reject) implementados. Frontend parcial em `platform.html`. Curadoria ativa depende de deploy.
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas — PR #65 aberto, sem merge.
- [~] **1.3** Programa de influenciadores PAGO POR RESULTADO — leaderboard implementado; lógica de pagamento e selos (Parceiro/Embaixador/Hall da Fama) não implementados ainda. **Decisão de negócio necessária — ver D-004.**
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas) — não iniciado.
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro ZIP) — PR #20 aberto, sem merge.
- [x] **1.6** Rastreador de preço de produto — Amazon/Walmart/BestBuy, histórico, cupons verificados (Playwright), alertas quando o preço cai (recheck a cada 6h). **Totalmente implementado e testado.**

---

## FASE 2 — RECEITA RÁPIDA

- [~] **2.1** Assinatura de empresas $10–30/mês — Stripe billing implementado (`/billing/subscribe`, `/billing/portal`, `/billing/webhook`). Desabilitado por enquanto (sem Stripe conectado). PR #68 aberto.
- [ ] **2.2** Diretório de empresas — não iniciado.
- [ ] **2.3** Publicidade local por região — não iniciado.
- [ ] **2.4** Leilão de destaque por categoria/ZIP — não iniciado.

---

## FASE 3 — CONFIANÇA E REDE

- [ ] **3.1** Reviews/reputação
- [ ] **3.2** Ranking comunitário
- [~] **3.3** Conteúdo da comunidade (Q&A) — fórum implementado (`/forum/` router, routers/forum.py).
- [ ] **3.4** Gamificação (Contributor, Trusted Member, Community Guide, Verified Helper)

---

## FASE 4 — INTELIGÊNCIA

- [~] **4.1** IA CONCIERGE — assistant router implementado (`routers/assistant.py`). Escopo completo não avaliado.
- [ ] **4.2** Sistema de INTENÇÃO (mudança de cidade, seguro, emprego, moradia) = motor de lucro
- [ ] **4.3** Personalização não-sensível

---

## FASE 5 — MONETIZAÇÃO PESADA

- [ ] **5.1** LEADS
- [ ] **5.2** Serviços financeiros
- [ ] **5.3** Produtos próprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B

---

## Legenda

- `[x]` = Implementado, testado, em produção (ou pronto para deploy)
- `[~]` = Implementado no código mas não em produção (aguarda deploy) ou incompleto
- `[ ]` = Não iniciado ou aguardando decisão

*Atualizado em: 2026-09-02*
