# ROADMAP — Clube USA

> Fonte da verdade do projeto. `[x]` = concluído e no `main`. `[p]` = pronto em PR, aguarda merge. `[ ]` = não iniciado.

**Legenda de estado:**
- `[x]` — Implementado e no `main` (produção)
- `[p]` — Implementado em PR aberto (aguarda merge pelo dono)
- `[ ]` — Não iniciado

---

## REGRAS DE SEGURANÇA (obrigatórias em toda feature)

- Auth global: TODA rota exige token válido; rotas públicas explicitamente listadas
- Multi-tenant: todo dado isolado por `user_id` do token (nunca do request body)
- Segredos: sempre via env var, nunca hardcoded
- Senhas/tokens: TTL curto (7 dias JWT), refresh obrigatório
- Rate-limit: 5 req/min em `/auth`, 60 req/min geral
- XSS/SQLi: queries parametrizadas, sanitização de inputs
- Stripe webhook: verificação HMAC obrigatória
- Nunca expor PII ou segredos em logs

---

## ESTADO ATUAL DO `main` (2026-09-23)

O backend **já funciona** em produção com:
- Cadastro (`POST /auth/register`) com phone, name, email (opcional), referral_code
- Login por OTP WhatsApp (`POST /auth/otp/request` + `/verify`) — JWT 7 dias
- Perfil, deals, leaderboard, referral stats
- Billing VIP via Stripe (checkout + portal + webhook)
- Painel admin completo
- Price alerts e product tracker
- Forum, news, AI assistant
- Rate limiting, security headers, CORS restrito

**O que o main NÃO tem ainda** (está em PRs):
- Confirmação de e-mail (PR #106)
- URL `/i/{code}` para referral (PR #102)
- Analytics time-series (PR #100)
- Definição formal de "cadastro válido" (PR #104)
- Testes automatizados (PR #103)

---

## FASE 0 — PRÉ-LANÇAMENTO

- [p] **0.1** Cadastro + perfil mínimo + email confirmado → **PR #106** (limpo, safe to merge)
- [p] **0.2** REFERRAL rastreável — link `/i/{code}` + atribuição → **PR #102** (safe to merge)
- [p] **0.3** Analytics básico (time-series de eventos) → **PR #100** (consolidado 0.2+0.3)
- [p] **0.4** "Cadastro válido" verificável + anti-fraude IP → **PR #104** (safe to merge)

> ⚠️ BLOQUEIO: nenhum PR foi mergeado ainda. Ver DECISOES.md D-001.

---

## FASE 1 — TRAÇÃO

- [ ] **1.1** PROMOÇÕES/ACHADOS — curadoria, urgência → PR #97 (urgency field, safe)
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Influenciadores PAGO POR RESULTADO → PR #96 (tier tracking)
- [ ] **1.4** Empregos (seed manual) → PR #93
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro ZIP) → PR #94
- [x] **1.6** Rastreador de preço (Amazon/Walmart/BestBuy, cupons, alertas)

---

## FASE 2 — RECEITA RÁPIDA

- [p] **2.1** Assinatura de empresas locais $10–30/mês (free→premium) → **PR #105**
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
- [ ] **4.2** Sistema de INTENÇÃO (mudança de cidade, seguro, emprego, moradia)
- [ ] **4.3** Personalização não-sensível

---

## FASE 5 — MONETIZAÇÃO PESADA

- [ ] **5.1** LEADS (seguros, advogados, dentistas, contractors)
- [ ] **5.2** Serviços financeiros (corretagem de seguros, remessas — preferir COMISSÃO)
- [ ] **5.3** Produtos próprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B (seguradoras, bancos, remessas, imobiliárias)

---

## PRs ABERTOS POR FASE (referência rápida)

| PR | Branch | Feature | Fase | Ação recomendada |
|----|--------|---------|------|-----------------|
| #106 | feat/fase-0.1-email-confirm-clean | Email confirmation | 0.1 | ✅ MERGEAR (requer SMTP env vars) |
| #102 | feat/0.2-referral-redirect | GET /i/{code} | 0.2 | ✅ MERGEAR |
| #103 | test/api-endpoints-coverage | 48 testes | QA | ✅ MERGEAR |
| #104 | feat/fase-0.4-valid-cadastro | Cadastro válido | 0.4 | ✅ MERGEAR |
| #100 | consolidado/fase-0.2-0.3 | Referral + analytics | 0.2/0.3 | MERGEAR se #102 não for |
| #97 | feat/fase-1.1-deal-urgency | Deal urgency | 1.1 | Aguardar Fase 1 |
| #96 | feat/fase-1.3-influencer-tiers | Influencer tiers | 1.3 | Aguardar Fase 1 |
| #94 | feat/fase-1.5-moradia | Moradia listings | 1.5 | Aguardar Fase 1 |
| #93 | feat/fase-1.4-empregos | Empregos listings | 1.4 | Aguardar Fase 1 |
| #105 | feat/fase-2.1-business-subscription | Business subscription | 2.1 | Aguardar Fase 2 |
| #107 | docs/decisoes-acao-2026-09-22 | Triage docs | docs | ❌ FECHAR (substituído) |
| #101 | docs/decisoes-roadmap-real-2026-09-19 | Triage docs | docs | ❌ FECHAR |
| #99 | docs/triage-2026-09-16 | Triage docs | docs | ❌ FECHAR |
| #95 | docs/triage-2026-09-14 | Triage docs | docs | ❌ FECHAR |
| #91 | claude/triage-roadmap-2026-09-12 | Triage docs | docs | ❌ FECHAR |
| #89 | docs/estado-real-2026-09-10 | Triage docs | docs | ❌ FECHAR |
| #88 | fix/decisoes-jwtttl-2026-09-09 | JWT TTL fix | auth | ❌ FECHAR (já corrigido no main) |
| #87 | feat/phase-0-email-confirmation | Email confirm (duplic.) | 0.1 | ❌ FECHAR (#106 é melhor) |
| #86 | decisoes/estado-real-2026-09-08 | Triage docs | docs | ❌ FECHAR |
| #85 | feat/fase-0.1-email-confirmation | Email confirm (duplic.) | 0.1 | ❌ FECHAR |
| #84 | feat/phase-0.1-email-confirmation | Email confirm (duplic.) | 0.1 | ❌ FECHAR |
| #83 | feat/0-2-referral-link | Referral (duplic.) | 0.2 | ❌ FECHAR (#102 é melhor) |
| #82 | docs/plano-merge-urgente | Plano merge | docs | ❌ FECHAR |
| #81 | docs/decisoes-criticas | Triage docs | docs | ❌ FECHAR |
| #80 | fix/deploy-config-zapi | Z-API config | deploy | ❌ FECHAR (ver se ainda se aplica) |
| #79 | docs/estado-2026-09-02 | Triage docs | docs | ❌ FECHAR |
| #78 | fix/relogin-vip-plan-token | VIP token bug | auth | ✅ REVISAR — pode ser bug real |

---

*Atualizado em: 2026-09-23*
