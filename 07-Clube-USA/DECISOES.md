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

### [2026-10-30] Provedor de email para confirmação de cadastro

**Contexto:**
A Fase 0.1 adicionou fluxo de confirmação de email. A infraestrutura está pronta (`utils/email.py`) com suporte a Resend, SMTP genérico e modo dev (log). Em prod, o `EMAIL_PROVIDER` precisa ser configurado — sem ele, os emails NÃO são enviados.

**Pergunta:**
Qual provedor de email usar para envio transacional (confirmação de cadastro, futuramente alertas de preço)?

**Opções:**

- **Resend** (`EMAIL_PROVIDER=resend`, variável `RESEND_API_KEY`)
  - Pros: API simples, free tier 3.000 emails/mês, excelente deliverability, muito developer-friendly
  - Contras: serviço externo pago a partir de escala ($20/mês após free tier)
  - Recomendado para começar

- **Amazon SES** (`EMAIL_PROVIDER=smtp` + credenciais SES)
  - Pros: muito barato em escala ($0,10/1.000 emails), boa deliverability
  - Contras: setup mais complexo (verificar domínio, sair do sandbox), custo incremental, requer conta AWS

- **SendGrid**
  - Pros: free tier 100/dia, robusto
  - Contras: free tier baixo, pricing cresce rápido

**Recomendação:** Resend para os primeiros 1.000 usuários. Free tier suficiente para validação do produto. Migrar para SES quando escalar (>3k emails/mês).

**Ação necessária pelo dono:**
1. Criar conta em resend.com
2. Verificar domínio clubeusa.com
3. Criar API key
4. Adicionar no Render: `EMAIL_PROVIDER=resend`, `RESEND_API_KEY=re_...`, `EMAIL_FROM=Clube USA <noreply@clubeusa.com>`

**Status:** PENDENTE

---

*Atualizado em: 2026-10-30*
