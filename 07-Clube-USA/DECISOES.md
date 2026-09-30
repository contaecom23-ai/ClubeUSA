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

### [2026-09-30] Provedor de email transacional para confirmação de cadastro

**Contexto:** A feature de confirmação de email (Fase 0.1) está implementada e pronta para usar — falta só configurar o provedor de email. O código usa variáveis de ambiente SMTP genéricas (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM), compatível com qualquer provedor.

**Pergunta:** Qual provedor de email transacional usar para enviar as confirmações de cadastro?

**Opções:**

- **Opção A — Resend (resend.com)**
  - Prós: Gratuito até 3.000 emails/mês (bom para 1k usuários), setup simples, interface limpa, reputação de entregabilidade boa
  - Contras: Empresa nova (fundada 2022), tier gratuito pode mudar
  - Custo: $0 até 3k/mês → $20/mês até 50k/mês

- **Opção B — SendGrid (sendgrid.com/Twilio)**
  - Prós: Líder de mercado, 100 emails/dia grátis no free forever, boa documentação, dashboard de analytics
  - Contras: Free tier muito restrito (100/dia = 3k/mês), precisa verificar domínio
  - Custo: $0 (100/dia) → $19.95/mês (50k/mês)

- **Opção C — Amazon SES**
  - Prós: Muito barato ($0.10/1k emails), altíssima confiabilidade
  - Contras: Setup mais complexo, precisa de conta AWS, cold start de reputação
  - Custo: $0.10/1k emails (basicamente zero)

- **Opção D — Gmail SMTP (para começar)**
  - Prós: Zero custo, zero setup (já tem conta Google)
  - Contras: Limite de 500 emails/dia (suficiente para os primeiros 1k), não deve ser usado em produção a longo prazo, requer "app password" no Google
  - Custo: $0

**Recomendação:** Opção A (Resend) para começar — setup em 5 minutos, gratuito para os primeiros 1k usuários, transição fácil para plano pago quando crescer. Fallback: Opção D (Gmail SMTP) como bootstrap zero-cost se quiser testar antes de criar conta.

**O que fazer após decidir:**
1. Criar conta no provedor escolhido
2. Verificar o domínio clubeusa.com
3. Adicionar as variáveis de ambiente no Render:
   - `SMTP_HOST` — ex: smtp.resend.com
   - `SMTP_PORT` — 587
   - `SMTP_USER` — resend (ou conforme o provedor)
   - `SMTP_PASS` — a API key do provedor
   - `SMTP_FROM` — "Clube USA <noreply@clubeusa.com>"

**Status:** PENDENTE

---

*Atualizado em: 2026-09-30*
