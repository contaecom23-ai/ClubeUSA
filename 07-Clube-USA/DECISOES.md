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

### [2026-08-02] BLOQUEIO CRÍTICO: 40 PRs abertos, nenhum mergeado — projeto parado

**Status:** PENDENTE

**Contexto:**

Este é o **maior bloqueio do projeto** e exige ação sua hoje.

O sistema roda 3x ao dia. A cada execução, verifica o `ROADMAP.md` na branch `main` e vê que a Fase 0.1 ainda está sem o `[x]`. Como resultado, cria uma nova branch e abre um novo PR. Isso está acontecendo há semanas.

Situação atual (2026-08-02):
- **40 PRs abertos**, todos drafts, **nenhum mergeado**
- O código da Fase 0.1 está completo e pronto desde a primeira semana
- O **PR mais recente e completo é o #40** (`claude/fase-0-1-cadastro-email`):
  - 1.534 linhas adicionadas
  - 25 arquivos (backend FastAPI, testes, frontend HTML, migration SQL, CI)
  - Estado: **clean** (sem conflito, pode ser mergeado agora)
  - Inclui: autenticação, confirmação de email, perfil, segurança completa, 17 testes

**Por que o loop continua:** O `ROADMAP.md` na `main` nunca é atualizado porque nenhum PR foi mergeado. O Claude vê 0.1 como "não feito" e recomeça do zero.

**Pergunta:**

Você consegue mergear o PR #40 agora? Isso desbloqueia tudo.

Link direto: https://github.com/contaecom23-ai/ClubeUSA/pull/40

**O que fazer depois de mergear o #40:**

1. Fechar os PRs #11 a #39 com a mensagem: *"Fechado — PR #40 é a implementação canônica da Fase 0.1."*
2. O Claude detectará o merge na próxima execução, marcará 0.1 como `[x]` e avançará para a Fase 0.2 (sistema de referral).

**Se você não sabe como mergear um PR:**

1. Abra https://github.com/contaecom23-ai/ClubeUSA/pull/40
2. Clique em **"Ready for review"** (para tirar de draft)
3. Clique em **"Merge pull request"** → **"Confirm merge"**

**Alternativa se o código não está como você quer:**

Se você revisar o PR #40 e ele não estiver certo, deixe um comentário explicando o que falta. O Claude lerá o comentário e corrigirá.

**Enquanto aguardo sua ação:**

O Claude **não vai criar mais PRs para a Fase 0.1**. O código já existe no PR #40. Criar um 41º PR seria desperdício. O Claude vai aguardar você mergear, ou deixar instruções claras no PR #40 sobre o que mudar.

**Decisões técnicas que dependem de você para ir a produção (após merge do #40):**

1. **Supabase:** Você precisa criar um projeto em supabase.com, executar a migration `07-Clube-USA/backend/migrations/001_initial_schema.sql`, e fornecer as variáveis `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`.
2. **Email:** Escolha um provedor SMTP. Recomendo Resend.com (free tier: 3.000 emails/mês). Alternativa: SendGrid (free 100/dia). Você fornece `SMTP_*` vars.
3. **Hospedagem da API:** Recomendo Railway.app (~$5/mês). Alternativa: Render.com (free tier com cold start de 30s). Você conecta o repo e define as env vars.
4. **Hospedagem do frontend:** Cloudflare Pages (gratuito). Você conecta o repo.

**Recomendação do Claude:**

Mergear PR #40 agora. É reversível se encontrar algo errado depois. Não mergear não é "seguro" — é o que mantém o projeto parado há semanas.

---

### [2026-06-23] Supabase — credenciais de produção

**Status:** PENDENTE (bloqueado pelo item acima)

**Contexto:** O backend usa Supabase como banco de dados. Sem credenciais reais, só funciona com mocks em testes.

**Pergunta:** Você tem um projeto Supabase? Pode fornecer `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`?

**Opções:**
- **A) Criar projeto novo em supabase.com** — free tier generoso (500MB, 2 projetos). Recomendado para começar.
- **B) Usar projeto existente** — se já tem um, forneça as credenciais.

**Recomendação:** Opção A. Crie em supabase.com, gere as chaves em Settings → API, e adicione como secrets no GitHub (Settings → Secrets → Actions) para o CI.

---

### [2026-06-23] Provedor de email transacional

**Status:** PENDENTE (bloqueado pelo item acima)

**Contexto:** Emails de confirmação de cadastro precisam ser enviados. Em desenvolvimento, o link aparece só no log — não precisa de SMTP real para testar.

**Pergunta:** Qual provedor usar para produção?

**Opções:**
- **A) Resend.com** — 3.000 emails/mês grátis, API simples, boa reputação. Recomendado.
- **B) SendGrid** — 100 emails/dia grátis, mais complexo de configurar.
- **C) Gmail SMTP** — gratuito mas limitado a 500/dia, pode ser bloqueado como spam.

**Recomendação:** Opção A (Resend.com).

---

*Atualizado em: 2026-08-02*
