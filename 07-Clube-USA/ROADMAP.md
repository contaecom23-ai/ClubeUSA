# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.

---

## ESTADO REAL EM 2026-08-20

O código em `07-Clube-USA/clubeusa/` (branch `main`) **já implementa mais do que o ROADMAP indicava**:

| O que já existe em `main` | Rota / Módulo |
|---------------------------|---------------|
| Registro por telefone + WhatsApp OTP | `POST /auth/register`, `POST /auth/otp/*` |
| Perfil de membro | `GET/PATCH /member/profile` |
| Referral com código único + stats | `GET /member/referral` |
| Promoções/deals por categoria | `GET /member/deals` |
| Rastreador de preço com alertas | `GET/POST /products/track`, `/alerts` |
| Painel admin completo | `GET /admin/*` |
| Billing Stripe (VIP $4,99/mês) | `POST /billing/*` |
| Segurança: rate-limit, OTP TTL, HMAC Stripe | middlewares |

**18 PRs abertos, nenhum merged.** 4 bloqueios críticos em DECISOES.md.

---

## FASE 0 — PRÉ-LANÇAMENTO

- [~] **0.1** Cadastro + perfil mínimo — **EXISTE em `main`** via WhatsApp OTP + `/member/profile`. Pendente: decisão do dono sobre modelo de auth (WhatsApp vs email) — ver DECISOES.md #2.
- [~] **0.2** REFERRAL rastreável — **backend EXISTE em `main`** (`/member/referral`, código único gerado no cadastro, stats, histórico). Pendente: merge PR #52 (redirect `/i/{code}`) e PR #57 (captura `?ref=` no frontend).
- [ ] **0.3** Analytics básico — PR #55 aberto e pronto para merge (baseado em `main` atual).
- [ ] **0.4** "Cadastro válido" verificável + anti-fraude — PR #58 aberto e pronto para merge (baseado em `main` atual).

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [~] **1.1** PROMOÇÕES/ACHADOS = carro-chefe — **backend EXISTE em `main`** (`/member/deals`, scanner automático, aprovação admin). Pendente: avaliação do produto com usuários reais.
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas — PR #14 (stacked em branch antiga, não merged).
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO — PR #16 (stacked em branch antiga, não merged).
- [ ] **1.4** Empregos (seed manual) — PR #19 (stacked em branch antiga, não merged).
- [ ] **1.5** Moradia (quartos/roommates/casas) — PR #20 (stacked em branch antiga, não merged).
- [x] **1.6** Rastreador de preço de produto — COMPLETO em `main` (`/products/track`, cupons, alertas, Playwright).

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

*Atualizado em: 2026-08-20*
