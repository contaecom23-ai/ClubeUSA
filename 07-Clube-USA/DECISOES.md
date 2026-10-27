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

### [2026-10-27] Provedor de email para confirmação de cadastro (Fase 0.1)

**Contexto:**
A Fase 0.1 implementou o fluxo completo de confirmação de email no backend. O código está pronto e testado. Em `development` funciona sem dependência externa (loga a URL no terminal). Para ativar em `production`, é preciso escolher um provedor e configurar as env vars `EMAIL_PROVIDER`, `EMAIL_API_KEY` e `EMAIL_FROM`.

**Pergunta:**
Qual provedor de email usar para enviar a confirmação de cadastro?

**Opções:**

| Provedor | Free tier | Custo paid | Prós | Contras |
|----------|-----------|------------|------|---------|
| **Resend** | 3.000 emails/mês, 100/dia | USD 20/mês para 50k | API moderna, setup em 5 min, ótima DX, suporte a Next.js/React Email | Mais novo, menor histórico de deliverability |
| **SendGrid** (Twilio) | 100 emails/dia (grátis sempre) | USD 20/mês para 50k | Líder de mercado, alta deliverability, docs maduras | Interface mais complexa, domínio de verificação pode levar mais tempo |
| **AWS SES** | 62.000/mês se hospedado na AWS | USD 0,10 por 1.000 | Mais barato em volume | Setup mais complexo (IAM, DNS, sandbox), pior DX |

**Recomendação do Claude:**
**Resend** — para os primeiros 1.000 usuários o free tier (3k/mês) é suficiente, o setup é <5 minutos, e o código já suporta. Se o volume crescer rapidamente ou deliverability se tornar crítica, migrar para SendGrid é uma mudança de 2 linhas de env var.

**Para ativar:**
```bash
EMAIL_PROVIDER=resend
EMAIL_API_KEY=re_xxxxx   # Criar conta em resend.com, gerar API Key
EMAIL_FROM=noreply@clubeusa.com  # Verificar domínio clubeusa.com no Resend
```

**Status:** PENDENTE

---

*Atualizado em: 2026-10-27*
