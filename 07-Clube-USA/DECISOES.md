# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-08-03] 🚨 BLOQUEIO CRÍTICO: 42 PRs abertos, zero merges — projeto parado

**Contexto:** O agente automatizado rodou 42 vezes desde 2026-07-08 e abriu 42 PRs, nenhum foi mergeado. O branch `main` não tem nenhum código — apenas este ROADMAP.md e DECISOES.md. A cada nova rodada, o agente lê o ROADMAP (onde tudo aparece como `[ ]` não-feito) e re-cria o mesmo PR da Fase 0.1.

**O código está pronto.** O PR #42 (branch `claude/fase-0.1-cadastro-perfil`) tem:
- Backend FastAPI completo (cadastro, login, perfil, confirmação de email)
- Frontend HTML (páginas de cadastro e perfil)
- Migration SQL do banco Supabase
- Testes automatizados
- Todas as regras de segurança aplicadas

**Pergunta direta: Você precisa fazer 3 coisas para o projeto avançar:**

1. **Mergear o PR #42** → https://github.com/contaecom23-ai/ClubeUSA/pull/42
2. **Criar um projeto Supabase** e fornecer as credenciais (ver seção abaixo)
3. **Decidir onde hospedar** (Railway, Render, Fly.io — ver opções abaixo)

**Status:** BLOQUEADO — aguarda ação do dono

---

### [2026-08-03] Configuração do Supabase (bloqueador de Fase 0.1)

**Contexto:** O backend FastAPI do PR #42 depende de um projeto Supabase. Sem credenciais, o código está pronto mas não pode ser testado nem implantado.

**O que precisa ser feito:**
1. Crie um projeto em https://supabase.com (plano gratuito é suficiente para Fase 0 com 1k usuários)
2. Em **Settings → API**, copie:
   - `SUPABASE_URL` (ex: `https://xyzxyz.supabase.co`)
   - `service_role key` (NÃO a `anon key` — é a chave secreta de servidor)
   - `JWT Secret` (em Settings → API → JWT Settings)
3. Em **Authentication → URL Configuration**, configure Site URL e Redirect URLs para o domínio do Clube USA
4. Execute a migration: copie o conteúdo de `07-Clube-USA/migrations/001_initial.sql` no SQL Editor do Supabase
5. Crie o arquivo `.env` em `07-Clube-USA/backend/` baseado no `.env.example` do PR #42

**Status:** PENDENTE — aguarda dono criar o projeto Supabase

---

### [2026-08-03] Hospedagem do backend e frontend

**Pergunta:** Onde hospedar o Clube USA?

**Opções:**

- **Opção A — Railway** (recomendado)
  - Pros: deploy automático via GitHub, simples, $5-20/mês para produção
  - Cons: pago desde o início (sem plano gratuito relevante)

- **Opção B — Render** (bom para testes)
  - Pros: plano gratuito para início, deploy fácil
  - Cons: cold start de ~30s no plano gratuito (ruim para UX); $7/mês no pago

- **Opção C — Fly.io**
  - Pros: plano gratuito generoso, rápido, global
  - Cons: curva de configuração um pouco maior

**Recomendação:** Render gratuito para testes internos → Railway pago quando lançar para usuários reais.

**Status:** PENDENTE — aguarda escolha do dono

---

### [2026-08-03] Domínio da plataforma

**Pergunta:** Qual é o domínio do Clube USA? (ex: `clubeusa.com`, `app.clubeusa.com`)

Necessário para configurar Supabase (Site URL, email de confirmação, CORS) e o hosting.

**Status:** PENDENTE — aguarda dono informar/registrar domínio

---

### [2026-08-03] Correção do YAML do GitHub Actions (reversível)

**Contexto:** O arquivo `.github/workflows/clubeusa-builder.yml` tem indentação severamente malformada — `workflow_dispatch`, `permissions` e `jobs` estão aninhados dentro de `schedule` em vez de estarem no mesmo nível. O workflow provavelmente não dispara pelo GitHub Actions (as sessões atuais são invocadas via Claude Code na web).

**Pergunta:** Posso corrigir a indentação do YAML?

**Recomendação:** Sim — é reversível, sem risco de perda de dados. Mas não é urgente enquanto as sessões rodam via Claude Code na web.

**Status:** PENDENTE — aguarda aprovação

---

*Atualizado em: 2026-08-03*
