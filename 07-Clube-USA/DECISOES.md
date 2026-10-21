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

### [2026-10-21] Provedor de email transacional

**Contexto:** Fase 0.1 implementou a confirmação de email. O backend está pronto: gera token, armazena, verifica, expira em 24h. Falta configurar um provedor real para envio. Em dev/homologação o token é apenas logado no console (sem envio real).

**Pergunta:** Qual provedor de email transacional usar para os primeiros 1.000 usuários?

**Opções:**

- **Resend** (recomendado)
  - Prós: tier gratuito 3.000 emails/mês; API HTTP simples sem SDK extra; excelente DX; painel limpo; domínio personalizado fácil
  - Contras: startup relativamente novo (desde 2023), mas com boa adoção; sem SLA gratuito
  - Custo: $0 até 3k emails/mês → ~$20/mês para 50k emails

- **SendGrid**
  - Prós: tier gratuito 100 emails/dia; consolidado no mercado
  - Contras: UI complexa; tier gratuito é apertado para crescimento rápido

- **AWS SES**
  - Prós: muito barato em escala ($0.10/1.000 emails)
  - Contras: setup mais complexo (domínio verificado, saída do sandbox); custo de manter infra AWS

**Recomendação:** Resend — simplicidade operacional para os primeiros 1.000 usuários, free tier suficiente, sem over-engineering. Migra para SES quando ultrapassar 50k emails/mês.

**Para ativar:** Criar conta em resend.com → Add Domain (clubeusa.com) → gerar API Key → adicionar `RESEND_API_KEY=re_...` e `EMAIL_FROM=Clube USA <noreply@clubeusa.com>` nas env vars do Render.

**Status:** PENDENTE (aguarda aprovação e criação de conta)

---

*Atualizado em: 2026-10-21*
