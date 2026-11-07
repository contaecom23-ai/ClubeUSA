# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> `[~]` = feito em branch/PR, **pendente merge na main**.

---

## Status atual (2026-11-07)

**⚠️ ATENÇÃO:** A branch `main` está congelada desde junho 2026. Há 161 PRs abertos não mergeados. Os itens marcados `[~]` têm código completo em branches mas **não estão em produção**. Ver DECISOES.md D-001 para o plano de desbloqueio.

---

## REGRAS DE SEGURANÇA (mandatórias em toda feature)

- Auth global: TODA rota exige token válido; lista explícita e mínima de rotas públicas (home, status, login, registro com rate-limit, webhook Stripe com verificação HMAC)
- Multi-tenant/isolamento: todo dado isolado por user_id; o dono vem SEMPRE do servidor (do token), nunca do input do cliente; acesso a recurso de outro retorna 404
- RLS (Row Level Security) no Supabase como endgame; até lá acesso só server-side com service_role; nunca expor anon key com dados sensíveis no client
- Segredos via env var, nunca hardcoded, sem default forjável
- Tokens com TTL curto (7 dias) + refresh; não 30+ dias
- Rate-limit em login e registro
- Proteção contra XSS, SQL injection, path traversal, IDOR
- CORS restrito; headers de segurança ativos; limite de tamanho em upload
- Webhooks externos com verificação de assinatura + janela anti-replay
- Nunca expor segredos ou PII em logs

## PADRÃO DE CONSTRUÇÃO (mandatório)

- Schema do banco é a FONTE DE VERDADE
- Toda feature nova entra com testes; isolamento multi-tenant testado (cross-tenant → 404)
- Antes de declarar pronto: leia o código alterado ponta a ponta; confira imports/deps; percorra o fluxo completo
- ESCALAR em DECISOES.md: migração destrutiva no banco; envio de dado real pra fora; push/merge na main ou deploy

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [~] **0.1** Cadastro + perfil mínimo + email confirmado
  → PR #161 `feat/fase-0-1-email-confirmation` (pronto, pendente merge)
- [~] **0.2** Sistema de REFERRAL rastreável (link `/i/{code}` + atribuição)
  → PR #157 `feat/fase-0.2-referral-redirect` (pronto, pendente merge)
- [~] **0.3** Analytics básico (série temporal de crescimento)
  → PR #109 `claude/fase-0.3-analytics-growth` (pronto, pendente merge)
- [~] **0.4** Definição de "cadastro válido" + anti-fraude por IP
  → PR #104 `feat/fase-0.4-valid-cadastro` (pronto, pendente merge)

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [~] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
  → PR #113 `feat/fase-1.1-promocoes-comunidade` (pendente merge)
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [~] **1.3** Programa de influenciadores PAGO POR RESULTADO (selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000)
  → PR #116 `feat/fase-1.3-influencer-tiers` (pendente merge)
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
- [x] **1.6** Rastreador de preço de produto — membro cola link (Amazon/Walmart/BestBuy), vê histórico, cupons verificados via Playwright, alerta quando preço cai (recheck 6h)

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

*Atualizado em: 2026-11-07*
