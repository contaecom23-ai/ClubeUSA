# ROADMAP — Clube USA

> Fonte da verdade do projeto. `[x]` = código completo e no `main`. `[~]` = código pronto em branch, aguarda merge/infra. `[ ]` = pendente.

---

## Estado real do projeto (2026-10-23)

O código base (`main`) contém a plataforma WhatsApp/deals completa, empurrada diretamente pelo dono em 2026-08-18. Os 90+ PRs de runs anteriores foram construídos sobre uma versão antiga do `main` e são incompatíveis com o código atual — podem ser fechados.

**Bloqueio de deploy:** infraestrutura não configurada (ver DECISOES.md: Supabase, email, hosting, domínio).

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [~] **0.1** Cadastro + perfil mínimo + email confirmado
  - Cadastro + perfil + OTP WhatsApp: **✓ em main**
  - Email confirmado (campo `email_confirmed` + fluxo de confirmação): `[ ]` pendente — depende de SMTP (D-003)
- [x] **0.2** Sistema de REFERRAL rastreável (`referral_code`, tabela `referrals`, `GET /member/referral`): **✓ em main**
- [~] **0.3** Analytics básico — **código pronto neste PR** (migration + analytics_service + endpoints `/admin/analytics` + auto-tracking de eventos key)
- [~] **0.4** "Cadastro válido" verificável — **código pronto neste PR** (`GET /member/validation-status` + campo `email_confirmed` na migration)

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [x] **1.1** PROMOÇÕES/ACHADOS — tabela `deals`, curadoria admin, `/member/deals`, score + aprovação: **✓ em main**
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO
- [ ] **1.4** Empregos (seed manual)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
- [x] **1.6** Rastreador de preço de produto multi-marketplace + alertas + cupons: **✓ em main**

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

*Atualizado em: 2026-10-23 — Fase 0.3 + 0.4 implementadas (PR claude/fase-0.3-analytics-0.4-validacao). Próxima: Fase 0.1 conclusão (email confirmado) após D-003 + Fase 1.2 ZIP search.*
