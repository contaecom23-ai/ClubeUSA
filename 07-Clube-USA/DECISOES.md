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

### [2026-10-16] Serviço de email transacional em produção
**Contexto:** A Fase 0.1 (email confirmado) foi implementada. O código detecta `SENDGRID_API_KEY` no ambiente: se presente, envia via SendGrid; caso contrário, loga o link (modo dev). Em produção é necessário configurar um provedor.

**Pergunta:** Qual serviço de email usar em produção?

**Opções:**
- **SendGrid (recomendação):** free tier generoso (100 emails/dia), API simples, já no código. Contra: requer conta + verificação de domínio `clubeusa.com`.
- **AWS SES:** mais barato em escala ($0.10/1k), mas setup mais complexo (verificação de domínio/identidade, IAM). Requer refactor do `email_service.py`.
- **Resend.com:** nova alternativa developer-friendly, free tier 3.000/mês, API similar ao SendGrid. Requer refactor.

**Recomendação:** Comece com **SendGrid** — zero custo para os primeiros 1.000 usuários, verificação de domínio leva ~15 min. Migre para SES quando ultrapassar 50k emails/mês.

**O que fazer:** Criar conta em sendgrid.com → criar API Key (Full Access) → adicionar `SENDGRID_API_KEY=SG.xxx` e `FROM_EMAIL=noreply@clubeusa.com` nas variáveis de ambiente do Render → verificar o domínio `clubeusa.com` no SendGrid.

**Status:** PENDENTE — aguardando configuração pelo dono

---

*Atualizado em: 2026-10-16*
