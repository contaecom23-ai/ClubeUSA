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

### [2026-08-06] 🚨 AÇÃO URGENTE — 46 PRs abertos, projeto parado em loop

**Contexto:**
O builder autônomo roda 3x/dia mas lê o ROADMAP.md da `main`. Como nenhum PR foi mergeado, a `main` continua com todas as tarefas desmarcadas `[ ]`. A cada rodada o builder conclui (erroneamente) que nada foi feito e cria um novo PR para a mesma Fase 0.1 — resultando em 46 PRs duplicados acumulados.

O **PR #46** (`feature/fase-0.1-cadastro-auth`) contém a implementação completa e verificada de Fase 0.1:
- Backend FastAPI: registro, login, `/me`, atualização de perfil, logout
- Rate limiting (5/min registro, 10/min login), JWT via Supabase, CORS restrito
- Frontend HTML: register.html, login.html, dashboard.html, confirm.html
- Schema SQL com RLS: `schema/001_users_profile.sql`
- 24 testes automatizados: **todos passando** (verificado em 2026-08-06)
- CI pipeline: `.github/workflows/test-backend.yml` (adicionado em 2026-08-06)

**Pergunta:**
Pode mergear o PR #46 e fechar os PRs #21–45 (duplicados)?

**Ação necessária (3 passos, ~5 minutos):**
1. Acesse https://github.com/contaecom23-ai/ClubeUSA/pull/46
2. Revise e faça merge do PR #46
3. Feche os PRs duplicados #21 a #45 (pode usar "Close pull request" em cada um, ou pedir ao Claude para fazer em lote após o merge)

**Por que o PR #46 e não outro:**
- É o mais recente e mais completo
- Tem CI adicionado (test-backend.yml) — pipelines rodando automaticamente nos próximos PRs
- Os outros PRs (22–45) têm o mesmo código com pequenas variações; nenhuma vale um merge separado

**O que acontece se nada for feito:**
- O builder continuará criando PR #47, #48, #49… a cada rodada
- Nenhum progresso real será feito no produto

**Recomendação:** Mergear PR #46 agora. Depois o builder avança para Fase 0.2 (Referral).

**Status:** PENDENTE — requer ação do dono do produto

---

### [2026-08-05] Credenciais Supabase — projeto de produção

**Contexto:**
O backend está implementado e testado (com mocks). Para fazer o smoke-test real e ativar o fluxo de email de confirmação, precisamos de credenciais de um projeto Supabase real:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`

Além disso, no painel Supabase você precisa configurar:
1. **Authentication > URL Configuration > Site URL**: `http://localhost:8000` (dev) / domínio real (prod)
2. **Authentication > Email Templates**: personalizar o email de confirmação para Clube USA
3. **Authentication > Settings > JWT expiry**: recomendo 604800 (7 dias)

**Pergunta:**
Você já tem um projeto Supabase criado para o Clube USA? Se sim, pode compartilhar as credenciais via `.env` (sem commitar)?

**Opções:**
- **A) Projeto Supabase já existe**: forneça as credenciais — Claude sobe o schema (`001_users_profile.sql`) e faz smoke-test real.
- **B) Criar projeto novo agora**: acesse app.supabase.com, crie projeto "clube-usa-prod", copie as credenciais.
- **C) Manter mock por ora**: seguir para Fase 0.2 (Referral) no mesmo modo mock; conectar ao Supabase real antes do lançamento.

**Recomendação:**
Opção A ou B o quanto antes — o fluxo de email de confirmação só pode ser validado com Supabase real. Leva ~5 minutos criar o projeto e rodar a migration.

**Status:** PENDENTE

---

### [2026-08-05] Domínio e hospedagem do frontend

**Contexto:**
O frontend é HTML estático (sem framework). Para o lançamento inicial (1k usuários), precisa de hospedagem.

**Pergunta:**
Qual é o domínio e onde quer hospedar o frontend?

**Opções:**
- **A) Vercel/Netlify (gratuito, CDN global)**: melhor opção para HTML estático — deploy em 2 minutos, HTTPS grátis. Recomendado.
- **B) VPS próprio (nginx)**: mais controle, custo baixo (~$5/mês DigitalOcean), mais trabalho de setup.
- **C) Subdomínio Supabase**: não recomendado — acopla infra.

**Recomendação:**
Vercel para o frontend + qualquer VPS ou Railway/Render para o backend FastAPI. Custo mínimo para 1k usuários.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-05*
