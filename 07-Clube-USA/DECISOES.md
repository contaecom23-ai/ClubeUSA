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

### [2026-10-29] Provedor de email para confirmações (Fase 0.1)

**Contexto:** A confirmação de email (Fase 0.1) está implementada com suporte a SMTP genérico. O código funciona com qualquer provedor SMTP. Em dev, loga o link no servidor (não envia email real). Para produção, precisa de um provedor configurado.

**Pergunta:** Qual provedor de email usar para envio transacional?

**Opções:**
- **Resend** (resend.com): $0/mês para 3k emails/mês. API moderna, excelente deliverability, setup simples via SMTP ou API. Recomendado para startups.
- **SendGrid** (sendgrid.com): Free até 100 emails/dia. Mais complexo de configurar. Histórico de problemas de deliverability no free tier.
- **AWS SES**: $0,10/1000 emails. Mais barato em escala, mas requer conta AWS, verificação de domínio, processo burocrático.
- **Gmail SMTP** (conta google existente): Gratuito, mas limitado a 500 emails/dia e tem restrições de uso comercial. Não recomendado para produção.

**Env vars necessárias (qualquer provedor):**
```
SMTP_HOST=smtp.resend.com         # ou smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=resend                  # ou "apikey" no SendGrid
SMTP_PASSWORD=re_xxxx             # chave da API do provedor
FROM_EMAIL=noreply@clubeusa.com   # precisa de domínio verificado
```

**Recomendação:** **Resend** — melhor custo-benefício para 0–10k usuários, setup em 10 min, deliverability superior. Migrar para AWS SES quando ultrapassar 50k emails/mês.

**Próximo passo do dono:** Criar conta no Resend, verificar domínio clubeusa.com, gerar chave API, adicionar ao `.env` de produção.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-29*
