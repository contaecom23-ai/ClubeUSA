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

### [2026-09-07/2026-10-16] Provedor de email transacional para confirmação de conta

**Contexto:** A infraestrutura de confirmação de email está pronta (migration SQL + endpoints + service). Para funcionar em produção, precisa de um provedor configurado via variáveis de ambiente. O código suporta:
- SendGrid (`SENDGRID_API_KEY`, `FROM_EMAIL`)
- SMTP genérico (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`)

**Pergunta:** Qual provedor usar em produção?

**Opções:**
- **Resend** (free: 3.000 emails/mês): prós — moderno, developer-friendly, gratuito até 3k/mês (cobre primeiros 1.000 usuários com folga); contras — menor histórico de mercado
- **SendGrid** (free: 100 emails/dia): prós — mais popular, boa reputação, já no código; contras — free tier apertado (100/dia = ~3.000/mês, mas em burst pode ser insuficiente)
- **AWS SES** ($0,10/1.000 emails): prós — mais barato em escala; contras — requer conta AWS, configuração mais complexa
- **Gmail SMTP**: prós — zero custo inicial; contras — 500 emails/dia, reputação ruim para produção

**Recomendação:** **Resend** para começar — gratuito até 3.000 emails/mês, API simples como SendGrid, troca de provedor é trivial (só mudar env vars para SMTP). Se escalar >3k emails/mês, migrar para AWS SES.

**Ação necessária após decisão:**
1. Criar conta no provedor escolhido e verificar domínio `clubeusa.com`
2. Aplicar migration `db/email_confirmation_migration.sql` no Supabase (Dashboard → SQL Editor)
3. Para SendGrid: configurar `SENDGRID_API_KEY=SG.xxx` e `FROM_EMAIL=noreply@clubeusa.com` e `ENVIRONMENT=production` no Render
4. Para SMTP (Resend/SES): configurar `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`, `ENVIRONMENT=production` no Render

**Status:** PENDENTE

---

### [2026-09-07] Email deve ser obrigatório ou opcional no cadastro?

**Contexto:** O cadastro atual usa telefone como identificador primário (WhatsApp OTP). Email é opcional mas recomendado para confirmação. "Cadastro válido" (Fase 0.4) = phone confirmado + email confirmado + ≥1 ação real.

**Pergunta:** Tornar o email OBRIGATÓRIO no cadastro para forçar confirmação?

**Opções:**
- **Manter opcional (status quo):** prós — menor fricção, maior conversão inicial; contras — muitos cadastros sem email, dificulta email marketing e métricas da Fase 0.4
- **Tornar obrigatório:** prós — base limpa, todos confirmáveis; contras — reduz conversão estimada em ~20-30%

**Recomendação:** Manter opcional agora. Adicionar incentivo pós-cadastro ("confirme seu email e ganhe 50 pontos bônus"). Reavaliar quando atingir 500 cadastros.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-16*
