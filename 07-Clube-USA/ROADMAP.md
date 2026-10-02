# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
>
> **Estado atual (2026-10-02):** Main branch tem auth via WhatsApp OTP + deals + Stripe.
> Fases 0.1–1.5 existem APENAS em PRs abertos — nada foi mergeado ao main.
> **O dono precisa revisar e mergear os PRs. Ver DECISOES.md para guia de ação.**

---

## REGRAS DE SEGURANÇA (obrigatórias em toda feature)

- Auth global: toda rota exige token válido; lista explícita mínima de rotas públicas.
- Multi-tenant: todo dado isolado por `user_id`; dono vem SEMPRE do token, nunca do input do cliente.
- RLS no Supabase como endgame; até lá, acesso só server-side com `service_role`.
- Segredos sempre via env var, nunca hardcoded.
- Senhas: hash forte (bcrypt/argon2); nunca fixa.
- Tokens JWT com TTL curto (7 dias) + refresh.
- Rate-limit em login e registro.
- Proteção contra XSS, SQL injection, IDOR, path traversal.
- CORS restrito; headers de segurança ativos.
- Webhooks externos com verificação de assinatura HMAC.
- Nunca expor segredos ou PII em logs.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [ ] **0.1** Cadastro + perfil mínimo + email confirmado
  - 🔄 PR aberto: [#123](https://github.com/contaecom23-ai/ClubeUSA/pull/123) — *feat(0.1): email confirmation flow — Fase 0.1 completa* (2026-10-01)
  - ⚠️ Duplicatas antigas: #115, #106, #75, #46 — fechar após mergear #123

- [ ] **0.2** Sistema de REFERRAL rastreável (link único `/i/{code}` + atribuição)
  - 🔄 PR aberto: [#117](https://github.com/contaecom23-ai/ClubeUSA/pull/117) — *feat(fase-0.2): link de referral rastreável /i/{code}* (2026-09-28)
  - ⚠️ Duplicatas: #121, #112, #102, #71, #3 — avaliar qual mergear

- [ ] **0.3** Analytics básico (funil de cadastro + crescimento diário)
  - 🔄 PR aberto: [#119](https://github.com/contaecom23-ai/ClubeUSA/pull/119) — *feat(fase-0.3): analytics básico — funil + crescimento diário* (2026-09-29)
  - ⚠️ Duplicata: #109, #4

- [ ] **0.4** Definição de "cadastro válido" (email confirmado + ≥1 ação real) + anti-fraude
  - 🔄 PR aberto: [#104](https://github.com/contaecom23-ai/ClubeUSA/pull/104) — *feat(fase-0.4): cadastro válido + anti-fraude por IP* (2026-09-21)
  - ⚠️ Duplicata: #5

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria comunitária + urgência)
  - 🔄 PR aberto: [#113](https://github.com/contaecom23-ai/ClubeUSA/pull/113) — *feat(fase-1.1): Promoções/Achados — submit comunitário + curadoria admin* (2026-09-26)
  - ⚠️ Duplicata: #12

- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
  - 🔄 PR aberto: [#14](https://github.com/contaecom23-ai/ClubeUSA/pull/14) — *feat(1.2): busca de promoções por ZIP + raio 1-50 milhas* (2026-07-08)

- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO
  - 🔄 PR aberto: [#116](https://github.com/contaecom23-ai/ClubeUSA/pull/116) — *feat(fase-1.3): influencer tier tracking* (2026-09-28)
  - ⚠️ Duplicata: #16

- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
  - 🔄 PR aberto: [#120](https://github.com/contaecom23-ai/ClubeUSA/pull/120) — *feat(fase-1.4): Empregos — API de vagas* (2026-09-30)
  - ⚠️ Duplicata: #19

- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
  - 🔄 PR aberto: [#20](https://github.com/contaecom23-ai/ClubeUSA/pull/20) — *feat(1.5): moradia — quartos, roommates e casas* (2026-07-12)

- [x] **1.6** Rastreador de preço de produto (Amazon/Walmart/BestBuy + alertas + recheck 6h)
  - ✅ Em main (rotas `/alerts`, `/products/track`)

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

*Atualizado em: 2026-10-02*
