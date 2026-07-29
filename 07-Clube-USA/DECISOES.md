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

### [2026-07-29] Qual provedor de email SMTP usar para confirmação de conta?

**Contexto:** Fase 0.1 implementou o fluxo de confirmação de email. O backend (FastAPI) envia
email via SMTP. Precisamos de um provedor externo com boa deliverabilidade. Sem isso, usuários
não recebem o email de confirmação e não conseguem ativar a conta.

**Pergunta:** Qual provedor SMTP configurar e com qual conta/domínio?

**Opções:**
- **Opção A — Resend.io** (recomendada): Free tier = 3.000 emails/mês grátis.
  SMTP simples: host `smtp.resend.com`, porta 587, user `resend`, senha = API key.
  Excelente deliverabilidade. Requer criar conta em resend.com e verificar domínio.
  _Prós: grátis para 1k usuários, fácil setup, boa reputação.
  Contras: precisa de domínio verificado (ex: clubeusa.com)._
- **Opção B — SendGrid**: Free tier = 100 emails/dia.
  _Prós: estabelecido, fácil. Contras: 100/dia é muito pouco se o cadastro crescer._
- **Opção C — AWS SES**: $0.10/1000 emails. Requer conta AWS.
  _Prós: baratíssimo em escala. Contras: setup mais trabalhoso, exige conta AWS._
- **Opção D — Gmail pessoal**: Funciona para teste, mas limitado a 500/dia e não confiável para produção.
  _Prós: zero custo imediato. Contras: não escalável, pode ser bloqueado._

**Recomendação:** Opção A (Resend.io). Resolve os primeiros 1–10k usuários de graça e
tem setup em 15 minutos. Só precisa verificar o domínio clubeusa.com e criar API key.

**Ação necessária:** Criar conta em resend.com, verificar domínio, pegar API key e
adicionar ao .env de produção: `SMTP_HOST=smtp.resend.com`, `SMTP_PORT=587`,
`SMTP_USER=resend`, `SMTP_PASSWORD=re_sua_api_key`, `EMAIL_FROM=noreply@clubeusa.com`.

**Status:** PENDENTE

---

### [2026-07-29] Criar projeto Supabase e fornecer credenciais

**Contexto:** O backend precisa de `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` para
funcionar. Também é necessário rodar a migration `database/001_users_schema.sql` no
Supabase para criar a tabela `users`.

**Pergunta:** Você já tem um projeto Supabase para o Clube USA, ou precisa criar um?

**Ação necessária:**
1. Criar projeto em supabase.com (grátis — 500MB, 50k usuários auth, 2 projetos gratuitos).
2. Em Project Settings → API: copiar "Project URL" e "service_role key" (não a anon key).
3. No SQL Editor do Supabase: rodar o conteúdo de `07-Clube-USA/database/001_users_schema.sql`.
4. Adicionar ao `.env` de produção: `SUPABASE_URL=...` e `SUPABASE_SERVICE_ROLE_KEY=...`.

**Status:** PENDENTE

---

### [2026-07-29] Qual é o domínio/URL de produção do Clube USA?

**Contexto:** O `APP_URL` é usado nos links de confirmação de email. Se errado,
os usuários recebem um link que não funciona.

**Pergunta:** Qual será o domínio do Clube USA? (ex: `https://clubeusa.com`)

**Ação necessária:** Definir e configurar `APP_URL=https://seu-dominio.com` no `.env`
de produção. Também atualizar `API_URL` nos arquivos HTML do frontend.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-29*
