# ROADMAP — Clube USA

> Fonte da verdade do projeto. `[x]` = concluído e merged. `[~]` = código pronto, aguardando merge/deploy. `[ ]` = pendente.

---

## ⚡ ESTADO ATUAL DOS PRs (atualizado 2026-07-07)

**A Fase 0 está CODIFICADA E TESTADA (66 testes passando).** Nenhum PR foi merged ainda por falta de decisões de infraestrutura.

| PR | Branch | Conteúdo | Depende de | Status |
|----|--------|----------|------------|--------|
| **#2** | `claude/fase-0.1-cadastro-perfil-email` | Fase 0.1 — auth completo | — | ✅ Revisar e mergear 1º |
| **#3** | `claude/fase-0.2-referral` | Fase 0.2 — referral rastreável | PR #2 | ✅ Revisar e mergear 2º |
| **#4** | `claude/fase-0.3-analytics` | Fase 0.3 — analytics + painel admin | PRs #2, #3 | ✅ Revisar e mergear 3º |
| **#5** | `claude/fase-0.4-valid-registration` | Fase 0.4 — cadastro válido + anti-fraude | PRs #2, #3, #4 | ✅ Revisar e mergear 4º |
| **#9** | `claude/fase-0-security-polish` | Security polish — senha forte + headers | PR #5 | ✅ Revisar e mergear 5º |
| #1 | `claude/fase-0-cadastro-email` | Fase 0.1 redundante | — | ❌ Fechar |
| #6 | `claude/fase-0.1-cadastro-email-confirmado` | Fase 0.1 redundante | — | ❌ Fechar |
| #7 | `feat/fase-0.1-cadastro-perfil-email` | Fase 0.1 redundante | — | ❌ Fechar |
| **#8** | `claude/sync-main-docs-estado-atual` | Docs sync (supersedido por este PR) | — | ❌ Fechar |

**Por que existem 3 PRs redundantes de Fase 0.1?** O ROADMAP.md no main mostrava todos os itens como `[ ]`, levando cada sessão autônoma a concluir que precisava re-implementar o que já estava feito. Este PR corrige isso.

**Próxima ação do dono:**
1. Configurar Supabase, email e hosting (ver DECISOES.md)
2. Fechar PRs redundantes: #1, #6, #7, #8
3. Fazer review e merge na ordem: **#2 → #3 → #4 → #5 → #9**
4. Builder retoma em Fase 1.1 (PROMOÇÕES/ACHADOS) após deploy

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [~] **0.1** Cadastro + perfil mínimo + email confirmado *(código pronto — PR #2)*
- [~] **0.2** Sistema de REFERRAL rastreável (link único por pessoa ex: clubeusa.com/i/joao + atribuição de qual cadastro veio de qual link) *(código pronto — PR #3)*
- [~] **0.3** Analytics básico *(código pronto — PR #4)*
- [~] **0.4** Definição de "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude *(código pronto — PR #5 + #9)*

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [ ] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência) — *bloqueado por decisões em DECISOES.md (D-008)*
- [ ] **1.2** Busca por ZIP + raio 1–5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido para todos, com teto de orçamento; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; opcional bônus mensal pro 1º lugar) — *bloqueado por D-006 e D-007*
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

*Atualizado em: 2026-07-07*
