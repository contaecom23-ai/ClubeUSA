# ROADMAP — Clube USA

> Fonte da verdade do produto. Marque `[x]` nas tarefas concluídas.
> **Atualizado em: 2026-08-26** — reflete o que está no branch main.

---

## LEGENDA
- `[x]` = implementado e no main
- `[~]` = implementado parcialmente (ver nota)
- `[ ]` = não implementado no main (pode haver PR aberta aguardando merge)

---

## FASE 0 — PRÉ-LANÇAMENTO

- `[~]` **0.1** Cadastro + perfil mínimo + \"email confirmado\"
  - ✅ Cadastro via OTP WhatsApp (`POST /auth/register`, `/auth/otp/request`, `/auth/otp/verify`)
  - ✅ Perfil completo (`GET /member/profile`, `PATCH /member/profile`)
  - ⚠️ Auth é 100% WhatsApp OTP, sem email. Decisão pendente: manter assim ou adicionar email? Ver DECISOES.md #001
  - PR #54 (email confirmation) aberta, não mergeada

- `[~]` **0.2** REFERRAL rastreável (link `/i/CODE` + atribuição)
  - ✅ Tabela `referrals`, campo `referral_code`, `referred_by` em `members`
  - ✅ `GET /member/referral` (link + stats + histórico)
  - ✅ Atribuição no cadastro via `referral_code` no body
  - ❌ Endpoint `GET /i/{code}` redirect NÃO está no main (está em PR #70)
  - ❌ Captura `?ref=CODE` no frontend depende do JS em platform.html

- `[ ]` **0.3** Analytics básico
  - PRs #55 e #67 têm implementação, não mergeadas

- `[ ]` **0.4** \"Cadastro válido\" verificável (email confirmado + ≥1 ação real) + anti-fraude
  - PR #58 tem implementação, não mergeada

---

## FASE 1 — TRAÇÃO

- `[~]` **1.1** PROMOÇÕES/ACHADOS = carro-chefe
  - ✅ Deal scanner (dealscanner2), aprovação admin, envio via WhatsApp/Telegram
  - ✅ `GET /member/deals` com filtro por categoria e plano
  - ⚠️ É admin-driven (scanner + aprovação manual). Não há submissão por usuários ainda.
  - PR #12 (antigo) aberta, não mergeada

- `[ ]` **1.2** Busca por ZIP + raio 1-5 milhas
  - PR #65 tem implementação, não mergeada

- `[ ]` **1.3** Influenciadores PAGO POR RESULTADO
  - PR #16 tem implementação, não mergeada

- `[ ]` **1.4** Empregos (seed manual)
  - PR #19 tem implementação, não mergeada

- `[ ]` **1.5** Moradia (quartos/roommates/casas, filtro ZIP)
  - PR #20 tem implementação, não mergeada

- `[x]` **1.6** Rastreador de preço de produto
  - ✅ `POST /products/track`, `GET /products/track`, `DELETE /products/track/{id}`
  - ✅ Multi-marketplace (Amazon/Walmart/BestBuy), cupons via Playwright, alerta de queda

---

## FASE 2 — RECEITA RÁPIDA

- `[ ]` **2.1** Assinatura de empresas locais $10-30/mês (free→premium)
  - ⚠️ Existe Stripe para plano VIP de membros, mas NÃO para empresas
  - PR #68 tem implementação para empresas, não mergeada

- `[ ]` **2.2** Diretório de empresas
- `[ ]` **2.3** Publicidade local por região
- `[ ]` **2.4** Leilão de destaque por categoria/ZIP

---

## FASE 3 — CONFIANÇA E REDE

- `[ ]` **3.1** Reviews/reputação
- `[ ]` **3.2** Ranking comunitário
- `[ ]` **3.3** Conteúdo da comunidade (Q&A)
- `[ ]` **3.4** Gamificação (Contributor, Trusted Member, Community Guide, Verified Helper)

---

## FASE 4 — INTELIGÊNCIA

- `[ ]` **4.1** IA CONCIERGE
- `[ ]` **4.2** Sistema de INTENÇÃO (mudança de cidade, seguro, emprego, moradia)
- `[ ]` **4.3** Personalização não-sensível

---

## FASE 5 — MONETIZAÇÃO PESADA

- `[ ]` **5.1** LEADS (seguros, advogados, dentistas, contractors)
- `[ ]` **5.2** Serviços financeiros (corretagem de seguros, remessas)
- `[ ]` **5.3** Produtos próprios

---

## FASE 6 — B2B

- `[ ]` **6.1** Dados agregados
- `[ ]` **6.2** Painel de insights por ZIP
- `[ ]` **6.3** Clientes B2B (seguradoras, bancos, remessas, imobiliárias)

---

## INFRA JÁ NO MAIN (não mapeada acima)

- ✅ Auth JWT com TTL 7 dias, rate-limit por IP, security headers HTTP
- ✅ Supabase com RLS habilitado, service_role no server, PII criptografado
- ✅ Stripe VIP ($4.99/mês, trial 30 dias, webhook HMAC verificado)
- ✅ Forum, Notícias, Assistente IA (routers separados)
- ✅ Admin panel (métricas, membros, deals, alertas)
- ✅ Alertas de preço por ASIN
- ✅ Leaderboard de pontos + gamificação (bronze/silver/gold/vip)
- ✅ WhatsApp groups tracking via Z-API webhook
- ⚠️ Webhook `/webhook/group` SEM verificação de client-token Z-API (segurança) — PR #61 corrige

---

*Atualizado em: 2026-08-26 pelo agente autônomo*
