# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> **Última sincronização com main: 2026-09-12**

---

## REGRAS DE SEGURANÇA (obrigatórias — ver DECISOES.md para bloqueios externos)

- Auth global: TODA rota exige token válido; rotas públicas explícitas e mínimas (home, status, login, registro com rate-limit, webhook Stripe com HMAC).
- Multi-tenant: todo dado isolado por `user_id` vindo do servidor (do token), nunca do cliente. Acesso a recurso de outro → 404.
- RLS Supabase como endgame; até lá, acesso somente server-side com `service_role`.
- Segredos sempre via env var, nunca hardcoded.
- Tokens JWT com TTL 7 dias.
- Rate-limit em login e registro.
- Proteção XSS, SQL injection (queries parametrizadas), IDOR.
- Webhooks externos com verificação de assinatura + janela anti-replay.

---

## FASE 0 — PRÉ-LANÇAMENTO

- [x] **0.1** Cadastro + perfil mínimo + verificação de identidade — `POST /auth/register`, `GET /member/profile`, `member_service.py`. *Verificação via OTP WhatsApp (mais forte que email); email é campo opcional.*
- [x] **0.2** Sistema de REFERRAL rastreável — código único por pessoa, atribuição no cadastro, `GET /member/referral` com stats, link curto `GET /i/{code}` → `?ref={code}` implementado.
- [x] **0.3** Analytics básico — snapshot `GET /admin/metrics` + série temporal `GET /admin/analytics?days=30` (cadastros/dia + taxa de referral). Fase 0.3 concluída em 2026-09-12.
- [ ] **0.4** "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude. *Bloqueado por decisão de produto (D-002): o que conta como "ação real"? E exige email service (D-001).*

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [x] **1.1** PROMOÇÕES/ACHADOS — sistema de deals com curadoria, filtro por categoria, admin approval workflow, envio via WhatsApp/Telegram (`/member/deals`, `dealscanner2/`, admin panel).
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido para todos, com teto; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000)
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
- [x] **1.6** Rastreador de preço de produto — Amazon/Walmart/BestBuy, cupons verificados Playwright, alertas automáticos.

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

*Atualizado em: 2026-09-12*
