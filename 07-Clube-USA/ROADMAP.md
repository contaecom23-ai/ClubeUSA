# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
>
> **Estado real em 2026-08-31:** 30+ PRs abertas, 0 merges. Itens abaixo refletem o que está no `main`, não o que existe em PRs pendentes.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [ ] **0.1** Cadastro + perfil mínimo + email confirmado
  - _PRs existentes:_ #46 (email auth), #54 (confirmação), #75 (confirmação v2) — aguardando merge
- [ ] **0.2** Sistema de REFERRAL rastreável (link único `/i/{code}` + atribuição de cadastro)
  - _PRs existentes:_ #52, #57, #70, #71 — aguardando merge
  - _Status no main:_ referral_code existe no schema e API, mas frontend não captura `?ref=`
- [ ] **0.3** Analytics básico
  - _PRs existentes:_ #55, #67 — aguardando merge
- [ ] **0.4** Definição de "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude
  - _PRs existentes:_ #58 — aguardando merge

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
  - _Status:_ deals existem no main via scraper, mas sem curadoria manual ou urgência
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
  - _PRs existentes:_ #14, #65 — aguardando merge
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido para todos, com teto de orçamento; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; opcional bônus mensal pro 1º lugar)
  - _PRs existentes:_ #16 — aguardando merge
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
  - _PRs existentes:_ #19 — aguardando merge
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
  - _PRs existentes:_ #20 — aguardando merge
- [x] **1.6** Rastreador de preço de produto (Amazon/Walmart/BestBuy, histórico, cupons verificados, alerta de queda)
  - _Status:_ implementado e no main

---

## FASE 2 — RECEITA RÁPIDA

- [ ] **2.1** Assinatura de empresas locais $10–30/mês (free→premium)
  - _PRs existentes:_ #68 — aguardando merge
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

*Atualizado em: 2026-08-31 — Claude (sessão automática)*
