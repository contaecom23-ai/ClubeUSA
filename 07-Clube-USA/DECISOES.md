# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 SITUAÇÃO ATUAL DO PROJETO (2026-08-14)

### Estado do repositório

A `main` contém apenas ROADMAP.md, DECISOES.md e o workflow YAML. **Nenhum código foi mergeado ainda.**

### O que foi feito pelos runs anteriores

O builder criou ~60 PRs ao longo de junho–agosto por duas razões:
1. O YAML do workflow estava quebrado (indentação inválida → 0 jobs → builder rodava via sessions externas sem restrição)
2. Como a `main` nunca tinha código, cada rodada via o ROADMAP todo desmarcado e criava um novo PR para Fase 0.1

### Limpeza realizada

Em 2026-08-14, o builder fechou todos os PRs duplicados.

**PRs restantes abertos (11 no total):**

| PR | Descrição | Ação recomendada |
|----|-----------|------------------|
| **#51** | fix YAML do workflow + DECISOES.md atualizado | **Mergear PRIMEIRO** |
| **#46** | Fase 0.1 — Cadastro + perfil mínimo + email confirmado | **Mergear SEGUNDO** |
| #9 | fix(security): senha forte + security headers | Revisar após #46 |
| #3 | Fase 0.2 — Referral rastreável | Rebase após #46 |
| #4 | Fase 0.3 — Analytics básico | Rebase após #46 |
| #5 | Fase 0.4 — Cadastro válido + anti-fraude | Rebase após #46 |
| #12 | Fase 1.1 — Promoções/Achados | Rebase após #46 |
| #14 | Fase 1.2 — Busca por ZIP + raio | Rebase após #46 |
| #16 | Fase 1.3 — Influenciadores pago por resultado | Rebase após #46 |
| #19 | Fase 1.4 — Empregos (seed manual) | Rebase após #46 |
| #20 | Fase 1.5 — Moradia (quartos/roommates) | Rebase após #46 |

**Nota sobre PRs #3–5 e #12–20:** foram criados antes de #46 ser mergeado (violando a ordem das fases). O código existe e pode ser aproveitado, mas precisarão de rebase em cima do código de 0.1 quando #46 entrar na main. O builder NÃO criará novos PRs para essas fases enquanto os existentes estiverem abertos.

---

## Decisões Pendentes

### [2026-08-14] 🔴 BLOQUEANTE — Mergear PR #51 e PR #46 para desbloquear o projeto

**Contexto:**
O builder está travado. A cada rodada, lê o ROADMAP.md da `main`, vê tudo desmarcado, e sem código para avançar. O único caminho é mergear o trabalho já feito.

**Ordem obrigatória de merge:**
1. **PR #51** — corrige o YAML quebrado do workflow (após merge, o GitHub Actions passa a rodar corretamente) + atualiza DECISOES.md na main
2. **PR #46** — Fase 0.1 completa (FastAPI, Supabase auth, 24 testes, frontend HTML)

**Links diretos:**
- PR #51: https://github.com/contaecom23-ai/ClubeUSA/pull/51
- PR #46: https://github.com/contaecom23-ai/ClubeUSA/pull/46

**O que o PR #46 entrega (Fase 0.1):**
- Backend FastAPI com `/register` (rate-limit 5/min), `/login` (rate-limit 10/min), `/me`, `PUT /me`, `/logout`
- Segurança: JWT via Supabase, user_id sempre do token, CORS restrito, zero secrets hardcoded
- Schema SQL: tabela `users_profile`, trigger `updated_at`, RLS habilitado
- 24 testes automatizados
- Frontend HTML: register.html, login.html, dashboard.html, confirm.html

**Pré-requisitos para funcionar em produção (após merge):**
1. Criar projeto no Supabase: https://app.supabase.com
2. Configurar env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `FRONTEND_URL`, `ALLOWED_ORIGINS`
3. Rodar migration SQL no SQL Editor do Supabase: `07-Clube-USA/schema/001_users_profile.sql`

**Recomendação:** Mergear agora. É a única ação que desbloqueia o projeto.

**Status:** PENDENTE — requer ação do dono do produto

---

### [2026-08-14] Credenciais Supabase e hospedagem

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA?

**Opções:**
- **A) Já tenho projeto Supabase**: forneça as credenciais via `.env` (sem commitar) — Claude sobe o schema e valida
- **B) Criar agora**: acesse app.supabase.com, crie projeto "clube-usa-prod", copie as credenciais (~5 min, grátis)
- **C) Adiar**: seguir para Fase 0.2 em modo mock; conectar ao Supabase antes do lançamento

**Recomendação:** Opção A ou B — o fluxo de email de confirmação só pode ser validado com Supabase real.

**Status:** PENDENTE

---

### [2026-08-14] Domínio e hospedagem

**Pergunta:** Qual é o domínio e onde hospedar frontend e backend?

**Opções:**
- **Frontend**: Vercel ou Netlify (gratuito, CDN global, deploy em 2 min) — recomendado
- **Backend**: Railway ou Render (free tier suficiente para 1k usuários) ou VPS DigitalOcean (~$5/mês)

**Recomendação:** Vercel para frontend + Railway para backend. Custo zero inicial para 1k usuários.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-14 (run 2 do dia — limpeza de 11 PRs duplicados adicionais)*
