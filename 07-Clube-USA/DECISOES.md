# DECISÕES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.
> Formato: data, contexto, pergunta, opções, recomendação, status.

---

## ⚠️ D-001 — AÇÃO URGENTE: 30+ PRs prontos aguardando merge [2026-09-24]

**Contexto:**
O projeto tem múltiplos PRs prontos (Fase 0.1 a 2.1) que não foram mergeados. O código já está escrito e testado — o bloqueio é operacional, não técnico. A cada sessão sem merge, novos PRs duplicados são criados, aumentando o ruído.

**Ação recomendada (em ordem, ~30 minutos):**

**Passo 1** — Configurar SMTP para email (necessário antes do PR #106):
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu@gmail.com
SMTP_PASSWORD=sua_app_password
SMTP_FROM=noreply@clubeusa.com
```

**Passo 2** — Rodar migração de banco (PR #106):
```sql
-- Copiar e executar no Supabase: 07-Clube-USA/clubeusa/db/email_confirm_migration.sql
```

**Passo 3** — Mergear PRs NESTA ORDEM:
1. **PR #106** — Email confirmação (Fase 0.1) → precisa dos passos 1 e 2 acima
2. **PR #102** — Referral `/i/{code}` redirect (Fase 0.2) → sem requisitos
3. **PR deste PR** — Analytics growth time-series (Fase 0.3) → sem requisitos
4. **PR #104** — Cadastro válido + anti-fraude (Fase 0.4) → sem requisitos
5. **PR #97** — Deals urgency (Fase 1.1) → sem requisitos

**Passo 4** — Fechar PRs duplicados:
Fechar todos os outros PRs de Fase 0.x e 1.x (há ~20 PRs obsoletos). São versões antigas do mesmo código, já supersedidas pelos PRs acima.

**Status:** PENDENTE — aguardando ação do dono

---

## D-002 — Provedor SMTP para email [2026-09-23]

**Contexto:** PR #106 (email confirmação) precisa de SMTP configurado para enviar emails de confirmação.

**Opções:**
- **Gmail App Password** — grátis, limite 500/dia. Pro: sem custo. Contra: limite baixo, não é profissional.
- **SendGrid free tier** — 100 emails/dia grátis, 100k/mês no plano pago ($19.95). Pro: profissional, boa entregabilidade. Contra: requer conta.
- **Resend** — 3k emails/mês grátis, $20/mês para 50k. Pro: API simples, feito para devs. Contra: mais novo.

**Recomendação:** Resend para começar (grátis até 3k/mês, suficiente para os primeiros 1.000 usuários, API limpa). Migrar para SendGrid quando passar de 3k/mês.

**Status:** PENDENTE — aguardando escolha do dono

---

## D-003 — Domínio e deploy [2026-09-22]

**Contexto:** A API está no código mas não há deploy configurado. O `render.yaml` existe mas não sabemos se a conta Render está ativa.

**Pergunta:** Onde está rodando a versão atual do Clube USA? Render? VPS? Local apenas?

**Opções:**
- Render (free tier): grátis mas com cold start de 30s. Suficiente para MVP.
- Railway: $5/mês. Sem cold start, mais confiável.
- VPS (DigitalOcean/Hetzner): $6-12/mês. Controle total.

**Recomendação:** Render free tier para MVP (<1.000 usuários). Migrar para Railway ou VPS quando tiver tráfego real.

**Status:** PENDENTE — aguardando confirmação do ambiente atual

---

*Atualizado em: 2026-09-24*
