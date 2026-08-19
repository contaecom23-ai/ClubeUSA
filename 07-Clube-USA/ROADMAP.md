# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
>
> Legenda: `[x]` = merged em main | `[P]` = em PR aberto, aguardando merge | `[ ]` = não iniciado

---

## REGRAS DE SEGURANÇA E CONSTRUÇÃO (obrigatórias)

- Auth global: TODA rota exige token; lista mínima e explícita de rotas públicas.
- Multi-tenant: todo dado isolado por `user_id` vindo **sempre** do token (servidor), nunca do input do cliente.
- RLS no Supabase como endgame; até lá, acesso só server-side com `service_role`. Nunca expor `anon key` com dados sensíveis.
- Segredos via env var; nunca hardcoded; sem default forjável.
- Tokens com TTL curto (7 dias) + refresh. Rate-limit em login e registro.
- XSS, SQLi, path-traversal e IDOR prevenidos. CORS restrito. Webhooks com verificação HMAC.
- Schema do banco = fonte de verdade. Toda feature nova entra com testes.

---

## ESTADO ATUAL EM MAIN (2026-08-19)

A `main` já tem código substancial:
- FastAPI completa com auth via OTP WhatsApp, rate-limit e security headers
- Cadastro de membro com `referral_code` (Phase 0.1/0.2 parcial)
- Referral link + estatísticas — `/member/referral`
- Click tracking + leaderboard — `/member/leaderboard`
- Deals listing com filtro por categoria
- Stripe VIP (checkout, portal, webhook com HMAC)
- Price alerts (ASIN) e product tracker cruzado (Amazon/Walmart/BestBuy)
- Admin panel (métricas, membros, deals, alertas)
- Routers: forum, news, assistant

**⚠️ BLOQUEIO CRÍTICO:** 18 PRs abertos, nenhum merged. Ver DECISOES.md item 1.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [P] **0.1** Cadastro + perfil mínimo + email confirmado
  - Auth via WhatsApp OTP já está em `main`; email é campo opcional
  - Email confirmation obrigatória aguardando merge: **PR #46** `[MERGEAR ESTE]`, PR #54
- [P] **0.2** Sistema de REFERRAL rastreável (link único por pessoa ex: clubeusa.com/i/joao + atribuição de qual cadastro veio de qual link)
  - Referral básico (link + stats) já em `main`
  - Redirect `/i/{code}` aguardando merge: **PR #52**, PR #57
- [P] **0.3** Analytics básico
  - Leaderboard + click tracking já em `main`
  - Painel analytics completo aguardando merge: **PR #55**
- [P] **0.4** Definição de "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude
  - Rate-limit básico já em `main`
  - Anti-fraude (bloqueio email descartável) aguardando merge: **PR #58**

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
  - Branch `claude/fase-1.1-promocoes` / PR #12 (stacked em branch, não em `main`)
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
  - Branch `claude/fase-1.2-busca-zip` / PR #14 (stacked)
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000)
  - Branch `claude/fase-1.3-influenciadores` / PR #16 (stacked)
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
  - Branch `claude/fase-1.4-empregos` / PR #19 (stacked)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
  - Branch `claude/fase-1.5-moradia` / PR #20 (stacked)
- [x] **1.6** Rastreador de preço de produto — membro cola o link (Amazon/Walmart/BestBuy), vê histórico de preço e ofertas cruzadas, cupons verificados (Playwright) com selo confirmado/não confirmado, alerta quando preço cai (recheck a cada 6h)

---

## FASE 2 — RECEITA RÁPIDA

- [ ] **2.1** Assinatura de empresas locais $10–30/mês (free→premium)
- [ ] **2.2** Diretório de empresas
- [ ] **2.3** Publicidade local por região
- [ ] **2.4** Leilão de destaque por categoria/ZIP

---

## FASE 3 — CONFIANÇA E REDE

- [ ] **3.1** Reviews/reputação
- [ ] **3.2** Ranking comunitário
- [ ] **3.3** Conteúdo da comunidade (Q&A, recomendações)
- [ ] **3.4** Gamificação (Contributor, Trusted Member, Community Guide, Verified Helper)

---

## FASE 4 — INTELIGÊNCIA

- [ ] **4.1** IA CONCIERGE (entende intenção, conecta com empresas)
- [ ] **4.2** Sistema de INTENÇÃO (mudança de cidade, seguro, emprego, moradia) = motor de lucro
- [ ] **4.3** Personalização não-sensível

---

## FASE 5 — MONETIZAÇÃO PESADA

- [ ] **5.1** LEADS (seguros, advogados, dentistas, contractors; lead premium verificado via concierge)
- [ ] **5.2** Serviços financeiros = margem alta (corretagem de seguros, remessas — preferir COMISSÃO)
- [ ] **5.3** Produtos próprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B (seguradoras, bancos, remessas, imobiliárias)

---

*Atualizado em: 2026-08-19*
