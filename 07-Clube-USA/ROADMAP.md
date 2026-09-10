# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.

> ⚠️ **ATENÇÃO (2026-09-10):** 88 PRs abertos, nenhum mergeado. O código abaixo reflete o estado do `main`.
> Todo o trabalho de feature está em branches. Ver **DECISOES.md → D-001** para o plano de desbloqueio.

---

## REGRAS DE SEGURANÇA (obrigatórias em todo código)

- Auth: TODA rota exige token válido; lista explícita e mínima de rotas públicas
- Multi-tenant: todo dado isolado por user_id; dono sempre do servidor (token), nunca do input
- Acesso a recurso de outro retorna 404 (não vazar existência)
- RLS (Row Level Security) no Supabase como endgame
- Segredos sempre via env var, nunca hardcoded
- Tokens JWT com TTL 7 dias + refresh
- Rate-limit em login e registro
- Proteção XSS, SQL injection (queries parametrizadas), IDOR
- CORS restrito; headers de segurança ativos
- Webhooks externos com verificação de assinatura HMAC + anti-replay

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [ ] **0.1** Cadastro + perfil mínimo + email confirmado
  - *PRs existentes (branches, não mergeados): #75, #84, #85, #87*
- [ ] **0.2** Sistema de REFERRAL rastreável (link único `/i/{code}` + atribuição)
  - *PRs existentes: #62, #71, #83*
- [ ] **0.3** Analytics básico
  - *PRs existentes: #62, #67, #70*
- [ ] **0.4** Definição de "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
  - *PRs existentes: #65*
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
- [x] **1.6** Rastreador de preço de produto — cola link (Amazon/Walmart/BestBuy), histórico de preço, cupons verificados automaticamente, alerta quando o preço cai

---

## FASE 2 — RECEITA RÁPIDA

- [ ] **2.1** Assinatura de empresas locais $10–30/mês (free→premium)
  - *PRs existentes: #68*
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

*Atualizado em: 2026-09-10 — Agente autônomo*
