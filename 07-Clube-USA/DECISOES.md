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

### [2026-09-20] D-001: Provedor de email para confirmação de cadastro (Fase 0.1)

**Contexto:**
O fluxo de confirmação de email (Fase 0.1) está implementado e testado. O código suporta Resend e SendGrid via variáveis de ambiente (`RESEND_API_KEY` ou `SENDGRID_API_KEY`). Sem uma chave configurada, o link é apenas logado no console — o cadastro funciona, mas email real não é enviado em produção.

A migration necessária: `clubeusa/db/email_confirm_migration.sql` (adiciona `email_confirmed_at` em `members` + cria tabela `email_verify_tokens`).

**Pergunta:** Qual provedor de email usar e com qual domínio remetente?

**Opções:**

- **A — Resend** (recomendado)
  - Prós: 3.000 emails/mês grátis, API simples, boa reputação de entrega, domínio verificado em 10 min.
  - Contras: empresa mais nova (2022), menos legacy que SendGrid.
  - Custo: grátis até 3k/mês; $20/mês para 50k. Para os primeiros 1.000 usuários: **zero custo**.
  - Config: `RESEND_API_KEY=re_xxxxx`

- **B — SendGrid**
  - Prós: market leader, amplamente testado.
  - Contras: free tier limitado (100/dia — insuficiente para crescimento), configuração mais burocrática.
  - Custo: grátis até 100/dia; $19.95/mês para 50k.
  - Config: `SENDGRID_API_KEY=SG.xxxxx`

- **C — AWS SES**
  - Prós: mais barato em escala ($0,10/1.000 emails).
  - Contras: requer conta AWS, setup mais complexo (sandbox → produção), não suportado no código atual.
  - Relevante a partir de ~50k emails/mês.

**Recomendação:** Resend para os primeiros 1.000 usuários — zero custo, setup em 10 min. Migrar para SES quando chegar perto de 50k/mês.

**Ação necessária do dono:**
1. Criar conta em resend.com
2. Verificar domínio `clubeusa.com` (adicionar DNS TXT — instruções no painel Resend)
3. Gerar API key → adicionar como `RESEND_API_KEY` no Render (Environment > Secret Files)
4. Adicionar `EMAIL_FROM=noreply@clubeusa.com` no Render
5. Executar `clubeusa/db/email_confirm_migration.sql` no Supabase SQL Editor

**Status:** PENDENTE

---

*Atualizado em: 2026-09-20*
