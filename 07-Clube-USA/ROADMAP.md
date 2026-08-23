# ROADMAP — Clube USA

> Fonte da verdade do projeto. Verificado em **2026-08-23** via leitura direta de `main.py` no branch main.
> `[x]` = no código de main. `[~]` = backend existe, aguarda merge de PR. `[ ]` = não implementado.

---

## REGRAS DE SEGURANÇA E QUALIDADE (obrigatórias em toda feature)

- Auth global: TODA rota exige token válido; rotas públicas explícitas e mínimas (home, status, login, registro com rate-limit, webhook Stripe com HMAC).
- Multi-tenant: todo dado isolado por `user_id` vindo do token (nunca do cliente); acesso cruzado retorna 404.
- RLS no Supabase como endgame; até lá: acesso server-side com `service_role`; nunca expor `anon key` com dados sensíveis.
- Segredos via env var, nunca hardcoded.
- Rate-limit em login e registro. Tokens com TTL curto.
- Proteção XSS, SQL injection (queries parametrizadas), IDOR (checar dono do recurso).
- Webhooks externos com verificação de assinatura + anti-replay.
- Schema do banco é a FONTE DE VERDADE. Toda feature nova entra com suite de testes.

---

## FASE 0 — PRÉ-LANÇAMENTO

- [x] **0.1** Cadastro + perfil mínimo + WhatsApp OTP — **JÁ NO MAIN**
  - `POST /auth/register`, `POST /auth/otp/request`, `POST /auth/otp/verify` implementados
  - OTP persistido no Supabase com TTL 10min, rate-limit por IP
- [~] **0.2** Sistema de REFERRAL rastreável — backend OK no main (`/member/referral` + `referral_code`)
  - Falta redirect `/i/{code}` → aguarda **merge do PR #62**
- [~] **0.3** Analytics básico — aguarda **merge do PR #62**
- [~] **0.4** "Cadastro válido" verificável + anti-fraude — aguarda **merge do PR #58**
  - Verificar conflitos com #62 antes de mergear

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [x] **1.1** PROMOÇÕES/ACHADOS — **JÁ NO MAIN**
  - DealScanner integrado (`/admin/deals/scan`, `/admin/deals/send`)
  - `GET /member/deals` com filtro por categoria e plano (free vs VIP)
  - Admin: aprovar/rejeitar deals, listar, enviar
- [~] **1.2** Busca por ZIP + raio 1–5 milhas — aguarda **merge do PR #65**
- [ ] **1.3** Influenciadores PAGO POR RESULTADO — **PR #16** (selos Parceiro/Embaixador/Hall da Fama)
- [ ] **1.4** Empregos (seed manual) — **PR #19**
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro ZIP) — **PR #20**
- [x] **1.6** Rastreador de preço — **JÁ NO MAIN**
  - `POST /alerts`, `GET /alerts`, `DELETE /alerts/{id}`, `POST /alerts/from-link`
  - `POST /products/track`, `GET /products/track`, `GET /products/track/{id}`

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
- [ ] **3.3** Conteúdo da comunidade (Q&A)
- [ ] **3.4** Gamificação (Contributor, Trusted Member, Community Guide, Verified Helper)

---

## FASE 4 — INTELIGÊNCIA

- [ ] **4.1** IA CONCIERGE
- [ ] **4.2** Sistema de INTENÇÃO (mudança de cidade, seguro, emprego, moradia)
- [ ] **4.3** Personalização não-sensível

---

## FASE 5 — MONETIZAÇÃO PESADA

- [ ] **5.1** LEADS (seguros, advogados, dentistas, contractors)
- [ ] **5.2** Serviços financeiros (corretagem de seguros, remessas — COMISSÃO)
- [ ] **5.3** Produtos próprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B

---

*Verificado em: 2026-08-23 — leitura direta do código em main*
