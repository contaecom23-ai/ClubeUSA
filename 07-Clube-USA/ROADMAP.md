# ROADMAP — Clube USA

> Fonte da verdade do projeto. Atualizado em: 2026-08-17.

**Legenda:**
- `[x]` Concluído e mesclado em `main`
- `[~]` Parcialmente implementado em `main` OU em PR aberto aguardando merge
- `[ ]` Não iniciado

**Estado real em 2026-08-17:**
O branch `main` já contém uma base FastAPI substancial (`api/main.py` ~40KB): cadastro por OTP via WhatsApp, referral_code, deals, Stripe, admin, forum, news, rastreador de produtos, alertas de preço. Porém **12 PRs estão abertas e nenhuma foi mergeada**. As tarefas abaixo refletem o que *de fato* está em `main` vs. o que está em PR pendente. Ver `DECISOES.md` para ações necessárias do dono.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [~] **0.1** Cadastro + perfil mínimo + email confirmado
  - Em `main`: cadastro por telefone + OTP WhatsApp, email opcional (não confirmado), perfil básico OK
  - Melhoria em aberto: PR #46 (`feature/fase-0.1-cadastro-auth`) contra main
  - **Nota honesta:** o sistema usa WhatsApp OTP — "email confirmado" do roadmap original não se aplica. Ver DECISOES.md item D-001.

- [~] **0.2** REFERRAL rastreável (link único por pessoa + atribuição)
  - Em `main`: `referral_code` gerado no cadastro, endpoint `/member/referral`, link `?ref=CODE`
  - Faltando: redirect `/i/{code}` (URL bonita tipo `clubeusa.com/i/joao`) — PR #52 cobre isso
  - **Ação:** dono mergear PR #52

- [ ] **0.3** Analytics básico
  - PR #4 aberto (chain antiga — ver DECISOES.md item D-002)

- [ ] **0.4** "Cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude
  - PR #5 aberto na chain antiga

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [~] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
  - Em `main`: endpoint `/member/deals` existe com filtro por categoria, diferenciação VIP/free
  - Curadoria editorial, urgência, UI dedicada: PR #12 na chain antiga

- [~] **1.2** Busca por ZIP + raio 1–5 milhas
  - PR #14 na chain antiga (inclui geolocalização de deals)

- [~] **1.3** Programa de influenciadores PAGO POR RESULTADO
  - Em `main`: sistema de pontos e leaderboard existe; selos e pagamento por resultado: PR #16

- [ ] **1.4** Empregos (seed manual nas primeiras semanas)
  - PR #19 na chain antiga

- [ ] **1.5** Moradia (quartos/roommates/casas, filtro ZIP)
  - PR #20 na chain antiga

---

## FASE 2 — RECEITA RÁPIDA

- [ ] **2.1** Assinatura de empresas locais $10–30/mês (free→premium)
  - Em `main`: Stripe para VIP de membros; Stripe para empresas ainda não existe
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

## PRs abertas (resumo em 2026-08-17)

| PR | Branch | Base | O que faz |
|----|--------|------|-----------|
| #52 | `fase-0.2-referral-rastreavel` | main | Redirect `/i/{code}` + captura no frontend |
| #51 | `docs/decisoes-2026-08-14` | main | Corrige YAML workflow + DECISOES.md |
| #46 | `feature/fase-0.1-cadastro-auth` | main | Melhora fluxo 0.1 (título diz "MERGEAR ESTE") |
| #12–#20 | chain `claude/fase-*` | entre si | Fases 1.1–1.5 (stacked, não baseadas em main) |
| #3–#9 | chain `claude/fase-0.*` | entre si | Fases 0.2–0.4 (stacked) |

**Recomendação:** ver DECISOES.md item D-002 sobre o que fazer com a chain antiga.

*Atualizado em: 2026-08-17*
