# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [x] **0.1** Cadastro + perfil mínimo + email confirmado
  - PR: `feat/fase-0.1-email-confirmacao`
  - Endpoint `POST /auth/email/confirm/request` (gera token 24h, envia via Resend/SMTP/log-dev)
  - Endpoint `GET /auth/email/confirm/{token}` (single-use, marca `email_confirmed_at`)
  - Campo `email_confirmed` no perfil (`GET /member/profile`)
  - Migração: `db/email_confirm_migration.sql` (coluna + tabela `email_confirm_tokens`)
  - Provider de email: ver DECISOES.md #001
- [x] **0.2** Sistema de REFERRAL rastreável — link `/i/{CODE}` → `/?ref={CODE}` (redirect com validação de código)
  - PR: mesmo `feat/fase-0.1-email-confirmacao`
  - Endpoint `GET /i/{code}` (redirect rastreável, anti-spam: código validado no DB)
  - Slug customizado (/i/joao): ver DECISOES.md #002
- [ ] **0.3** Analytics básico
- [ ] **0.4** Definição de "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido para todos, com teto de orçamento; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; opcional bônus mensal pro 1º lugar)
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
- [x] **1.6** Rastreador de preço de produto — membro cola o link de um produto (Amazon/Walmart/BestBuy), vê o histórico de preço e ofertas cruzadas nos outros marketplaces, cupons verificados automaticamente (Playwright) com selo confirmado/não confirmado, e recebe alerta quando o preço cai (recheck a cada 6h)

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

*Atualizado em: 2026-09-29*
