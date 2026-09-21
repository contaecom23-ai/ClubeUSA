# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> **Atenção**: Os itens marcados com `[PR]` têm implementação pronta em branch aguardando merge.

---

## REGRAS DE SEGURANÇA (obrigatórias em toda feature)

- Auth global: TODA rota exige token válido; lista explícita e mínima de rotas públicas.
- Multi-tenant: todo dado isolado por `user_id`; id vem SEMPRE do token, nunca do input do cliente; acesso a recurso de outro retorna 404.
- RLS (Row Level Security) no Supabase como endgame; até lá acesso só server-side com service_role; nunca expor anon key com dados sensíveis no client.
- Segredos via env var, nunca hardcoded. Tokens com TTL curto (7 dias) + refresh.
- Rate-limit em login e registro. XSS escape, SQL injection (queries parametrizadas), path traversal e IDOR.
- CORS restrito. Webhooks externos com verificação de assinatura + janela anti-replay.
- Nunca expor segredos ou PII em logs.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [PR] **0.1** Cadastro + perfil mínimo + email confirmado — `feat/fase-0.1-email-confirm-clean` (PR aberto 2026-09-21); branches anteriores: #85, #87, #98
- [PR] **0.2** Sistema de REFERRAL rastreável (link único `/i/{code}` + atribuição) — #102, #100, #92, #83
- [PR] **0.3** Analytics básico — #90, #92
- [PR] **0.4** Definição de "cadastro válido" verificável + anti-fraude — #104

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [PR] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência) — #97
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [PR] **1.3** Programa de influenciadores PAGO POR RESULTADO (selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000) — #96
- [PR] **1.4** Empregos (seed manual) — #93
- [PR] **1.5** Moradia (quartos/roommates/casas, filtro ZIP — seed manual) — #94
- [x] **1.6** Rastreador de preço de produto (Amazon/Walmart/BestBuy, histórico, cupons, alertas)

---

## FASE 2 — RECEITA RÁPIDA

- [PR] **2.1** Assinatura de empresas locais $10–30/mês (free→premium) — #105
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

- [ ] **5.1** LEADS (seguros, advogados, dentistas, contractors; lead premium via concierge)
- [ ] **5.2** Serviços financeiros = margem alta (corretagem de seguros, remessas — COMISSÃO)
- [ ] **5.3** Produtos próprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B (seguradoras, bancos, remessas, imobiliárias)

---

## ESTADO REAL (2026-09-21)

| Fase | Item | Status |
|------|------|--------|
| 0.1 | Email confirmado | Branch criado, PR aberto, aguarda merge |
| 0.2 | Referral /i/{code} | Múltiplos PRs abertos, aguarda merge |
| 0.3 | Analytics | PRs abertos, aguarda merge |
| 0.4 | Cadastro válido | PR aberto, aguarda merge |
| 1.1–1.5 | Features de tração | PRs abertos, aguarda merge |
| 2.1 | Assinatura empresas | PR aberto, aguarda merge |

> **ATENÇÃO**: Nada está em produção. Ver DECISOES.md — D-004 (paralisia de merge).

*Atualizado em: 2026-09-21*
