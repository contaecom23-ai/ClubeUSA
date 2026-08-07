# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-08-07] Serviço de e-mail transacional para produção

**Contexto:** O sistema de e-mail de confirmação está implementado. Em dev, o link é printado no console. Para produção, precisamos de um serviço SMTP real.

**Pergunta:** Qual serviço de e-mail usar e quem cria a conta?

**Opções:**
- **Resend (resend.com)** — plano gratuito 3.000 emails/mês, API simples, excelente deliverability. Recomendado para startups. ~$20/mês depois de 3k.
- **SendGrid** — mais maduro, 100 emails/dia grátis, depois pago. Mais complexo de configurar.
- **AWS SES** — mais barato em escala ($0.10/1.000), mas requer conta AWS e configuração maior.
- **SMTP próprio (ex: Gmail)** — NÃO recomendado para produção (deliverability ruim, limites baixos).

**Recomendação:** Resend para o lançamento. Simples, barato, funciona bem até ~50k emails/mês. Migrar para AWS SES quando o custo do Resend justificar. Você precisa criar a conta, gerar API key e adicionar ao `.env` como `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` (ou adaptar o code para SDK da Resend se preferir).

**Status:** PENDENTE

---

### [2026-08-07] Rate limiting em produção com múltiplos workers

**Contexto:** O rate limiting de login/registro está implementado com `slowapi` usando memória local (in-process). Isso funciona para 1 processo, mas com múltiplos workers Uvicorn os contadores ficam isolados por processo.

**Pergunta:** Quando escalar para múltiplos workers, quer adicionar Redis para rate limiting centralizado?

**Opções:**
- **Redis** — centralizado, correto, necessário para multi-worker. Custo adicional (Redis Cloud free tier existe).
- **Manter in-memory** — simples, mas rate limit dividido por N workers (menos eficaz).
- **Cloudflare Rate Limiting** — fazer na camada de CDN antes de chegar no app. Mais robusto ainda.

**Recomendação:** Para o lançamento com 1 worker e 1k usuários, in-memory é suficiente. Planejar migração para Redis quando tiver múltiplos workers. Não é urgente agora.

**Status:** PENDENTE — sem ação necessária até escalar horizontalmente

---

### [2026-08-07] Domínio e hospedagem do frontend/backend

**Contexto:** O frontend é HTML estático e o backend é FastAPI. Precisam de hospedagem para lançamento.

**Pergunta:** Onde hospedar o MVP?

**Opções:**
- **Frontend:** Cloudflare Pages (gratuito, CDN global) ou Vercel (gratuito). Recomendo Cloudflare Pages.
- **Backend:** Railway.app (~$5/mês para FastAPI + auto-deploy), Render.com (free tier com cold start), ou VPS (DigitalOcean $6/mês).

**Recomendação:** Frontend no Cloudflare Pages (grátis) + Backend no Railway (simples, sem cold start, ~$5/mês). Total: ~$5/mês para o MVP. Você precisa criar as contas e conectar o repositório.

**Status:** PENDENTE

---

### [2026-08-07] Projeto Supabase

**Contexto:** O schema SQL está pronto em `supabase/migrations/001_initial_schema.sql`. Precisamos de um projeto Supabase real para apontar o backend.

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA?

**O que fazer:**
1. Criar projeto em supabase.com
2. Executar o SQL de migração no SQL Editor do Supabase
3. Copiar `Project URL` e `service_role key` (em Settings > API)
4. Adicionar ao `.env` do backend

**Status:** PENDENTE — aguardando você criar o projeto

---

*Atualizado em: 2026-08-07*
