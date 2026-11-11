# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## 🚨 BLOQUEIO CRÍTICO — LEIA ISTO PRIMEIRO

**Data:** 2026-11-11  
**Situação:** 170 PRs abertos, **zero merges** desde 18/ago/2026 (quase 3 meses).  
O agente está em loop: cada rodada lê o mesmo main (ago/2026), não enxerga os PRs pendentes, e cria código duplicado.

**Para desbloquear o projeto você precisa de ~15 minutos:**

---

### AÇÃO 1 — Merge obrigatório (email verification, Fase 0.1)

**Escolha UM destes PRs para mergear — são todos implementações de email verification:**

| PR | Branch | Título | Recomendação |
|----|--------|--------|--------------|
| **#153** | feat/fase-0.1-email-confirmado | Fase 0.1 completa | ✅ Mergear este — mais antigo, mais revisado |
| #160 | feat/0.1-email-verification | verificação de email | Alternativa se #153 tiver conflito |
| #165 | feat/fase-0.1-email-verify | verificação token 24h | Alternativa |
| #166 | feat/fase-0.1-email-confirmation | confirmação multi-provider | Alternativa |
| #167 | feat/fase-0.1-email-verificacao | verificação — tokens seguros | Mais recente |
| #152, #148, #150, #161 | (duplicatas) | (email confirm) | Fechar após mergear um |

**Recomendação:** Mergear o PR #153. Depois feche os outros como duplicatas.

---

### AÇÃO 2 — Merge (Referral rastreável, Fase 0.2)

| PR | Branch | Título |
|----|--------|--------|
| **#157** | feat/fase-0.2-referral-redirect | referral redirect rastreável com atribuição completa |
| #117 | feat/fase-0.2-referral-link-rastreavel | link /i/{code} com analytics |

**Recomendação:** Após #153 ser mergeado, mergear #157.

---

### AÇÃO 3 — Merge (Security fixes)

| PR | Branch | Título |
|----|--------|--------|
| **#158** | fix/security-audit-2026-11-05 | 3 correções: PII em logs, OTP timing, CSP |

**Recomendação:** Mergear junto com ou logo após #157.

---

### Depois dos 3 merges acima

O agente poderá ver o estado real do main e avançar sem duplicar trabalho.

**PRs de documentação do loop (#151, #154, #155, #156, #159, #162, #163, #164, #168, #169, #170) podem ser fechados** — são sinais de alarme que cumpriram sua função.

---

## Decisões de Produto Pendentes

### [2026-11-11] D-001: Provedor de Email Transacional

**Contexto:** O sistema de email verification precisa enviar emails reais (confirmação de cadastro, verificação). Os PRs de email usam SMTP genérico configurável via env var.

**Pergunta:** Qual provedor usar?

**Opções:**
- **Resend** (resend.com): $0 até 3.000 emails/mês, fácil integração, boa entregabilidade. Pro: barato para começar. Contra: outro serviço externo.
- **SendGrid**: $0 até 100 emails/dia (Free tier), muito estabelecido. Pro: confiável. Contra: free tier muito limitado.
- **SMTP próprio (Gmail ou outro)**: $0, sem dependência. Contra: péssima entregabilidade, pode cair em spam.
- **Mailgun**: $0 até 1.000 emails/mês. Similar ao Resend.

**Recomendação:** Resend — melhor custo-benefício para 1k usuários iniciais, integração simples, sem custo até crescer.

**Status:** PENDENTE — aguardando aprovação do dono.

---

### [2026-11-11] D-002: Supabase Project — Configurado?

**Contexto:** O backend usa Supabase (auth, DB, RLS). Sem um projeto Supabase configurado e as env vars no servidor, nada roda em produção.

**Pergunta:** O projeto Supabase já foi criado? As env vars `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` estão configuradas no Render/deploy?

**Status:** PENDENTE — confirme se existe ou crie em supabase.com (plano Free).

---

### [2026-11-11] D-003: Stripe — Necessário agora?

**Contexto:** Stripe está listado no stack mas as Fases 0 e 1 não exigem pagamento ainda.

**Pergunta:** Devo integrar Stripe neste momento ou deixar para a Fase 2 (assinaturas)?

**Recomendação:** Deixar para Fase 2. Não bloqueia o lançamento.

**Status:** PENDENTE — confirme para eu não implementar antes da hora.

---

*Atualizado em: 2026-11-11 — 170 PRs abertos, bloqueio documentado.*
