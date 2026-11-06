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

### [2026-11-06] Serviço de email para verificação de conta

**Contexto:** A fase 0.1 (email confirmado) está implementada. O backend suporta envio via SMTP genérico. Em dev, o link de verificação é logado no console. Em produção, precisa de um provedor SMTP real. Sem isso, nenhum usuário consegue verificar o email.

**Pergunta:** Qual provedor de email usar para o Clube USA?

**Opções:**

- **Opção A — Resend (resend.com)**
  - Prós: simples, $0 até 3.000 emails/mês, SDK moderno, excelente deliverability, dashboard limpo
  - Contras: serviço externo; requer domínio verificado (SPF/DKIM no clubeusa.com)
  - Custo estimado: $0 até ~3k membros; $20/mês até 50k/mês

- **Opção B — SendGrid (sendgrid.com)**
  - Prós: líder de mercado, $0 até 100 emails/dia (free), $20/mês 100k/mês
  - Contras: painel mais complexo, free tier muito restrito para crescimento inicial

- **Opção C — AWS SES**
  - Prós: $0,10/1.000 emails, escala infinita, confiável
  - Contras: requer conta AWS, configuração mais complexa, sandbox inicial (pedir saída)

- **Opção D — Zoho Mail / domínio próprio (SMTP)**
  - Prós: já pode ter no plano do domínio
  - Contras: deliverability inferior, não recomendado para transacional

**Recomendação do Claude:** **Opção A (Resend)** para começar — grátis até 3k emails/mês, que cobre bem os primeiros 1.000 cadastros. Migrar para SES quando volume justificar. Requer configurar SPF/DKIM no DNS do clubeusa.com.

**O que você precisa fazer:**
1. Criar conta em resend.com
2. Verificar domínio clubeusa.com (adicionar registros DNS)
3. Adicionar no .env de produção:
   ```
   SMTP_HOST=smtp.resend.com
   SMTP_PORT=587
   SMTP_USER=resend
   SMTP_PASS=<sua-api-key>
   EMAIL_FROM=noreply@clubeusa.com
   ```

**Status:** PENDENTE

---

*Atualizado em: 2026-11-06*
