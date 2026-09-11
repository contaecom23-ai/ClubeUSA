# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> Atualizado em: 2026-09-11 | Ref: análise do código real na branch main

---

## NOTAS DE DESIGN (reconciliação com o código real)

- **Auth**: o app usa autenticação por **telefone + OTP via WhatsApp** (não email). A frase "email confirmado" no roadmap original era uma premissa inicial substituída pela decisão de produto de usar WhatsApp/Z-API. Ver DECISOES.md D-002.
- **Link de referral**: o código atual gera `{APP_URL}?ref={code}` (query param). O roadmap original previa `/i/{code}`. Ver DECISOES.md D-004.
- **VIP/Plano pago**: o Stripe está integrado ($4.99/mês com 30 dias de trial). Auth para features pagas via `require_paid_plan`.

---

## FASE 0 — PRÉ-LANÇAMENTO

- [x] **0.1** Cadastro + perfil mínimo + autenticação confirmada
  - `POST /auth/register` (phone, name, email opcional, language, state, categories, referral_code)
  - `POST /auth/otp/request` + `POST /auth/otp/verify` — OTP 6 dígitos via WhatsApp (Z-API), TTL 10min, max 3 tentativas
  - JWT com TTL 7 dias
- [x] **0.2** Sistema de REFERRAL rastreável
  - `referral_code` único por membro (gerado no cadastro)
  - Tabela `referrals` com status pending/confirmed/rejected e pontos
  - `referred_by` FK na tabela `members`
  - Register endpoint aceita `referral_code` e atribui automaticamente
  - Link: `{APP_URL}?ref={code}` — ver D-004 sobre formato /i/
- [ ] **0.3** Analytics básico — série temporal de crescimento
  - `GET /admin/analytics?days=N` — cadastros + referrals por dia (implementado neste PR)
- [ ] **0.4** "Cadastro válido" verificável (OTP concluído + ≥1 ação real) + anti-fraude básico

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência, listagem pública com conversão)
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (por cadastro válido, com teto; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; bônus mensal 1º lugar opcional)
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
- [x] **1.6** Rastreador de preço de produto
  - `POST /products/track` — cola URL (Amazon/Walmart/BestBuy), busca ofertas cruzadas
  - Cupons verificados via Playwright com selo confirmado/não confirmado
  - Recheck a cada 6h; alertas via WhatsApp quando preço cai
  - Exclusivo para plano pago (`require_paid_plan`)

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

*Atualizado em: 2026-09-11*
