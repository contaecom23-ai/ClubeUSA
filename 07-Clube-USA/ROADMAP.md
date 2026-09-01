# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> **Última atualização:** 2026-09-01
> **Estado:** App não deployado. Main branch tem código funcional. Ver D-001 em DECISOES.md.

---

## Estado real do main (sem merge de nenhum PR)

O código abaixo **já existe** no branch `main` e funcionará assim que o app for deployado:

| Componente | Estado |
|---|---|
| Auth (cadastro + OTP WhatsApp + JWT) | ✅ Funcional |
| Perfil de membro | ✅ Funcional |
| Referral code (geração + contagem) | ✅ Funcional |
| Billing Stripe VIP | ✅ Funcional |
| Rastreador de preços Amazon (Fase 1.6) | ✅ Funcional |
| Forum + Notícias + Assistente IA | ✅ Funcional |
| Painel Admin | ✅ Funcional |
| Banco Supabase (21 tabelas) | ✅ Criado |
| Deploy no Render | ❌ Pendente (ver SETUP_PENDENTE.md) |

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [~] **0.1** Cadastro + perfil mínimo + email confirmado
  - ✅ Cadastro por telefone + OTP WhatsApp + JWT: **FEITO no main**
  - ❌ Email confirmado: pendente (D-003 — decisão: manter WhatsApp OTP ou adicionar email?)
- [~] **0.2** Sistema de REFERRAL rastreável (link único + atribuição)
  - ✅ `referral_code` gerado no cadastro, contagem de indicações: **FEITO no main**
  - ❌ Endpoint `/i/{code}` de redirect: pendente (PR #52 ou #71, aguardando merge)
  - ❌ Captura automática do `?ref=CODE` no frontend: pendente
- [ ] **0.3** Analytics básico (funil, crescimento diário, engajamento)
- [ ] **0.4** "Cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (PR #16 — aguardando merge após deploy)
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas) (PR #19 — aguardando merge após deploy)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP) (PR #20 — aguardando merge após deploy)
- [x] **1.6** Rastreador de preço de produto (Amazon/Walmart/BestBuy, histórico, cupons verificados, alertas)

---

## FASE 2 — RECEITA RÁPIDA

- [ ] **2.1** Assinatura de empresas locais $10–30/mês (PR #68 — aguardando merge após deploy)
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

## Próximo passo ÚNICO

**→ Deploy do main no Render** (ver `SETUP_PENDENTE.md`). Leva < 30 min. Desbloqueia tudo.

Depois do deploy: mergear PR #46, depois PR #62, depois decidir o que fazer com os outros 28 PRs.
