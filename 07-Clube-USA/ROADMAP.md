# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> **ESTADO REAL** — atualizado em 2026-09-19 pelo agente após auditoria do código em main.

---

## O que existe NO MAIN hoje (código funcionando)

- **Auth via WhatsApp OTP**: login por número de telefone com código 6 dígitos (otp_codes table + Z-API)
- **Sistema de membros**: cadastro, planos free/VIP, pontos, níveis (bronze/silver/gold/vip)
- **Deals/Promoções**: tabela deals com score, aprovação manual/auto, categorias
- **Referral schema**: referral_code único por membro, referred_by, tabela referrals — estrutura pronta, falta o endpoint de redirect `/i/{code}`
- **Forum e News**: routers em `api/routers/forum.py` e `api/routers/news.py`
- **Chat IA (assistant)**: router em `api/routers/assistant.py`
- **RLS no Supabase**: Row Level Security ativo nas tabelas principais
- **Audit logs**: tabela imutável para rastreamento de ações

## O que está em PRs (branches), NÃO merged ainda

⚠️ 29+ PRs abertos desde julho/2026. Nenhum merged. Ver DECISOES.md D-001.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [ ] **0.1** Cadastro + perfil mínimo + **email confirmado**
  - *Auth WhatsApp funciona. Email como campo: ver DECISOES.md D-002.*
  - *PRs existentes: #75, #84, #85, #87, #98 (escolher um)*
- [ ] **0.2** Sistema de REFERRAL rastreável — link `/i/{code}` + atribuição
  - *Schema pronto no main. Falta: endpoint redirect + captura no frontend.*
  - *PR mais limpo: #100 (não-draft, pronto para merge)*
- [ ] **0.3** Analytics básico
  - *PR #100 inclui analytics time-series básico*
- [ ] **0.4** "Cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
  - *Tabela deals existe. PR #97 adiciona expires_at + is_urgent + sort urgência*
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
  - *Branch: claude/fase-1.2-busca-zip — sem PR aberto visível*
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO
  - *Selos: Parceiro 50 / Embaixador 250 / Hall da Fama 1000*
  - *PR #96 — /member/influencer + /admin/influencers*
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
  - *PR #93 — tabela jobs + seed admin*
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)
  - *PR #94 — tabela housing + seed admin*
- [x] **1.6** Rastreador de preço de produto (Amazon/Walmart/BestBuy)
  - *Implementado em main: db/product_tracker_migration.sql + price_alerts*

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

*Atualizado em: 2026-09-19 — Auditoria do agente: código real em main catalogado*
