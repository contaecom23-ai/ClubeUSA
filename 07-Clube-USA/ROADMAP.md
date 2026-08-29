# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> **Estado real em 2026-08-29** — leia DECISOES.md para ação imediata.

---

## LEGENDA
- `[x]` = Feito e no **main**
- `[~]` = Parcialmente feito no **main**
- `[ ]` = Não feito no main (pode existir em PR aberto aguardando merge)

---

## REGRAS DE SEGURANÇA (obrigatórias em toda feature)

- Auth global: TODA rota exige token; rotas públicas: `/`, `/health`, `/public/*`, `/auth/*` (com rate-limit), `/billing/webhook` (HMAC Stripe), `/i/{code}` (redirect)
- Multi-tenant: todo dado isolado por `user_id` do token (nunca do input cliente); recurso de outro → 404
- RLS no Supabase como endgame; até lá: acesso server-side com `service_role`; nunca expor `anon key` com dados sensíveis no client
- Segredos sempre via env var; nunca hardcoded
- Rate-limit em `/auth/*` (5 req/min por IP)
- Proteção XSS, SQL injection (queries parametrizadas), IDOR
- Webhooks externos com verificação HMAC + janela anti-replay

---

## FASE 0 — PRÉ-LANÇAMENTO

- `[~]` **0.1** Cadastro + perfil mínimo — auth via **WhatsApp OTP funciona** no main; email confirmado **não implementado** (ver D-001 em DECISOES.md — decisão de produto necessária)
- `[~]` **0.2** REFERRAL rastreável — código gerado automático, `?ref=CODE` capturado no cadastro, stats em `GET /member/referral`; **faltando:** endpoint `/i/{code}` de link curto — já implementado em PR #62, aguardando merge
- `[ ]` **0.3** Analytics básico — endpoint `GET /admin/analytics` implementado em PR #62, aguardando merge
- `[ ]` **0.4** Definição de "cadastro válido" + anti-fraude — PR #58 implementa, aguardando merge

---

## FASE 1 — TRAÇÃO

- `[~]` **1.1** PROMOÇÕES/ACHADOS — backend completo no main (`GET /member/deals`, admin scan/approve/reject/send via WhatsApp); falta: UI de curadoria e urgência no frontend
- `[ ]` **1.2** Busca por ZIP + raio 1–5 milhas — PR #65 (17 testes), aguardando merge
- `[ ]` **1.3** Influenciadores PAGO POR RESULTADO — PR #16, aguardando merge
- `[ ]` **1.4** Empregos (seed manual) — PR #19, aguardando merge
- `[ ]` **1.5** Moradia (quartos/roommates/casas, filtro ZIP) — PR #20, aguardando merge
- `[x]` **1.6** Rastreador de preço de produto — completo no main (Amazon/Walmart/BestBuy, Playwright, alertas, `POST /products/track`)

---

## FASE 2 — RECEITA RÁPIDA

- `[~]` **2.1** Assinatura de empresas $10–30/mês — Stripe VIP $4,99/mês **existe no main** (checkout, webhook, portal); assinatura de **empresas** $10–30/mês: PR #68, aguardando merge
- `[ ]` **2.2** Diretório de empresas
- `[ ]` **2.3** Publicidade local por região
- `[ ]` **2.4** Leilão de destaque por categoria/ZIP

---

## FASE 3 — CONFIANÇA E REDE

- `[ ]` **3.1** Reviews/reputação
- `[ ]` **3.2** Ranking comunitário
- `[~]` **3.3** Conteúdo da comunidade — Forum básico no main (`/forum/` router, Q&A)
- `[ ]` **3.4** Gamificação (selos, pontos)

---

## FASE 4 — INTELIGÊNCIA

- `[ ]` **4.1** IA CONCIERGE
- `[ ]` **4.2** Sistema de INTENÇÃO
- `[ ]` **4.3** Personalização não-sensível

---

## FASE 5 — MONETIZAÇÃO PESADA

- `[ ]` **5.1** LEADS
- `[ ]` **5.2** Serviços financeiros
- `[ ]` **5.3** Produtos próprios

---

## FASE 6 — B2B

- `[ ]` **6.1** Dados agregados
- `[ ]` **6.2** Painel de insights por ZIP
- `[ ]` **6.3** Clientes B2B

---

*Atualizado em: 2026-08-29 — próxima atualização após merges em DECISOES.md*
