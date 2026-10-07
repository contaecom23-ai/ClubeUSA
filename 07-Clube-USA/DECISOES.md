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

### [2026-10-07] Escolha do provider de email para confirmação (Fase 0.1)

**Contexto:** A Fase 0.1 requer envio de email de confirmação. A infraestrutura backend está pronta (tokens, endpoints, testes). Falta ativar o provider em produção.

**Pergunta:** Qual serviço de email usar para o Clube USA?

**Opções:**

- **Resend (resend.com)** — recomendado
  - Free tier: 3.000 emails/mês, 100/dia
  - Setup: criar conta, verificar domínio `clubeusa.com`, gerar `RESEND_API_KEY`
  - Prós: API simples, boa entregabilidade, free tier suficiente para 1k usuários, não requer configuração de SMTP
  - Contras: depende de serviço externo (mas todos dependem)

- **SMTP (Gmail, Mailgun, SendGrid SMTP)**
  - Free tier variado; Gmail tem limite 500/dia
  - Prós: mais controle, pode usar o que já tem
  - Contras: configuração mais manual, deliverability menor com Gmail pessoal

**Recomendação:** Resend — melhor deliverability, API mais simples, free tier suficiente para a Fase 0. Plano pago ($20/mês) quando precisar de mais volume.

**O que precisa fazer:**
1. Criar conta em resend.com
2. Verificar o domínio `clubeusa.com` (adicionar DNS TXT/MX)
3. Adicionar no Supabase/Render/ambiente de produção:
   ```
   EMAIL_PROVIDER=resend
   EMAIL_FROM=noreply@clubeusa.com
   RESEND_API_KEY=re_...
   ```
4. Aplicar migration: `clubeusa/db/email_confirmation_migration.sql` no Supabase SQL Editor

**Status:** PENDENTE

---

*Atualizado em: 2026-10-07*
