# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

> ⚠️ **Status 2026-09-26**: Todos os itens abaixo têm código pronto em PRs aguardando merge. O main não reflete o trabalho feito. Veja DECISOES.md para a fila de merge.

- [ ] **0.1** Cadastro + perfil mínimo + email confirmado → _código pronto: [PR #106](https://github.com/contaecom23-ai/ClubeUSA/pull/106)_
- [ ] **0.2** Sistema de REFERRAL rastreável (link único por pessoa ex: clubeusa.com/i/joao + atribuição de qual cadastro veio de qual link) → _código pronto: [PR #102](https://github.com/contaecom23-ai/ClubeUSA/pull/102), correção: [PR #112](https://github.com/contaecom23-ai/ClubeUSA/pull/112)_
- [ ] **0.3** Analytics básico → _código pronto: [PR #109](https://github.com/contaecom23-ai/ClubeUSA/pull/109)_
- [ ] **0.4** Definição de "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude → _código pronto: [PR #104](https://github.com/contaecom23-ai/ClubeUSA/pull/104)_

---

## FASE 1 — TRAÇÃO (foco em UM produto)

> ⚠️ **Status 2026-09-26**: Fase 0 não mergeada. Fase 1 tem PRs parciais. Aguarda merge da Fase 0 primeiro.

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência) → _código pronto: [PR #113](https://github.com/contaecom23-ai/ClubeUSA/pull/113)_
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas → _código pronto: [PR #65](https://github.com/contaecom23-ai/ClubeUSA/pull/65)_
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido para todos, com teto de orçamento; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; opcional bônus mensal pro 1º lugar) → _bloqueado: decisão de negócio pendente (ver DECISOES.md D-003)_
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas) → _bloqueado: requer deploy + decisão de produto_
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual) → _bloqueado: requer deploy + decisão de produto_
- [x] **1.6** Rastreador de preço de produto — membro cola o link de um produto (Amazon/Walmart/BestBuy), vê o histórico de preço e ofertas cruzadas nos outros marketplaces, cupons verificados automaticamente (Playwright) com selo confirmado/não confirmado, e recebe alerta quando o preço cai (recheck a cada 6h)

---

## FASE 2 — RECEITA RÁPIDA

- [ ] **2.1** Assinatura de empresas locais $10–30/mês (free→premium) → _código pronto: [PR #68](https://github.com/contaecom23-ai/ClubeUSA/pull/68) (aguarda Fase 0)_
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

*Atualizado em: 2026-09-26*
