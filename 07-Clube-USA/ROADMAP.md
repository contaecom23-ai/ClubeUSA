# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> 
> ⚠️ **Estado real (2026-09-16):** O código abaixo reflete o que está na `main` (base de 2026-08-18).
> Existem 29 PRs abertos com features adicionais — nenhuma chegou à `main` ainda.

---

## REGRAS DE SEGURANÇA E CONSTRUÇÃO

- Auth global: TODA rota exige token válido; rotas públicas explícitas e mínimas
- Multi-tenant: todo dado isolado por `user_id` do token, nunca do input
- Acesso a recurso alheio retorna 404 (não vazar existência)
- RLS no Supabase como endgame; até lá, acesso só server-side com `service_role`
- Segredos via env var; nunca hardcoded
- Rate-limit em login/registro
- Proteção contra XSS, SQL injection, path traversal, IDOR
- CORS restrito a origens conhecidas
- Webhooks com verificação de assinatura HMAC
- Nunca expor segredos ou PII em logs

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [~] **0.1** Cadastro + perfil mínimo + email confirmado
  - ✅ Cadastro via phone/OTP (WhatsApp) — funciona
  - ✅ Perfil mínimo (name, phone, email, state, categories) — funciona
  - ❌ Email confirmado — código no PR #98, requer provedor de email (ver D-002)
- [~] **0.2** Sistema de REFERRAL rastreável (link único por pessoa + atribuição)
  - ✅ `referral_code` único por membro — no schema e API
  - ✅ `referred_by` atribuído no cadastro — funciona
  - ✅ `/member/referral` retorna link e stats — funciona
  - ❌ Redirect `/i/{code}` na landing page — código no PR #98, não na main
- [ ] **0.3** Analytics básico
  - ✅ `audit_logs` tabela existe e registra eventos
  - ❌ Endpoint de time-series analytics — em PR #90/92, não na main
- [ ] **0.4** "Cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude
  - Bloqueado por 0.1 (email confirmation)

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
  - ❌ `expires_at` + `is_urgent` nos deals — em PR #97, não na main
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO
  - ❌ Influencer tier tracking — em PR #96, não na main
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
  - ❌ Em PR #93, não na main
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP)
  - ❌ Em PR #94, não na main
- [x] **1.6** Rastreador de preço de produto — Amazon/Walmart/BestBuy, histórico, cupons Playwright

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

*Atualizado em: 2026-09-16*
