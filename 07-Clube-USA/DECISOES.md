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

## Decisões Pendentes

---

### [2026-11-09] Provedor de email transacional para verificação de email

**Contexto:** A Fase 0.1 implementou o fluxo completo de verificação de email (token seguro, endpoints, HTML de resposta). O código usa SMTP genérico via smtplib — funciona com qualquer provedor. Em dev, o link é logado no console. Em produção, as variáveis de ambiente `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` precisam ser configuradas.

**Pergunta:** Qual provedor de email usar em produção?

**Opções:**

- **Opção A — Resend (resend.com):** $0 até 3.000 emails/mês, depois $20/mês até 50k. SMTP simples, domínio próprio fácil, dashboard limpo. Pro: barato para começar. Contra: startup nova (menos histórico de entregabilidade).

- **Opção B — SendGrid (Twilio):** $0 até 100 emails/dia, $19.95/mês até 50k. Pro: mercado consolidado, excelente entregabilidade. Contra: UI complicada, free tier bem limitado (100/dia).

- **Opção C — Amazon SES:** $0.10 por 1.000 emails. Baratíssimo em escala. Pro: custo quase zero. Contra: exige conta AWS + verificação de domínio + reputação inicial baixa, setup mais complexo.

- **Opção D — Gmail SMTP (temporário):** Grátis via app password. Pro: zero custo. Contra: limite de 500/dia, domínio @gmail.com em produção não é profissional, não escala.

**Recomendação:** **Opção A (Resend)** para começar. Gratuito até 3k emails/mês (suficiente para os primeiros 3.000 usuários cadastrados), setup em 10 minutos, domínio `@clubeusa.com` facilmente configurado. Migrar para SES quando volume justificar o custo de setup.

**Variáveis a configurar no Render/Supabase:**
```
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=re_XXXXXXXXXXXX  (API key do Resend)
SMTP_FROM=noreply@clubeusa.com
```

**Status:** PENDENTE — aguardando aprovação do dono para criar conta e configurar.

---

*Atualizado em: 2026-11-09*
