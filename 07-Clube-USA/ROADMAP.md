# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluídas.
> **IMPORTANTE:** itens marcados `[~]` = código pronto em PR, aguardando merge + deploy.

---

## ESTADO ATUAL DOS PRs (2026-07-06)

A Fase 0 está **totalmente codificada** em uma cadeia de PRs. Nenhum foi merged ainda.
**Ordem obrigatória de merge (cada um depende do anterior):**

| PR | Branch | Conteúdo | Status |
|----|--------|----------|--------|
| **#2** | `claude/fase-0.1-cadastro-perfil-email` | Fase 0.1 — auth, perfil, email | Draft, aguardando review |
| **#3** | `claude/fase-0.2-referral` | Fase 0.2 — referral rastreável | Draft, base no PR#2 |
| **#4** | `claude/fase-0.3-analytics` | Fase 0.3 — analytics server-side | Draft, base no PR#3 |
| **#5** | `claude/fase-0.4-valid-registration` | Fase 0.4 — cadastro válido + anti-fraude | Draft, base no PR#4 |

**PRs redundantes (podem ser fechados):**
- PR #1 (`claude/fase-0-cadastro-email`): implementação mais antiga da 0.1, supersedida pelo #2
- PR #6 (`claude/fase-0.1-cadastro-email-confirmado`): outra implementação da 0.1, supersedida pelo #2
- PR #7 (`feat/fase-0.1-cadastro-perfil-email`): implementação mais recente da 0.1, isolada — a cadeia #2-5 cobre tudo

**Por que 3 PRs redundantes de 0.1?** Cada sessão autônoma lia o ROADMAP.md no main (que mostrava `[ ]`), concluía que 0.1 não estava feita, e re-implementava. Este arquivo corrige isso.

**Bloqueio real para avançar:** infraestrutura — Supabase, email, hosting, domínio.
Ver DECISOES.md para todas as decisões pendentes.

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [~] **0.1** Cadastro + perfil mínimo + email confirmado *(código pronto em PR #2; aguarda merge + Supabase setup)*
- [~] **0.2** Sistema de REFERRAL rastreável (link único `?ref=joao-x7k2` + atribuição) *(código pronto em PR #3; aguarda merge do #2)*
- [~] **0.3** Analytics básico (tracking server-side + painel admin) *(código pronto em PR #4; aguarda merge do #3)*
- [~] **0.4** Cadastro válido verificável (email confirmado + ≥1 ação real) + anti-fraude (bloqueio de emails descartáveis) *(código pronto em PR #5; aguarda merge do #4)*

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência)
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido para todos, com teto de orçamento; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; opcional bônus mensal pro 1º lugar)
- [ ] **1.4** Empregos (seed manual nas 1ªs semanas)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP — seed manual)

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

*Atualizado em: 2026-07-06 — Fase 0 toda codificada em PRs #2-5; aguardando review do dono e decisões de infra*
