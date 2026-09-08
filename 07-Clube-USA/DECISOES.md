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

### [2026-09-08] Provedor de email para confirmação de conta (Fase 0.1)

**Contexto:** O fluxo de confirmação de email está implementado no backend (tokens seguros, hash SHA-256, TTL 24h, endpoints funcionando). Falta apenas configurar um provedor real de envio. Em dev, o link é apenas logado. Em produção, sem provedor configurado, o email não é enviado (falha silenciosa — não quebra o cadastro, mas o usuário não consegue confirmar).

**Pergunta:** Qual provedor de email usar para envio transacional?

**Opções:**

- **Opção A: SendGrid (recomendado)**
  - Prós: Free tier de 100 emails/dia (suficiente para os primeiros 1.000 usuários), integração simples (1 env var), boa entregabilidade, UI simples no dashboard
  - Contras: A conta precisa ser criada e o domínio `clubeusa.com` verificado (SPF/DKIM — ~15 min de setup)
  - Custo: $0 até 100/dia, ~$20/mês para volumes maiores
  - Setup: criar conta em sendgrid.com → gerar API key → adicionar `SENDGRID_API_KEY` no .env de produção

- **Opção B: SMTP via Mailgun**
  - Prós: 1.000 emails/mês grátis, integração via SMTP padrão
  - Contras: Exige verificação de domínio também, interface mais técnica
  - Custo: $0 até 1k/mês

- **Opção C: Não implementar email — manter só WhatsApp OTP**
  - Prós: Público brasileiro no exterior usa muito WhatsApp; OTP via WA já verifica identidade fortemente
  - Contras: Sem email, "cadastro válido" da Fase 0.4 não pode usar email como critério; perda de canal de comunicação
  - Recomendação: NÃO recomendo esta opção — email é essencial para recuperação de conta e comunicação formal

**Recomendação do Claude:** Opção A (SendGrid). Setup de 15 minutos, gratuito para os primeiros 1.000 usuários, e os templates HTML já estão prontos no código.

**Ação necessária pelo dono:**
1. Criar conta em sendgrid.com
2. Verificar domínio clubeusa.com (adicionar registros DNS)
3. Gerar API key com permissão "Mail Send"
4. Adicionar `SENDGRID_API_KEY=SG.xxx` e `EMAIL_FROM=noreply@clubeusa.com` ao .env de produção
5. Executar `email_confirmation_migration.sql` no Supabase SQL Editor

**Status:** PENDENTE

---

### [2026-09-08] Execução da migration email_confirmation_migration.sql

**Contexto:** A migration adiciona `email_confirmed` e `email_confirmed_at` à tabela `members`, e cria a tabela `email_confirmations`. É idempotente (`IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`).

**Pergunta:** Autoriza execução da migration no banco de produção?

**Opções:**
- **Sim:** Executar o arquivo `clubeusa/db/email_confirmation_migration.sql` no Supabase SQL Editor
- **Não:** Manter sem email confirmation por ora

**Recomendação:** Sim — migration é não-destrutiva (apenas adiciona, não altera/remove dados existentes). Segura para executar a qualquer momento.

**Status:** PENDENTE

---

*Atualizado em: 2026-09-08*
