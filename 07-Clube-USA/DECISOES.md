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

### [2026-09-12] D-001: Serviço de email para confirmação de cadastro

**Contexto:**
A infraestrutura de email de confirmação (Fase 0.1) está implementada com abstração plugável via env var `EMAIL_PROVIDER`. Em dev, os emails são apenas logados (não enviados de verdade). Para ativar em produção, basta escolher o provedor e configurar as variáveis de ambiente no Render — sem mudança de código.

**Pergunta:**
Qual serviço de email usar para enviar confirmações de cadastro em produção?

**Opções:**

- **Resend** (resend.com)
  - Prós: Gratuito até 3.000 emails/mês; API REST simples; excelente deliverability; configuração em 10 min; plano pago a partir de $20/mês para 50k emails
  - Contras: Empresa menor, menos legacy que SendGrid
  - Config: `EMAIL_PROVIDER=resend`, `RESEND_API_KEY=re_xxxxx`

- **SendGrid** (sendgrid.com — agora Twilio SendGrid)
  - Prós: Líder de mercado, robusto
  - Contras: Free tier limitado (100 emails/dia — insuficiente); plano Essentials $19.95/mês para 50k emails; UI mais complexa
  - Config: `EMAIL_PROVIDER=sendgrid`, `SENDGRID_API_KEY=SG.xxxxx`

- **Amazon SES**
  - Prós: $0.10 por 1.000 emails (o mais barato em escala)
  - Contras: Requer conta AWS, verificação de domínio mais burocrática, sandbox inicial
  - Melhor para quando ultrapassar 50k emails/mês

**Recomendação:**
**Resend** para os primeiros 1.000 usuários. Gratuito, rápido de configurar, deliverability excelente. Migrar para SES quando ultrapassar 10.000 cadastros/mês e o custo começar a importar.

**Como ativar (Render → Environment):**
```
EMAIL_PROVIDER=resend
RESEND_API_KEY=<chave do painel resend.com>
ENVIRONMENT=production
APP_URL=https://clubeusa.com
```
Importante: verificar o domínio `clubeusa.com` no painel do provedor escolhido antes de ativar.

**Ação necessária:**
1. Criar conta em resend.com
2. Verificar o domínio `clubeusa.com` (adicionar registros DNS conforme instruções do Resend)
3. Criar uma API key
4. Rodar a migration: `clubeusa/db/email_confirmation_migration.sql` no Supabase SQL Editor
5. Configurar env vars no Render conforme acima

**Status:** PENDENTE

---

*Atualizado em: 2026-09-12*
