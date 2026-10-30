# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

Formato de cada entrada:

```
### [DATA] Título da decisão
**Contexto:** ...
**Pergunta:** ...
**Opções:**
- Opção A: prós / contras
- Opção B: prós / contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## BLOQUEIO CRITICO — ACAO NECESSARIA DO DONO [2026-10-30]

**Situacao:** Ha 30+ PRs abertos no repositorio, NENHUM foi merged em main ate hoje.
O builder autonomo continua criando PRs novos a cada rodada, mas como nenhum entra em main,
cada sessao re-implementa as mesmas features. Fase 0.1 (email confirmation) aparece em
pelo menos 5 PRs diferentes: #148, #147, #115, #106, #75. Isso e desperdicio de recursos.

**Acao imediata recomendada (escolha UMA):**
1. MERGEAR os PRs mais limpos (veja abaixo), ou
2. FECHAR os PRs duplicados e manter so 1 de cada feature, ou
3. INSTRUIR o builder a parar de criar PRs ate que o dono revise — adicionar essa instrucao ao prompt do scheduler

**PRs prioritarios para review (top 5, mais recentes e limpos):**
- PR #148 — `feat/fase-0.1-email-confirm` — confirmacao de email (IMPLEMENTAR PRIMEIRO)
- PR #117 — `feat/fase-0.2-referral-link-rastreavel` — referral URL /i/{code}
- PR #116 — `feat/fase-1.3-influencer-tiers` — tracking de influenciadores
- PR #113 — `feat/fase-1.1-promocoes-comunidade` — submit de promocoes
- PR #109 — `feat/fase-0.3-analytics-growth` — analytics de crescimento

**O que o builder NAO consegue fazer sozinho:** mergear PRs, deployar em producao,
criar contas em servicos externos (SMTP, Stripe live), aprovar gastos.

**Status: PENDENTE — requer acao do dono**

---

## Decisões Pendentes

### [2026-09-07 / 2026-10-26] Provedor de email transacional para confirmação de conta

**Contexto:** A infraestrutura de confirmação de email está pronta (migration `db/email_confirmation_migration.sql` + endpoints `POST /auth/email/send-confirmation` e `GET /auth/email/confirm/{token}` + auto-disparo no cadastro). Em desenvolvimento, o link de verificação é apenas logado no console. Em produção, precisa de um provedor configurado. O código suporta:
- SendGrid (`SENDGRID_API_KEY`, `FROM_EMAIL`)
- SMTP genérico (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`)

**Pergunta:** Qual provedor usar em produção?

**Opções:**
- **Resend** (free: 3.000 emails/mês): prós — moderno, developer-friendly, gratuito até 3k/mês (cobre primeiros 1.000 usuários com folga); contras — menor histórico de mercado
- **SendGrid** (free: 100 emails/dia): prós — mais popular, boa reputação, já no código; contras — free tier apertado (100/dia = ~3.000/mês, mas em burst pode ser insuficiente)
- **AWS SES** ($0,10/1.000 emails): prós — mais barato em escala; contras — requer conta AWS, configuração mais complexa
- **Gmail SMTP**: prós — zero custo inicial; contras — 500 emails/dia, reputação ruim para produção

**Recomendação:** **Resend** para começar — gratuito até 3.000 emails/mês, API simples como SendGrid, troca de provedor é trivial (só mudar env vars para SMTP). Se escalar >3k emails/mês, migrar para AWS SES.

**Ação necessária após decisão:**
1. Criar conta no provedor escolhido e verificar domínio `clubeusa.com`
2. Aplicar migration `db/email_confirmation_migration.sql` no Supabase (Dashboard → SQL Editor)
3. Para SendGrid: configurar `SENDGRID_API_KEY=SG.xxx` e `FROM_EMAIL=noreply@clubeusa.com` e `ENVIRONMENT=production` no Render
4. Para SMTP (Resend/SES): configurar `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`, `ENVIRONMENT=production` no Render

**Status:** PENDENTE

---

### [2026-09-07] Email deve ser obrigatório ou opcional no cadastro?

**Contexto:** O cadastro atual usa telefone como identificador primário (WhatsApp OTP). Email é opcional mas recomendado para confirmação. "Cadastro válido" (Fase 0.4) = phone confirmado + email confirmado + ≥1 ação real.

**Pergunta:** Tornar o email OBRIGATÓRIO no cadastro para forçar confirmação?

**Opções:**
- **Manter opcional (status quo):** prós — menor fricção, maior conversão inicial; contras — muitos cadastros sem email, dificulta email marketing e métricas da Fase 0.4
- **Tornar obrigatório:** prós — base limpa, todos confirmáveis; contras — reduz conversão estimada em ~20-30%

**Recomendação:** Manter opcional agora. Adicionar incentivo pós-cadastro ("confirme seu email e ganhe 50 pontos bônus"). Reavaliar quando atingir 500 cadastros.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-26*
