# ROADMAP — Clube USA

> Fonte da verdade do projeto. `[x]` = concluído e merged. `[~]` = código pronto, aguardando merge/deploy. `[ ]` = pendente.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [x] **0.1** Cadastro + perfil mínimo + email confirmado *(código completo — deploy aguarda Supabase setup, ver DECISOES.md)*
- [x] **0.2** Sistema de REFERRAL rastreável (link único por pessoa ex: clubeusa.com/register.html?ref=joao-x7k2 + atribuição de qual cadastro veio de qual link) *(código completo — deploy aguarda infra do 0.1)*
- [x] **0.3** Analytics básico *(código completo — tracking de eventos server-side + painel admin)*
- [x] **0.4** Definição de "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude *(código completo — bloqueio de emails descartáveis + endpoint /users/me/validation-status)*

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [~] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência) *(código pronto — branch claude/fase-1.1-promocoes; aguarda merge da cadeia Fase 0 + migration 004)*
- [~] **1.2** Busca por ZIP + raio 1–5 milhas *(código pronto — branch claude/fase-1.2-busca-zip; aguarda merge de 1.1 + migration 005 + seed zip_codes)*
- [~] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido para todos, com teto de orçamento; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; opcional bônus mensal pro 1º lugar) *(código pronto — branch claude/fase-1.3-influenciadores; créditos display only, saques requerem Fase 5)*
- [~] **1.4** Empregos (seed manual nas 1ªs semanas) *(código pronto — branch claude/fase-1.4-empregos; migration 006_jobs.sql + 14 vagas no seed; endpoints GET /jobs, POST /admin/jobs, DELETE /admin/jobs/{id} + filtro ZIP/raio)*
- [~] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual) *(código pronto — branch claude/fase-1.5-moradia; migration 007_housing.sql + 15 anúncios seed cobrindo FL/MA/NJ/NY/CA/TX/IL/GA; endpoints GET /housing, GET /housing/search, GET /housing/{id}, POST /admin/housing, DELETE /admin/housing/{id}; 38 testes)*

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

*Atualizado em: 2026-07-12 (Fase 1.5 código pronto — branch claude/fase-1.5-moradia; próxima: Fase 2.1 Assinatura de empresas)*
