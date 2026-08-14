# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-08-14] 🚨 AÇÃO NECESSÁRIA — Mergear PR #46 para desbloquear o projeto

**Contexto:**
O builder autônomo roda 3x/dia lendo o ROADMAP.md da `main`. Como nenhum PR foi mergeado até hoje, a `main` continua sem código. A cada rodada o builder via todas as tarefas desmarcadas e criava um novo PR para Fase 0.1. Resultado: 50 PRs duplicados acumulados entre junho e agosto de 2026.

**Ação tomada em 2026-08-14:**
- Todos os 49 PRs duplicados (#21–45, #47–50) foram fechados pelo builder
- Restou apenas o **PR #46** (`feature/fase-0.1-cadastro-auth`), que contém a implementação completa

**O que o PR #46 entrega:**
- Backend FastAPI: `/register` (rate-limit 5/min), `/login` (rate-limit 10/min), `/me`, `PUT /me`, `/logout`
- Segurança: JWT via Supabase, user_id sempre do token, CORS restrito, sem hardcode de secrets
- Schema SQL (`schema/001_users_profile.sql`): tabela `users_profile`, trigger `updated_at`, RLS habilitado
- 24 testes automatizados (passando)
- Frontend HTML: register.html, login.html, dashboard.html, confirm.html
- CI pipeline: `.github/workflows/test-backend.yml`

**Pergunta:**
Pode mergear o PR #46 agora?
→ https://github.com/contaecom23-ai/ClubeUSA/pull/46

**Pré-requisitos para o merge funcionar em produção:**
1. Criar projeto no Supabase (gratuito): https://app.supabase.com
2. Configurar env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `FRONTEND_URL`, `ALLOWED_ORIGINS`
3. Rodar o SQL de migration (`07-Clube-USA/schema/001_users_profile.sql`) no SQL Editor do Supabase

**O que acontece após o merge:**
- O builder marca Fase 0.1 como `[x]` no ROADMAP
- Próxima rodada avança para **Fase 0.2** (sistema de referral rastreável)
- O loop de PRs duplicados para definitivamente

**Recomendação:** Mergear PR #46 agora. É a única ação bloqueante.

**Status:** PENDENTE — requer ação do dono do produto

---

### [2026-08-14] Credenciais Supabase e hospedagem

**Contexto:**
O backend está implementado e testado com mocks. Para ativar o fluxo real (email de confirmação, JWT real), são necessárias credenciais de produção.

**Pergunta:**
Você já tem um projeto Supabase criado para o Clube USA?

**Opções:**
- **A) Já tenho projeto Supabase**: forneça as credenciais via `.env` (sem commitar) — Claude sobe o schema e valida.
- **B) Criar agora**: acesse app.supabase.com, crie projeto "clube-usa-prod", copie as credenciais (~5 min).
- **C) Adiar**: seguir para Fase 0.2 (Referral) em modo mock; conectar ao Supabase antes do lançamento.

**Recomendação:** Opção A ou B — o fluxo de email de confirmação só pode ser validado com Supabase real.

**Status:** PENDENTE

---

### [2026-08-14] Domínio e hospedagem

**Pergunta:** Qual é o domínio e onde quer hospedar o frontend e o backend?

**Opções:**
- **Frontend**: Vercel/Netlify (gratuito, CDN global, deploy em 2 min) — recomendado
- **Backend**: Railway/Render (free tier) ou VPS DigitalOcean (~$5/mês)

**Recomendação:** Vercel para frontend + Railway para backend. Custo zero inicial para 1k usuários.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-14*
