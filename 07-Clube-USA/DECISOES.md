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

### [2026-10-30] Qual serviço de email usar em produção?

**Contexto:** A Fase 0.1 implementou confirmação de email. O código detecta automaticamente qual serviço usar via env vars: `RESEND_API_KEY` (Resend) ou `SMTP_HOST` (SMTP genérico). Sem nenhuma das duas, o token é logado (modo dev).

**Pergunta:** Qual serviço de email configurar em produção?

**Opções:**
- **Resend** (`RESEND_API_KEY`): Prós: API simples, 100 emails/dia grátis, ótima entregabilidade, setup em 5min. Contras: custo ~$20/mês acima de 100/dia. **Recomendação: esta para os primeiros 1.000 usuários.**
- **SendGrid** (`SMTP_HOST=smtp.sendgrid.net`): Prós: 100/dia grátis, amplamente conhecido. Contras: painel mais complexo, entregabilidade ok.
- **AWS SES** (`SMTP_HOST=email-smtp.us-east-1.amazonaws.com`): Prós: $0,10/1.000 emails, escala bem. Contras: setup mais complexo, domínio precisa ser verificado.

**Recomendação:** Resend para o lançamento (grátis até 100/dia, suficiente para os primeiros meses). Migrar para AWS SES quando passar de 3.000 emails/dia.

**Ação necessária:** Criar conta em resend.com, verificar domínio clubeusa.com, adicionar `RESEND_API_KEY` + `APP_BASE_URL` + `FROM_EMAIL` nas env vars do Render/Supabase.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-30*
