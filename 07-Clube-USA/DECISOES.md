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

### [2026-10-12] Provedor de email para verificação de cadastro

**Contexto:** A FASE 0.1 foi implementada — o fluxo de verificação de email está pronto (endpoints, tokens, HTML de confirmação). O código usa SMTP via env vars (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`). Em dev, apenas loga o link no console. Em produção, precisa de um provedor real configurado.

**Pergunta:** Qual provedor de email usar para envio transacional?

**Opções:**

- **Opção A — SendGrid (recomendado):**
  - Prós: free tier 100 emails/dia; SMTP + API; confiabilidade alta; delivery excelente; monitoramento nativo
  - Contras: conta e verificação de domínio necessária
  - Config: `SMTP_HOST=smtp.sendgrid.net`, `SMTP_PORT=587`, `SMTP_USER=apikey`, `SMTP_PASSWORD=<SG.key>`, `SMTP_FROM=noreply@clubeusa.com`

- **Opção B — Amazon SES:**
  - Prós: muito barato ($0,10/1000); integra bem com infra AWS
  - Contras: sandboxed por padrão; precisa verificar domínio no SES; um pouco mais complexo de configurar
  - Config: similar ao SendGrid via SMTP

- **Opção C — Resend.com:**
  - Prós: API moderna, free tier 3000 emails/mês; muito simples de configurar
  - Contras: relativamente novo, menos consolidado que SendGrid/SES

**Recomendação:** Opção A (SendGrid) — free até 100/dia é suficiente para os primeiros 1.000 usuários, setup em 10 minutos, domínio clubeusa.com verificado. Quando escalar (10k+), migrar para SES pela economia.

**Ação necessária:** Criar conta no SendGrid, verificar domínio clubeusa.com, e adicionar as env vars ao Render/servidor de produção.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-12*
