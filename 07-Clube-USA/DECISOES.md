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

### [2026-10-21] Configuração de SMTP para confirmação de email (Fase 0.1)

**Contexto:**  
A Fase 0.1 implementou confirmação de email. O código está pronto (`services/email_service.py`), usa SMTP padrão via variáveis de ambiente. Em `ENVIRONMENT=development`, o link de confirmação é apenas logado no servidor — não enviado. Para funcionar em produção, você precisa configurar um provedor de email transacional.

**Pergunta:**  
Qual provedor SMTP usar para enviar os emails de confirmação?

**Opções:**

- **Opção A — Resend** (recomendado):  
  - Prós: gratuito até 3.000 emails/mês, API simples, suporte SMTP padrão, boa deliverability, fácil de configurar  
  - Contras: limite de 3k/mês no free (suficiente para os primeiros 1.000 usuários)  
  - Setup: cadastro em resend.com → criar API key → `SMTP_HOST=smtp.resend.com`, `SMTP_PORT=587`, `SMTP_USER=resend`, `SMTP_PASS=re_...`

- **Opção B — SendGrid**:  
  - Prós: confiável, 100 emails/dia grátis  
  - Contras: processo de aprovação para domínio próprio, limite menor no free tier  

- **Opção C — Gmail SMTP** (conta Google existente):  
  - Prós: zero custo, imediato  
  - Contras: 500 emails/dia máximo, pode ser bloqueado por volume, requer "App Password" no Google  
  - Não recomendado para produção acima de 200 usuários

**Recomendação:**  
Opção A (Resend) — custo zero para os primeiros 1.000 usuários, SMTP padrão compatível com o código atual, boa deliverability. Cadastro leva 5 minutos.

**Para ativar após decidir:**  
Nas variáveis de ambiente do Supabase/Render, adicionar:
```
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=re_SUA_API_KEY_AQUI
SMTP_FROM=Clube USA <noreply@clubeusa.com>
```

**Status:** PENDENTE

---

### [2026-10-21] Aplicar migration SQL da Fase 0.1 no Supabase

**Contexto:**  
O arquivo `07-Clube-USA/clubeusa/db/email_confirmation_migration.sql` precisa ser executado no banco Supabase de produção para adicionar as colunas `email_confirmed`, `email_confirm_token` e `email_confirm_expires_at` na tabela `members`. O código novo depende dessas colunas.

**Pergunta:**  
Confirmar que deseja aplicar a migration. Esta operação é segura (`ADD COLUMN IF NOT EXISTS`) e não perde dados.

**Passos:**
1. Acessar Supabase Dashboard → SQL Editor
2. Colar e executar o conteúdo de `07-Clube-USA/clubeusa/db/email_confirmation_migration.sql`
3. Verificar que as 3 novas colunas apareceram em `members`
4. Deploy do novo código (após configurar SMTP)

**Status:** PENDENTE

---

*Atualizado em: 2026-10-21*
