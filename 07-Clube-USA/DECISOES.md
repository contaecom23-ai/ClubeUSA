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

### [2026-11-02] Provedor de email transacional para confirmação de email (Fase 0.1)
**Contexto:** O sistema envia emails de confirmação via SMTP. O `email_service.py` já está pronto e aceita qualquer provedor SMTP via env vars (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`). Em dev, só loga o link.

**Pergunta:** Qual provedor usar em produção?

**Opções:**
- **A — Resend** (resend.com): UI moderna, free até 3k/mês, SDK Python simples, excelente deliverability. Exige domínio verificado. ~$20/mês acima de 100k/mês. **Recomendação: melhor escolha para este estágio.**
- **B — SendGrid** (sendgrid.com): Mais robusto, free até 100/dia (muito pouco), $19.95/mês para 50k. Overkill para fase 0.
- **C — AWS SES**: $0.10 por 1000 emails, escala ilimitada, mas setup mais complexo (domínio + DKIM + sandbox release). Ótimo se já usa AWS.
- **D — Mailgun**: Free 1k/mês por 3 meses depois pago. Similar ao Resend.

**Recomendação:** Resend — melhor DX, free tier suficiente para os primeiros 1k usuários, muda só as env vars (SMTP é padrão). Não requer mudança de código.

**O que fazer:** Criar conta, verificar domínio `clubeusa.com`, pegar credenciais SMTP e adicionar ao Render/Supabase env vars. Custo: $0 até ~3k emails/mês.

**Status:** PENDENTE

---

*Atualizado em: 2026-06-23*
