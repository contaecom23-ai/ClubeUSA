# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
>
> **Estado em 2026-09-16:** App ainda não deployado em produção. Código em desenvolvimento na
> branch `consolidado/fase-0.2-0.3`. PRs anteriores (#70–#99) foram substituídos por esta consolidação.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [ ] **0.1** Cadastro + perfil mínimo + email confirmado
  - Cadastro e perfil mínimo existem (schema + API). Falta confirmação de email.
  - **Bloqueado por D-002** (escolha do provedor de email: Resend / SendGrid / AWS SES).
- [x] **0.2** REFERRAL rastreável — `GET /i/{code}` redireciona para cadastro com ref pré-preenchido
  - Link formato `clubeusa.com/i/ABC123` funcionando. Atribuição via `?ref=` no frontend.
- [x] **0.3** Analytics básico — `GET /admin/analytics`: crescimento diário, cliques, referrals (30 dias)
  - Lê das tabelas existentes. Sem schema novo.
- [ ] **0.4** "Cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude
  - Depende de 0.1 estar completo.

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência, campo `expires_at`)
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Influenciadores PAGO POR RESULTADO (selos Parceiro/Embaixador/Hall da Fama)
- [ ] **1.4** Empregos (seed manual)
- [ ] **1.5** Moradia (quartos/roommates, filtro ZIP — seed manual)
- [x] **1.6** Rastreador de preço — histórico + cupons verificados (Playwright)

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
- [ ] **5.2** Serviços financeiros (corretagem de seguros, remessas — preferir COMISSÃO)
- [ ] **5.3** Produtos próprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B (seguradoras, bancos, remessas, imobiliárias)

---

*Atualizado em: 2026-09-16*
