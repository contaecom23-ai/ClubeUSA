# ROADMAP — Clube USA

> Fonte da verdade do projeto. `[x]` = merged em main. `[PR]` = implementado, PR aberto aguardando merge.

---

## REGRAS DE SEGURANÇA (obrigatórias em todo código)

- Toda rota exige token válido; lista pública explícita e mínima.
- Multi-tenant: `user_id` sempre do servidor (token), nunca do input do cliente; cross-tenant → 404.
- RLS no Supabase como endgame; acesso server-side com `service_role`; nunca expor `anon key`.
- Segredos via env var, nunca hardcoded. Senhas geradas aleatoriamente com hash forte.
- Tokens com TTL 7 dias. Rate-limit em login/registro. Proteção XSS, SQLi, IDOR.
- CORS restrito; headers de segurança ativos; validação em uploads.
- Webhooks com verificação HMAC + anti-replay.
- Nunca expor segredos ou PII em logs.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [x] **0.0** Infra base: FastAPI, Supabase, auth JWT, rate-limit, CORS, segurança headers
- [ ] **0.1** Cadastro + perfil mínimo + email confirmado *(implementado em PR, aguardando merge e decisão sobre envio de email — ver DECISOES.md D-001)*
- [PR] **0.2** Sistema de REFERRAL rastreável — link `/i/{code}` + atribuição *(PR #92)*
- [PR] **0.3** Analytics básico — série temporal de crescimento *(PR #92)*
- [ ] **0.4** Definição de "cadastro válido" (email confirmado + ≥1 ação real) + anti-fraude

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência) ← **próxima prioridade**
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO
- [PR] **1.4** Empregos — seed manual pelo admin *(PR #93, stacked em PR #92)*
- [PR] **1.5** Moradia — quartos/roommates/casas, filtro ZIP *(este PR, stacked em PR #93)*
- [x] **1.6** Rastreador de preço de produto (Amazon/Walmart/BestBuy + cupons)

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

- [ ] **5.1** LEADS (seguros, advogados, dentistas, contractors)
- [ ] **5.2** Serviços financeiros = margem alta (corretagem de seguros, remessas — COMISSÃO)
- [ ] **5.3** Produtos próprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B (seguradoras, bancos, remessas, imobiliárias)

---

## ESTADO DO PIPELINE (2026-09-13)

| Branch | Conteúdo | PR | Base |
|--------|----------|----|------|
| `feat/completa-fase-0.2-0.3` | Referral /i/{code} + Analytics série temporal | #92 → main | main |
| `feat/fase-1.4-empregos` | Vagas de emprego seed manual | #93 → PR#92 | PR#92 |
| `feat/fase-1.5-moradia` | Moradia seed manual | este PR | PR#93 |

**Para desbloquear:** merge PR #92 em main, depois #93, depois este.

---

*Atualizado em: 2026-09-13*
