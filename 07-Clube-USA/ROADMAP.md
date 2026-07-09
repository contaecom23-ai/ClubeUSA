# ROADMAP — Clube USA

> Fonte da verdade do projeto. `[x]` = concluído e merged. `[~]` = código pronto, aguardando merge/deploy. `[ ]` = pendente.

---

## ⚡ ESTADO ATUAL DOS PRs (atualizado 2026-07-09)

**16 PRs abertos, nenhum merged.** A causa raiz: este PR (#10) ainda não foi merged, então o ROADMAP no main continua mostrando `[ ]` e o builder continua criando duplicatas. **Mergear este PR é a ação mais urgente.**

**PRs para MERGEAR (na ordem):**
| PR | Branch | Conteúdo | Depende de | Ordem |
|----|--------|----------|------------|-------|
| **#10** | `claude/fix-workflow-yaml-e-docs-main` | **Este PR** — workflow fix + ROADMAP atualizado | — | **1º — URGENTE** |
| **#2** | `claude/fase-0.1-cadastro-perfil-email` | Fase 0.1 — auth completo | — | 2º |
| **#3** | `claude/fase-0.2-referral` | Fase 0.2 — referral rastreável | PR #2 | 3º |
| **#4** | `claude/fase-0.3-analytics` | Fase 0.3 — analytics + painel admin | PRs #2, #3 | 4º |
| **#5** | `claude/fase-0.4-valid-registration` | Fase 0.4 — cadastro válido + anti-fraude | PRs #2–#4 | 5º |
| **#9** | `claude/fase-0-security-polish` | Security polish — senha forte + headers | PR #5 | 6º |

**PRs para FECHAR (duplicatas — 7 ao total):**
| PR | Branch | Motivo |
|----|--------|--------|
| #1 | `claude/fase-0-cadastro-email` | Duplicata de #2 |
| #6 | `claude/fase-0.1-cadastro-email-confirmado` | Duplicata de #2 |
| #7 | `feat/fase-0.1-cadastro-perfil-email` | Duplicata de #2 |
| #8 | `claude/sync-main-docs-estado-atual` | Supersedido por #10 |
| #11 | `feat/fase-0.1-cadastro-perfil` | Duplicata de #2 (criada 2026-07-08) |
| #13 | `claude/fase-0-cadastro-perfil` | Duplicata de #2 (criada 2026-07-09) |
| #15 | `claude/fase-0-cadastro` | Duplicata de #2 (criada 2026-07-09) |

**PRs de Fase 1 — AVALIAR antes de mergear (ver D-010 em DECISOES.md):**
| PR | Branch | Conteúdo | Status |
|----|--------|----------|--------|
| #12 | `claude/fase-1.1-promocoes` | Fase 1.1 — Promoções/Achados | Aguarda D-008 respondido + Fase 0 deployed |
| #14 | `claude/fase-1.2-busca-zip` | Fase 1.2 — Busca por ZIP | Aguarda Fase 1.1 deployed |
| #16 | `claude/fase-1.3-influenciadores` | Fase 1.3 — Influenciadores pago por resultado | Aguarda D-007 + D-006 respondidos |

**Próxima ação do dono (60 minutos):**
1. Fechar os 7 PRs duplicados listados acima
2. Mergear este PR #10
3. Configurar Supabase (ver D-002 em DECISOES.md — grátis, ~10 min)
4. Mergear em ordem: #2 → #3 → #4 → #5 → #9
5. Responder D-008 (5 perguntas de produto para Fase 1.1) — desbloqueia o builder

---

## FASE 0 — PRÉ-LANÇAMENTO (base invisível)

- [~] **0.1** Cadastro + perfil mínimo + email confirmado *(código pronto — PR #2)*
- [~] **0.2** Sistema de REFERRAL rastreável (link único por pessoa ex: clubeusa.com/i/joao + atribuição de qual cadastro veio de qual link) *(código pronto — PR #3)*
- [~] **0.3** Analytics básico *(código pronto — PR #4)*
- [~] **0.4** Definição de "cadastro válido" verificável (email confirmado + ≥1 ação real) + anti-fraude *(código pronto — PR #5 + #9)*

---

## FASE 1 — TRAÇÃO (foco em UM produto)

- [~] **1.1** PROMOÇÕES/ACHADOS = carro-chefe (curadoria, urgência) *(código em PR #12 — aguarda D-008 respondido + Fase 0 deployed)*
- [~] **1.2** Busca por ZIP + raio 1–5 milhas *(código em PR #14 — aguarda Fase 1.1 deployed)*
- [~] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro válido para todos, com teto de orçamento; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; opcional bônus mensal pro 1º lugar) *(código em PR #16 — aguarda D-006, D-007 respondidos)*
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

*Atualizado em: 2026-07-09*
