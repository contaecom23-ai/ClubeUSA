# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-08-07] ⛔ BLOQUEIO CRÍTICO — 47 PRs abertos, projeto parado há 3+ semanas

**Contexto:**
Execução autônoma de 2026-08-07. Detectei o bloqueio antes de criar um 48° PR. **Não enviei código desta vez.** A implementação local está pronta e testada (23/23 testes passando — FastAPI + bcrypt + JWT + rate-limit + 5 páginas HTML em PT-BR), mas não foi empurrada para evitar duplicata.

**Estado em 2026-08-07:**
- **47 PRs abertos**, todos implementando Fase 0.1. Zero mergeados.
- Este loop existe desde 2026-06-23. Documentado em 2026-07-14, 17, 19, 25 e agora 08-07. **Nada mudou.**
- Cada run do agente detecta Fase 0.1 como não-concluída → implementa → abre PR → ninguém mergeia → próxima run repete.

**O que você precisa fazer — 15 minutos:**

1. **Mergeie o PR #46** (`feature/fase-0.1-cadastro-auth`, criado 2026-08-05, título: "feat: Fase 0.1 [MERGEAR ESTE]").
   - Alternativa: PR #47 (o mais recente, 2026-08-07) também é uma implementação limpa.

2. **Feche todos os outros PRs de Fase 0.1** com comentário "Duplicata — mergeando PR #46".

3. **Rode a migration SQL no Supabase:**
   - Arquivo: `07-Clube-USA/supabase/migrations/001_initial_schema.sql`
   - Supabase Dashboard → SQL Editor → cole e execute.

4. **Configure as variáveis de ambiente** (ver decisão de Supabase abaixo).

5. **Após o merge**, na próxima run o agente detecta 0.1 como concluída e avança para **Fase 0.2 (Referral)**.

**Por que o loop acontece:** o agente verifica se Fase 0.1 está na `main`. Como a `main` nunca muda (sem merge), o agente sempre vê 0.1 como pendente e recomeça do zero.

**Status:** PENDENTE CRÍTICO — bloqueando todo progresso. Esta é a 6ª notificação.

---

### [2026-08-07] Serviço de e-mail transacional para produção

**Contexto:** O sistema de e-mail de confirmação está implementado. Em dev, o link é printado no console. Para produção, precisamos de um serviço SMTP real.

**Pergunta:** Qual serviço de e-mail usar e quem cria a conta?

**Opções:**
- **Resend (resend.com)** — plano gratuito 3.000 emails/mês, API simples, excelente deliverability. ~$20/mês depois de 3k.
- **SendGrid** — mais maduro, 100 emails/dia grátis, depois pago.
- **AWS SES** — mais barato em escala ($0.10/1.000), requer conta AWS e mais configuração.

**Recomendação:** Resend para o lançamento. Você precisa criar a conta, gerar API key e adicionar ao `.env` como `SMTP_HOST=smtp.resend.com`, `SMTP_USER=resend`, `SMTP_PASSWORD=sua-api-key`.

**Status:** PENDENTE

---

### [2026-08-07] Rate limiting em produção com múltiplos workers

**Contexto:** Rate limiting atual é in-process (in-memory). Com múltiplos workers Uvicorn, os contadores ficam isolados por processo (menos eficaz).

**Recomendação:** In-memory é suficiente para 1 worker e 1k usuários. Planejar migração para Redis quando escalar horizontalmente. Não urgente agora.

**Status:** PENDENTE — sem ação necessária até escalar horizontalmente

---

### [2026-08-07] Domínio e hospedagem do frontend/backend

**Recomendação:** Frontend no Cloudflare Pages (grátis) + Backend no Railway (~$5/mês). Total: ~$5/mês para o MVP. Você precisa criar as contas e conectar o repositório.

**Status:** PENDENTE

---

### [2026-08-07] Projeto Supabase

**O que fazer:**
1. Criar projeto em supabase.com (gratuito)
2. Executar o SQL de migração no SQL Editor: `07-Clube-USA/supabase/migrations/001_initial_schema.sql`
3. Copiar `Project URL` e `service_role key` (Settings > API)
4. Adicionar ao `.env` do backend: `SUPABASE_URL=...` e `SUPABASE_SERVICE_ROLE_KEY=...`

**Status:** PENDENTE — aguardando você criar o projeto

---

*Atualizado em: 2026-08-07*
