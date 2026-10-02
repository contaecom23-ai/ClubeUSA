# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir, ele registra aqui e segue para outra tarefa.

```
### [DATA] Título da decisão
**Contexto:** ...
**Pergunta:** ...
**Opções:**
- Opção A: prós / contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## Decisões Pendentes

---

### [2026-10-02] D-001: PARALISIA DE MERGE — 40+ PRs parados, projeto bloqueado há meses

**Contexto:**
O projeto tem 40+ pull requests abertos no GitHub cobrindo TODAS as fases 0.1 a 1.5 do roadmap, além de correções de segurança e documentação. Nenhum PR foi mergeado desde agosto de 2026. O main branch está desatualizado (última feature real: price tracker em junho). O Claude continua criando PRs novos a cada sessão, gerando duplicação e confusão crescente. O projeto está tecnicamente paralisado.

**O que existe no main hoje:**
- Auth via WhatsApp OTP (phone + OTP de 6 dígitos)
- Cadastro de membros (`/auth/register`)
- Deals curados pelo admin
- Referral básico (`?ref=code` — sem pretty URL)
- Billing Stripe (VIP $4,99/mês)
- Price tracker / alertas de preço (Fase 1.6 ✅)

**O que está em PRs NÃO mergeados:**
- Fase 0.1: email confirmation (PRs #46, #75, #106, #115, #123)
- Fase 0.2: URL de referral `/i/{code}` (PRs #3, #71, #102, #112, #117, #121)
- Fase 0.3: analytics/dashboard admin (PRs #4, #109, #119)
- Fase 0.4: anti-fraude (PRs #5, #104)
- Fase 1.1: promoções comunitárias (PRs #12, #113)
- Fase 1.2: busca por ZIP (PR #14)
- Fase 1.3: influenciadores (PRs #16, #116)
- Fase 1.4: empregos (PRs #19, #120)
- Fase 1.5: moradia (PR #20)
- Correções de segurança (PR #110)
- 10+ PRs de documentação

**Pergunta:**
Como desbloquear o projeto? Qual das 3 opções abaixo você quer seguir?

**Opções:**

**Opção A — Mergear os PRs mais recentes de cada fase (RECOMENDADO)**
Usar os PRs mais recentes (agosto–outubro) pois provavelmente corrigem problemas dos mais antigos.
Ordem recomendada de merge:
1. PR #123 — Fase 0.1 (email confirmation) — fechar #115, #106, #75, #46 depois
2. PR #117 — Fase 0.2 (referral URL) — avaliar conflito com #123, fechar duplicatas
3. PR #119 — Fase 0.3 (analytics)
4. PR #104 — Fase 0.4 (anti-fraude)
5. PR #113 — Fase 1.1 (promoções)
6. PR #14 — Fase 1.2 (ZIP search)
7. PR #116 — Fase 1.3 (influenciadores)
8. PR #120 — Fase 1.4 (empregos)
9. PR #20 — Fase 1.5 (moradia)
10. PR #110 — Correções de segurança (pode ir a qualquer hora, não tem dependência)

*Prós:* Aproveita trabalho feito, produto vai para o ar rapidamente.
*Contras:* PRs podem ter conflitos entre si; requer revisão de cada um.

**Opção B — Fechar todos os PRs e fazer um único branch consolidado**
O Claude faria um branch `main-consolidation` que integra todas as features de uma vez.
*Prós:* Código limpo, sem conflitos, versão definitiva.
*Contras:* Perda de histórico de revisões; Claude precisa de ~2 semanas de sessões para consolidar tudo; risco maior.

**Opção C — Continuar como está (NÃO recomendado)**
Continuar criando PRs sem mergear.
*Prós:* Nenhum.
*Contras:* Duplicação infinita, perda de valor, projeto nunca vai ao ar.

**Recomendação:**
Opção A. Comece pelo PR #123 (email confirmation) — é o mais recente e tem o título "Fase 0.1 completa". Leva 15 minutos para revisar e mergear. Com isso, a paralisia acaba e o Claude pode construir em cima do que foi mergeado.

**Se não quiser revisar código:** diga ao Claude para criar um branch consolidado (Opção B) e ele faz o trabalho pesado.

**Ação imediata mínima:** Abra https://github.com/contaecom23-ai/ClubeUSA/pull/123 e clique em Merge.

**Status:** PENDENTE

---

### [2026-10-02] D-002: Auth por WhatsApp OTP vs Email — qual manter?

**Contexto:**
O main branch usa WhatsApp OTP (Z-API) como único método de autenticação. Os PRs de Fase 0.1 adicionam email confirmation. Isso cria uma ambiguidade: qual é a estratégia de auth final?

**Opções:**

**Opção A — Manter WhatsApp OTP (status quo)**
- Simples, funciona hoje
- Elimina a necessidade de Z-API para auth (mas já está integrado para grupos)
- Problema: Z-API custa dinheiro, se a conta ficar inativa o OTP para de funcionar
- Para o público imigrante brasileiro, WhatsApp é onipresente — faz sentido

**Opção B — Migrar para Email + Senha**
- Independente de WhatsApp
- Custo zero de infraestrutura (SMTP via SendGrid/Resend gratuito)
- Mais familiar para empresas (Fase 2)
- Requer alterar o fluxo de auth no frontend

**Opção C — Suportar ambos (email + WhatsApp)**
- Máxima acessibilidade
- Complexidade técnica maior
- Pode confundir o usuário

**Recomendação:**
Opção A por agora (manter WhatsApp OTP), pois o público é 100% brasileiro e WhatsApp tem 95%+ de penetração. A Fase 0.1 de email confirmation pode ser implementada ADICIONALMENTE ao OTP (email como campo opcional para recuperação de conta), não como substituição. Isso é o que PR #123 provavelmente faz.

**Decisão necessária:** Confirme se quer manter WhatsApp OTP como auth principal OU substituir por email.

**Status:** PENDENTE

---

### [2026-10-02] D-003: Deploy — o app está rodando em produção?

**Contexto:**
Existe um `render.yaml` e um `DEPLOYMENT.md` no repositório, mas não está claro se o app está efetivamente deployado e acessível em clubeusa.com. Se não estiver deployado, os usuários não têm acesso à plataforma.

**Pergunta:**
O site clubeusa.com está funcionando? Existe um ambiente de produção ativo?

**Ação necessária:**
1. Confirme se o deploy no Render (ou onde for) está ativo
2. Informe ao Claude para que ele possa ajustar configurações conforme necessário
3. Se não estiver deployado, esta deve ser a PRIORIDADE #1 antes de qualquer nova feature

**Status:** PENDENTE

---

*Atualizado em: 2026-10-02*
