# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> `🔄 PR #XX` = implementado em PR aberta, aguardando merge pelo dono.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- 🔄 **0.1** Cadastro + perfil mínimo + email confirmado *(PR #54 ou #46 — aguardando merge + chave de email)*
- 🔄 **0.2** Sistema de REFERRAL rastreável (link único por pessoa ex: clubeusa.com/i/joao + atribuição de qual cadastro veio de qual link) *(PR #62 ou #52)*
- 🔄 **0.3** Analytics básico *(PR #62 ou #55 ou #67)*
- 🔄 **0.4** Definição de "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude *(PR #58)*

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- 🔄 **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência) *(PR #12)*
- 🔄 **1.2** Busca por ZIP + raio 1–5 milhas *(PR #65 ou #14)*
- 🔄 **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido para todos, com teto de orçamento; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; opcional bônus mensal pro 1º lugar) *(PR #16)*
- 🔄 **1.4** Empregos (seed manual nas 1ªs semanas) *(PR #19)*
- 🔄 **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual) *(PR #20)*
- [x] **1.6** Rastreador de preço de produto — membro cola o link de um produto (Amazon/Walmart/BestBuy), vê o histórico de preço e ofertas cruzadas nos outros marketplaces, cupons verificados automaticamente (Playwright) com selo confirmado/não confirmado, e recebe alerta quando o preço cai (recheck a cada 6h)

---

## FASE 2 — RECEITA RÁPIDA

- 🔄 **2.1** Assinatura de empresas locais $10–30/mês (free→premium) *(PR #68)*
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

## PRs de Infraestrutura / Segurança (sem fase, mas necessárias)

- 🔄 CI: testes automáticos nos PRs *(PR #56)*
- 🔄 fix(security): headers HTTP + validações *(PR #9)*
- 🔄 fix(security): verificar token Z-API no webhook *(PR #61)*
- 🔄 fix(referral): captura de ?ref=CODE no frontend *(PR #57)*
- 🔄 test: cobertura de caminhos críticos *(PR #63)*

---

## Status Geral (2026-08-25)

| Fase | Itens | Código pronto | Em main |
|---|---|---|---|
| Fase 0 | 4 | 4 (PRs abertas) | 0 |
| Fase 1 | 6 | 5 (PRs abertas) + 1 (merged) | 1 |
| Fase 2 | 4 | 1 (PR aberta) | 0 |
| Fase 3-6 | 13 | 0 | 0 |

**Bloqueio principal:** Merge das PRs existentes (ver DECISOES.md).

---

*Atualizado em: 2026-08-25*
