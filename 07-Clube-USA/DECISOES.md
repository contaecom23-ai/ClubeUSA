# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## ⚠️ SITUAÇÃO CRÍTICA — LEIA PRIMEIRO (2026-10-28)

### Diagnóstico honesto do agente autônomo

O projeto está em paralisia de merge desde outubro/2026. Em resumo:

| Item | Estado |
|------|--------|
| PRs abertas | **35+**, nenhuma mergeada |
| Código pronto para Fase 0 | **SIM** — PR #125 implementa 0.1+0.2+0.3+0.4 completo |
| CI/GitHub Actions | **QUEBRADO** — YAML com indentação errada, fix em PR #145 |
| Próxima tarefa desbloqueada | **NENHUMA** — tudo aguarda merge do dono |

**O problema não é falta de código. É falta de merge.**

---

## Ação necessária — 2 PRs para mergear (em ordem)

### PASSO 1 — Merge PR #145 (CI fix + docs)
**Link:** https://github.com/contaecom23-ai/ClubeUSA/pull/145

O que faz:
- Corrige o YAML quebrado do GitHub Actions (o agente não roda via CI atualmente)
- Documenta a situação

Estado: `mergeable_state: clean` ✅

---

### PASSO 2 — Merge PR #125 (Fase 0 completa)
**Link:** https://github.com/contaecom23-ai/ClubeUSA/pull/125

O que faz:
- **Fase 0.1** — Confirmação de email (endpoint + serviço SMTP + migration)
- **Fase 0.2** — Rota `/i/{code}` para link de referral amigável
- **Fase 0.3** — Analytics de funil e crescimento diário (`/admin/analytics/`)
- **Fase 0.4** — Anti-fraude por IP (max 3 cadastros/IP por 24h via audit_logs)
- Marca Fase 0.1–0.4 como `[x]` no ROADMAP.md

Estado: `mergeable_state: clean` ✅  
Migrações SQL a aplicar após merge: ver PR #125 (2 arquivos, ambos idempotentes)

---

### PASSO 3 — Fechar os 33 PRs obsoletos

Após mergear #145 e #125, os demais ~33 PRs são duplicatas e podem ser fechados.
**Claude pode fechar automaticamente se o dono confirmar neste PR.**

---

## Decisões de produto pendentes

### D-001 — Autenticação: email OU WhatsApp/OTP?

**Data:** 2026-10-28  
**Contexto:** O app em `main` usa OTP via WhatsApp como método primário. O PR #125 adiciona confirmação de email em cima disso. Para a maioria dos imigrantes brasileiros, WhatsApp é mais acessível que email. Mas email é necessário para password reset, notificações de deals, etc.

**Pergunta:** O cadastro deve:
- (A) Exigir ambos (telefone + email confirmado) — mais seguro, mais atrito
- (B) Aceitar apenas telefone, email opcional confirmável — menor atrito, fluxo atual do PR #125
- (C) Migrar para email como primário, telefone opcional — padrão da maioria dos SaaS

**Recomendação:** Opção B (PR #125 já implementa). O WhatsApp é o canal principal da comunidade brasileira. Email como campo verificável mas não obrigatório para o cadastro inicial dá a melhor taxa de conversão agora.

**Status:** PENDENTE — aguarda confirmação do dono para liberar merge do PR #125.

---

### D-002 — Frequência do agente autônomo

**Data:** 2026-10-28  
**Contexto:** O agente roda 3x/dia via GitHub Actions (quando o YAML estiver correto) + via claude.ai agendado. Cada run cria 1 PR novo quando há trabalho a fazer. Com 35+ PRs abertos sem merge, novas runs não têm tarefa desbloqueada e apenas criam mais ruído de docs.

**Pergunta:** O que fazer com o agente enquanto os PRs não são mergeados?

**Opções:**
- (A) Pausar o agente até o dono mergear os PRs pendentes
- (B) Continuar 3x/dia mas o agente só envia notificação, sem criar novos PRs
- (C) Continuar como está (gera ruído, mas mantém o dono informado)

**Recomendação:** Opção B. O agente deve checar o estado e notificar, mas não criar PRs duplicados.

**Status:** PENDENTE

---

### D-003 — Infraestrutura de email (SMTP) para confirmação de email

**Data:** 2026-10-28  
**Contexto:** O PR #125 implementa o fluxo de confirmação de email. Para funcionar em produção, precisa de:
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` configurados no Render (ou outro provider)

**Pergunta:** Qual provedor de email usar?
- (A) SendGrid (free até 100 emails/dia, depois ~$20/mês)
- (B) Mailgun (free até 1000 emails/mês, depois ~$15/mês)
- (C) Amazon SES (~$0.10 por 1000 emails — mais barato para escala)
- (D) Gmail SMTP (gratuito até 500/dia — bom para fase inicial, não para produção)

**Recomendação:** Opção D para os primeiros 1.000 usuários (grátis, fácil setup). Migrar para SendGrid ou SES ao atingir 500 emails/dia.

**Status:** PENDENTE — aguarda o dono configurar as env vars no Render após merge do PR #125.

---

## Estado real do ROADMAP (2026-10-28)

O que já funciona em `main` (independente dos PRs):

| Item Roadmap | Estado real | Observação |
|-------------|-------------|-----------|
| 0.1 Cadastro + email confirmado | ⚠️ Parcial | Cadastro funciona (OTP), email não é confirmado. PR #125 completa. |
| 0.2 Referral rastreável | ⚠️ Parcial | `?ref=CODE` funciona, falta `/i/{code}` (pretty URL). PR #125 completa. |
| 0.3 Analytics básico | ⚠️ Parcial | `/admin/metrics` existe, falta funil/crescimento. PR #125 completa. |
| 0.4 Cadastro válido + anti-fraude | ⚠️ Parcial | Sem anti-fraude por IP. PR #125 completa. |
| 1.1 Promoções/Achados | ✅ Parcial em main | Sistema de deals funciona, admin aprova/rejeita |
| 1.6 Rastreador de preço | ✅ Implementado | Completo em main |

---

*Atualizado em: 2026-10-28 pelo agente autônomo*
