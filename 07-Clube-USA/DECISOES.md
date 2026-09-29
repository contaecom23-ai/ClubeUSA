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

### [2026-09-29] Provedor de email transacional para confirmação de email

**Contexto:** A Fase 0.1 foi implementada com infraestrutura completa de confirmação de email (endpoints, token seguro, HTML de confirmação). Em dev, o link é logado no console. Em produção, precisa de um serviço de email.

**Pergunta:** Qual provedor de email transacional usar?

**Opções:**
- **Resend** (resend.com) — Free: 3.000 emails/mês, 100/dia. API REST simples. Já suportado no código (basta definir `RESEND_API_KEY`). Exige conta e domínio verificado.
  - ✅ Generous free tier para 1k usuários
  - ✅ Integração já codificada (`utils/email_sender.py`)
  - ⚠️ Exige verificar domínio clubeusa.com no painel deles
- **SendGrid** — Free: 100 emails/dia. Mais complexo de configurar, mais conhecido.
  - ⚠️ Limite de 100/dia no plano free é apertado
- **Mailgun** — Free: 5.000 emails/mês por 3 meses, depois pago.
  - ⚠️ Teste gratuito limitado
- **AWS SES** — $0,10/1.000 emails. Baratíssimo em escala, mas setup mais complexo (IAM, verificação de domínio, etc.).
  - ✅ Custo quase zero em escala
  - ⚠️ Setup mais trabalhoso

**Recomendação:** Começar com **Resend** (já suportado, free tier suficiente para 1k usuários). Migrar para SES quando ultrapassar 90k emails/mês. Passos: criar conta em resend.com → verificar domínio clubeusa.com → adicionar `RESEND_API_KEY` no `.env` do servidor.

**Status:** PENDENTE

---

*Atualizado em: 2026-09-29*
