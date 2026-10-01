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

### [2026-10-01] Escolha do provider de email para confirmação de conta

**Contexto:**
A feature de confirmação de email (Fase 0.1) está 100% implementada: migration SQL, service, endpoints `POST /auth/email/send` e `POST /auth/email/verify`, testes passando. Só falta configurar as variáveis de ambiente do provider de email. O código já suporta SendGrid e SMTP — zero mudança de código, só `.env`.

**Pergunta:**
Qual provider de email usar para envio do OTP de confirmação?

**Opções:**

| | Provider | Custo | Facilidade | Confiabilidade |
|-|---------|-------|------------|----------------|
| A | **SendGrid** (free tier: 100 emails/dia) | $0 até 100/dia, depois ~$15/mês/40k | Fácil (chave de API) | Alta |
| B | **Resend** (free tier: 3.000 emails/mês) | $0 até 3k/mês, depois $20/mês/50k | Muito fácil | Alta |
| C | **Gmail SMTP** (sua conta Google) | $0 | Médio (senha de app) | Média (limites do Gmail) |
| D | **AWS SES** | ~$0.10/1000 emails | Médio (verificação de domínio obrigatória) | Muito alta |

**Recomendação:** **Resend** (Opção B).
- Free tier mais generoso (3k/mês >> 100/dia do SendGrid)
- API simples — basta `RESEND_API_KEY` e `RESEND_FROM_EMAIL`
- Sem reputação SMTP para gerenciar
- Para escalar de 1k para 100k usuários não muda nada de código

**Para ativar:**
1. Crie conta em resend.com e gere uma API key
2. Verifique o domínio clubeusa.com (DNS TXT record)
3. Adicione ao `.env` / Render environment:
   ```
   SENDGRID_API_KEY=re_...    # Resend usa mesma var ou adicionar suporte nativo
   ENVIRONMENT=production
   SENDGRID_FROM_EMAIL=noreply@clubeusa.com
   ```
   > Nota: o código atual suporta SendGrid e SMTP. Para Resend nativo, uma linha de código adicional (Resend tem SDK Python). Posso adicionar em 10 min se você escolher Resend.

**Migration SQL para rodar no Supabase:**
`clubeusa/db/email_confirmation_migration.sql` — execute antes do deploy.

**Status:** PENDENTE — aguarda escolha do dono

---

*Atualizado em: 2026-10-01*
