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

### [2026-08-02] Configuração do Supabase (bloqueador de Fase 0.1)

**Contexto:** O backend FastAPI depende de um projeto Supabase existente. Sem as credenciais, o código está pronto mas não pode ser testado nem implantado.

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA? Se não, precisa criar um e fornecer as credenciais.

**O que precisa ser feito:**
1. Crie um projeto em [supabase.com](https://supabase.com) (plano gratuito é suficiente para Fase 0 com 1k usuários)
2. Em **Settings → API**, copie:
   - `SUPABASE_URL` (ex: `https://xyzxyz.supabase.co`)
   - `service_role key` (NÃO é a `anon key` — é a chave secreta de servidor)
   - `JWT Secret` (em Settings → API → JWT Settings)
3. Em **Authentication → URL Configuration**, configure:
   - **Site URL**: a URL onde o frontend estará hospedado (ex: `https://clubeusa.com`)
   - **Redirect URLs**: mesma URL + `/profile.html`
4. Em **Authentication → Email Templates**, customize os templates para português (opcional mas recomendado)
5. Execute a migration em **SQL Editor → New Query**: copie o conteúdo de `07-Clube-USA/migrations/001_initial.sql`
6. Crie o arquivo `.env` em `07-Clube-USA/backend/` com base no `.env.example`

**Status:** PENDENTE

---

### [2026-08-02] Hospedagem do backend e frontend

**Contexto:** O backend FastAPI precisa ser implantado em algum servidor para funcionar. O frontend são arquivos HTML estáticos.

**Pergunta:** Onde você quer hospedar o Clube USA?

**Opções:**

- **Opção A — Railway** (recomendado para início)
  - Pros: deploy automático via GitHub, plano gratuito tem $5/mês de crédito, zero configuração de servidor
  - Cons: plano pago ~$5-20/mês para produção contínua
  - Frontend: pode ser servido pelo próprio FastAPI (`StaticFiles`) ou Netlify/Vercel grátis

- **Opção B — Render**
  - Pros: plano gratuito para serviços web (dorme após 15min de inatividade), bom para testes
  - Cons: cold start lento (~30s) no plano gratuito — ruim para UX de usuário real
  - Recomendo: usar pago ($7/mês) quando lançar

- **Opção C — Fly.io**
  - Pros: plano gratuito generoso, rápido, global
  - Cons: um pouco mais complexo para configurar

**Recomendação:** Comece com Render (gratuito, plano free) para testes internos. Migre para Railway ou Render pago quando for lançar para usuários reais.

**Status:** PENDENTE

---

### [2026-08-02] Domínio da plataforma

**Contexto:** O frontend e backend precisam de uma URL definitiva para configurar o Supabase (Site URL, email confirmation links, CORS).

**Pergunta:** Qual é o domínio do Clube USA? (ex: `clubeusa.com`, `app.clubeusa.com`)

**O que fazer:** Registre o domínio e aponte para o servidor escolhido na decisão acima.

**Status:** PENDENTE

---

### [2026-08-02] Alerta: workflow do GitHub Actions com YAML malformado

**Contexto:** O arquivo `.github/workflows/clubeusa-builder.yml` tem indentação severamente malformada — `workflow_dispatch`, `permissions` e `jobs` estão aninhados dentro de `schedule` em vez de estarem no mesmo nível de `on`. O workflow atual provavelmente não dispara corretamente pelo GitHub Actions (esta sessão é invocada via Claude Code na web, não via GitHub Actions).

**Pergunta:** Posso corrigir a indentação do YAML? É uma mudança pequena e reversível, mas envolve um arquivo que não criei.

**Recomendação:** Sim — corrigir. É um bug evidente, reversível, sem risco de perda de dados. Posso incluir no próximo PR se aprovar.

**Status:** PENDENTE — aguarda aprovação do dono

---

*Atualizado em: 2026-08-02*
