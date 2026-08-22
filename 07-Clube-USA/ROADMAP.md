# ROADMAP — Clube USA

> Fonte da verdade do projeto. Última leitura do código: 2026-08-22.

---

## ESTADO REAL EM 2026-08-22

O código em `07-Clube-USA/clubeusa/` (branch `main`) já implementa:

| Item | O que existe em `main` | Status |
|------|----------------------|--------|
| 0.1 Cadastro + auth | WhatsApp OTP → JWT, `/member/profile`, `/auth/register` | ✅ em main |
| 0.2 Referral backend | Código único gerado no cadastro, `/member/referral`, stats, histórico | ✅ em main |
| 0.2 Referral redirect | `/i/{code}` → captura `?ref=` no frontend | PR #62 aguarda merge |
| 0.3 Analytics | Tracking de eventos, funil de cadastro | PR #62 aguarda merge |
| 0.4 Cadastro válido + anti-fraude | Email descartável bloqueado | PR #62 aguarda merge |
| 1.1 Promoções/Deals | Scanner + aprovação admin + `/member/deals` por categoria | ✅ em main |
| 1.6 Rastreador de preço | Amazon/Walmart, cupons Playwright, alertas de queda | ✅ em main |
| Segurança webhook Z-API | Verificação de token no `/webhook/group` | PR #62 aguarda merge |

**Próxima ação do dono:** Mergear PR #62 e PR #56 (CI). Ver DECISOES.md.

---

## FASE 0 — PRÉ-LANÇAMENTO

- [x] **0.1** Cadastro + perfil mínimo — implementado via WhatsApp OTP em `main` (`/auth/register`, `/auth/otp/*`, `/member/profile`)
- [~] **0.2** REFERRAL rastreável — backend ✅ em `main` (`/member/referral`, código único, stats); redirect `/i/{code}` aguarda PR #62
- [ ] **0.3** Analytics básico — PR #62 aguarda merge
- [ ] **0.4** "Cadastro válido" + anti-fraude — PR #62 aguarda merge

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [x] **1.1** PROMOÇÕES/ACHADOS — backend em `main`, scanner automático + painel admin
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas — aguarda Fase 0 completa
- [ ] **1.3** Influenciadores pago por resultado — aguarda Fase 0 completa
- [ ] **1.4** Empregos (seed manual) — aguarda Fase 0 completa
- [ ] **1.5** Moradia (quartos/roommates/casas) — aguarda Fase 0 completa
- [x] **1.6** Rastreador de preço de produto — completo em `main`

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

*Atualizado em: 2026-08-22 (leitura do código confirmada)*
