# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> Atualizado em: **2026-09-14** — reflete o estado REAL do código na branch `main`.

---

## REGRAS DE SEGURANÇA (obrigatórias em toda feature)

- Auth global: TODA rota exige token válido; lista explícita e mínima de rotas públicas.
- Multi-tenant: todo dado isolado por `user_id`; dono vem sempre do servidor (token), nunca do input.
- RLS no Supabase como endgame; até lá, acesso só server-side com `service_role`.
- Segredos via env var, nunca hardcoded.
- Rate-limit em login e registro.
- XSS, SQLi, path traversal, IDOR prevenidos.
- Webhooks com verificação de assinatura + anti-replay.

---

## ESTADO REAL EM MAIN (2026-09-14)

A API em `07-Clube-USA/clubeusa/api/main.py` já tem na branch `main`:

| Feature | Status em main |
|---|---|
| Cadastro de membro (`/auth/register`) | ✅ Implementado |
| Auth via WhatsApp OTP (`/auth/otp/*`) | ✅ Implementado |
| Perfil do membro (`/member/profile`) | ✅ Implementado |
| Referral code por membro (gerado no cadastro) | ✅ Implementado |
| Link de indicação `?ref=CODE` (captura no cadastro) | ✅ Implementado |
| Endpoint `/member/referral` (link + histórico) | ✅ Implementado |
| Métricas admin snapshot (`/admin/metrics`) | ✅ Implementado |
| Rate-limit por IP (5/min auth, 60/min geral) | ✅ Implementado |
| OTP com TTL e limite de tentativas | ✅ Implementado |
| Deals (`/member/deals`) | ✅ Implementado |
| Leaderboard de pontos | ✅ Implementado |
| Stripe VIP subscription | ✅ Implementado |
| Admin panel completo | ✅ Implementado |
| Rastreador de preço (Fase 1.6) | ✅ Implementado |
| Redirect `/i/{code}` para referral | ⚠️ PR #83/#92 pendentes, não em main |
| Analytics time-series (`/admin/analytics`) | ❌ Não em main (PRs #67 #70 #90 #92) |
| "Cadastro válido" verificável (≥1 ação real) | ❌ Não implementado |
| Influenciadores pago por resultado (Fase 1.3) | ❌ Não implementado |
| Empregos (Fase 1.4) | ❌ PR #93 pendente, não em main |
| Moradia (Fase 1.5) | ❌ PR #94 pendente, não em main |

**⚠️ SITUAÇÃO OPERACIONAL (2026-09-14):** 94+ PRs abertas sem merge. O agente autônomo
cria código e PRs mas o dono nunca faz merge. Ver D-004 em DECISOES.md.

---

## FASE 0 — PRÉ-LANÇAMENTO

- [x] **0.1** Cadastro + perfil mínimo *(auth WhatsApp OTP + perfil em main)*
- [x] **0.2** REFERRAL rastreável *(`referral_code` + `?ref=CODE` em main; redirect `/i/{code}` em PR pendente)*
- [ ] **0.3** Analytics básico time-series *(snapshot existe; time-series não — PRs #67 #70 #90 #92)*
- [ ] **0.4** "Cadastro válido" verificável + anti-fraude avançado *(depende de D-001)*

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe *(deals básico em main; curadoria/urgência não)*
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas *(PR #65 pendente)*
- [ ] **1.3** Influenciadores PAGO POR RESULTADO
- [ ] **1.4** Empregos (seed manual) *(PR #93 pendente)*
- [ ] **1.5** Moradia (quartos/roommates/casas) *(PR #94 pendente)*
- [x] **1.6** Rastreador de preço de produto

---

## FASE 2 — RECEITA RÁPIDA

- [ ] **2.1** Assinatura de empresas locais $10–30/mês *(PR #68 pendente)*
- [ ] **2.2** Diretório de empresas
- [ ] **2.3** Publicidade local por região
- [ ] **2.4** Leilão de destaque por categoria/ZIP

---

## FASE 3 — CONFIANÇA E REDE

- [ ] **3.1** Reviews/reputação
- [ ] **3.2** Ranking comunitário
- [ ] **3.3** Conteúdo da comunidade (Q&A)
- [ ] **3.4** Gamificação (Contributor, Trusted Member, Community Guide, Verified Helper)

---

## FASE 4 — INTELIGÊNCIA

- [ ] **4.1** IA CONCIERGE
- [ ] **4.2** Sistema de INTENÇÃO = motor de lucro
- [ ] **4.3** Personalização não-sensível

---

## FASE 5 — MONETIZAÇÃO PESADA

- [ ] **5.1** LEADS premium verificados
- [ ] **5.2** Serviços financeiros (seguros, remessas — comissão)
- [ ] **5.3** Produtos próprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B

---

*Atualizado em: 2026-09-14. Próxima tarefa desbloqueada: ver DECISOES.md D-004.*
