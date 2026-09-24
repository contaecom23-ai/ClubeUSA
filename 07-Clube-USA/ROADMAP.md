# ROADMAP — Clube USA

> Fonte da verdade do projeto. `[x]` = no main. `[p]` = PR aberto aguardando merge. `[ ]` = não iniciado.

---

## REGRAS DE SEGURANÇA (obrigatórias em todo código)
- Auth global: TODA rota exige token válido; rotas públicas: home, status, login, registro (rate-limit), webhook Stripe (HMAC)
- Multi-tenant: todo dado isolado por user_id do servidor (token), nunca do cliente; acesso a recurso de outro retorna 404
- RLS no Supabase como endgame; até lá, acesso apenas server-side com service_role; nunca expor anon key
- Segredos via env var; senhas hash forte; tokens TTL curto (7 dias max) + refresh
- Rate-limit em login/registro; XSS/SQLi/IDOR protegidos; CORS restrito; uploads com validação de tipo/tamanho
- Webhooks com verificação de assinatura + janela anti-replay; nunca expor PII em logs

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [p] **0.1** Cadastro + perfil mínimo + email confirmado — **PR #106** (precisa: SMTP env vars + migração SQL)
- [p] **0.2** Sistema de REFERRAL rastreável (link `/i/{code}` + atribuição) — **PR #102**
- [p] **0.3** Analytics básico — série temporal de crescimento diário — **PR desta sessão** (sem migração, usa dados existentes)
- [p] **0.4** Definição de "cadastro válido" verificável + anti-fraude — **PR #104**

> **⚠️ AÇÃO NECESSÁRIA**: Mergear PRs #106 → #102 → #104 + este PR de analytics. Ver DECISOES.md D-001.

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [p] **1.1** PROMOÇÕES/ACHADOS = carro-chefe — **PR #97**
- [p] **1.2** Busca por ZIP + raio 1–5 milhas — **PR aberto**
- [p] **1.3** Programa de influenciadores PAGO POR RESULTADO — **PR #96**
- [p] **1.4** Empregos (seed manual) — **PR #93**
- [p] **1.5** Moradia (quartos/roommates/casas) — **PR #94**
- [x] **1.6** Rastreador de preço de produto (Amazon/Walmart/BestBuy + histórico + alertas)

---

## FASE 2 — RECEITA RÁPIDA

- [p] **2.1** Assinatura de empresas locais $10–30/mês — **PR #105**
- [ ] **2.2** Diretório de empresas
- [ ] **2.3** Publicidade local por região
- [ ] **2.4** Leilão de destaque por categoria/ZIP

---

## FASE 3 — CONFIANÇA E REDE

- [ ] **3.1** Reviews/reputação
- [ ] **3.2** Ranking comunitário
- [ ] **3.3** Conteúdo da comunidade (Q&A)
- [ ] **3.4** Gamificação (Contributor, Trusted Member, Community Guide)

---

## FASE 4 — INTELIGÊNCIA

- [ ] **4.1** IA CONCIERGE
- [ ] **4.2** Sistema de INTENÇÃO (mudança de cidade, seguro, emprego, moradia)
- [ ] **4.3** Personalização não-sensível

---

## FASE 5 — MONETIZAÇÃO PESADA

- [ ] **5.1** LEADS (seguros, advogados, dentistas; lead premium verificado)
- [ ] **5.2** Serviços financeiros (corretagem de seguros, remessas — COMISSÃO)
- [ ] **5.3** Produtos próprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B (seguradoras, bancos, imobiliárias)

---

*Atualizado em: 2026-09-24*
