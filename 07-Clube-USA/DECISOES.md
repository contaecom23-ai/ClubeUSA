# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 SITUAÇÃO ATUAL DO PROJETO (2026-08-16)

### Estado do repositório

A `main` contém apenas ROADMAP.md, DECISOES.md e o workflow YAML. **Nenhum código foi mergeado ainda. Zero usuários possíveis.**

### O que foi feito pelos runs anteriores

O builder criou ~60 PRs ao longo de junho–agosto por duas razões:
1. O YAML do workflow estava quebrado (indentação inválida → 0 jobs → builder rodava via sessions externas sem restrição)
2. Como a `main` nunca tinha código, cada rodada via o ROADMAP todo desmarcado e criava um novo PR para a mesma Fase 0.1

### PRs restantes abertos (11 no total)

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

**Nota sobre PRs #3–5 e #12–20:** Criados antes de #46 ser mergeado. O código existe e pode ser aproveitado, mas precisarão de rebase quando #46 entrar na main. O builder NÃO criará novos PRs enquanto os existentes estiverem abertos.

---

## ✅ AÇÃO NECESSÁRIA — 2 cliques (estimativa: 5 minutos)

**1. Mergear PR #51** (corrige workflow YAML + atualiza DECISOES.md na main):
→ https://github.com/contaecom23-ai/ClubeUSA/pull/51

**2. Mergear PR #46** (Fase 0.1 completa — backend FastAPI + auth Supabase + 24 testes):
→ https://github.com/contaecom23-ai/ClubeUSA/pull/46

Após esses 2 merges, o próximo run avança automaticamente para Fase 0.2 (referral rastreável).

---

## Decisões Pendentes

### [2026-08-14] 🔴 BLOQUEANTE — Mergear PR #51 e PR #46

**Contexto:**
O builder está travado há 9 dias. A cada rodada lê o ROADMAP.md da `main`, vê tudo desmarcado, não tem código para avançar.

**O que o PR #46 entrega (Fase 0.1):**
- Backend FastAPI com `/register` (rate-limit 5/min), `/login` (rate-limit 10/min), `/me`, `PUT /me`, `/logout`
- Segurança: JWT via Supabase, user_id sempre do token, CORS restrito, zero secrets hardcoded
- Schema SQL: tabela `users_profile`, FK `user_id → auth.users(id) ON DELETE CASCADE`, trigger `updated_at`, RLS habilitado
- 24 testes automatizados (cobertura: registro, login, JWT, logout, perfil, isolamento multi-tenant)
- Frontend HTML: register.html, login.html, dashboard.html, confirm.html

**Verificação de qualidade do PR #46 (auditoria completa em 2026-08-16):**
- FastAPI com CORS restrito, docs desabilitados em produção, rate-limiting ativo ✅
- Isolamento multi-tenant: `user_id` vem sempre do JWT, nunca do body ✅
- Senha com validação forte (mín. 8 chars, letra + número) ✅
- Erro genérico no login (não revela se foi email ou senha) ✅
- FK `user_id → auth.users(id) ON DELETE CASCADE`: **corrigido em 2026-08-16** — evita perfis órfãos ✅
- Schema SQL válido: RLS habilitado, políticas corretas (SELECT/UPDATE próprio perfil; INSERT só via service_role) ✅
- Testes mockam Supabase corretamente, nenhuma chamada real ocorre em CI ✅
- **Conclusão: PR #46 está pronto para merge (+ melhoria de FK aplicada hoje).**

**Pré-requisitos pós-merge para funcionar em produção:**
1. Criar projeto no Supabase: https://app.supabase.com
2. Configurar env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `FRONTEND_URL`, `ALLOWED_ORIGINS`
3. Rodar migration SQL: `07-Clube-USA/schema/001_users_profile.sql`

**Status:** PENDENTE — **9º DIA CONSECUTIVO SEM AÇÃO DO DONO**

---

### [2026-08-14] Credenciais Supabase e hospedagem

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA?

**Opções:**
- **A) Já tenho projeto Supabase**: forneça as credenciais via `.env` (sem commitar)
- **B) Criar agora**: acesse app.supabase.com, crie projeto "clube-usa-prod" (~5 min, grátis)
- **C) Adiar**: seguir para Fase 0.2 em modo mock; conectar ao Supabase antes do lançamento

**Recomendação:** A ou B — o fluxo de email de confirmação só pode ser validado com Supabase real.

**Status:** PENDENTE

---

### [2026-08-14] Domínio e hospedagem

**Opções:**
- **Frontend**: Vercel ou Netlify (gratuito, CDN global)
- **Backend**: Railway ou Render (free tier suficiente para 1k usuários)

**Recomendação:** Vercel para frontend + Railway para backend. Custo zero para os primeiros 1k usuários.

**Status:** PENDENTE

---

## 📋 Histórico de runs (cronologia reversa)

### 2026-08-16 — 9º dia consecutivo sem ação do dono

**Run atual (auditoria completa PR #46):**
- Leu e auditou todo o código do PR #46 ponta a ponta: main.py, routers/auth.py, core/security.py, core/config.py, core/supabase_client.py, models/user.py, tests/conftest.py, tests/test_auth.py, schema/001_users_profile.sql.
- **Bug encontrado e corrigido:** `user_id UUID NOT NULL UNIQUE` sem FK para `auth.users(id)`. Sem essa constraint, perfis ficam órfãos se o usuário for deletado do Supabase Auth (remoção LGPD, banimento, cleanup de teste). **Fix pushado diretamente no branch `feature/fase-0.1-cadastro-auth`** — mudança aditiva, não-destrutiva, segura de fazer autônomo.
- **Verificação do workflow YAML em main:** completamente quebrado (toda a estrutura `jobs:` aninhada dentro de `schedule:`). PR #51 tem o YAML corrigido e válido.
- **Situação geral:** Nenhum PR foi mergeado. O código está pronto. Só falta a ação do dono.
- Notificação enviada.

**Runs anteriores (2026-08-16, run 1):**
- Situação idêntica aos runs anteriores. Nenhum PR foi mergeado.
- **Diagnóstico honesto:** O workflow YAML no branch `main` está completamente quebrado (indentação inválida — tudo aninhado dentro do item `schedule:`, tornando `jobs:` invisível para o GitHub Actions). Isso significa que este run foi provavelmente disparado manualmente via Claude.ai, não via GitHub Actions.
- O PR #51 corrige o workflow YAML. O PR #46 tem o código completo da Fase 0.1.
- O builder **não criou novos PRs** — não há tarefas desbloqueadas sem os merges.
- **Avaliação do código em PRs:** PR #46 está limpo, testado, sem conflitos com a main. PR #51 está clean. Ambos prontos para merge imediato.
- Notificação enviada ao dono do produto.

### 2026-08-15 (run 2) — 7º dia consecutivo sem ação do dono

- Situação idêntica ao run anterior. Nenhum PR foi mergeado.
- Código completo de Fases 0.1–1.5 está em PRs abertos aguardando merge.
- O builder **não criou novos PRs** — não há novas tarefas desbloqueadas.
- Notificação enviada ao dono do produto.

### 2026-08-15 (run 1) — 7º dia consecutivo sem ação do dono

- PR #46 (`feature/fase-0.1-cadastro-auth`) → `mergeable_state: clean`. Nenhum conflito.
- PR #51 (`docs/decisoes-2026-08-14`) → workflow YAML corrigido, DECISOES.md atualizado.
- Nenhuma ação nova tomada. Não há tarefa desbloqueada sem o merge de #51 e #46.

### 2026-08-14 — 6º dia consecutivo

- Leu DECISOES.md no branch `admin/decisoes-desbloqueio-2026-08-09`.
- Confirmou bloqueio. Não criou novo PR. Atualizou log.

### 2026-08-13 (run 3) — Criou PR #50 duplicado

- Não leu DECISOES.md antes. PR #50 é duplicata de #46.

### 2026-08-13 (runs 1 e 2) — Diagnosticou loop

- Leu DECISOES.md, confirmou bloqueio, não criou novos PRs.

### 2026-08-12 — Criou PR #49 duplicado + diagnóstico

- Run 1: criou PR #49 (não leu DECISOES.md antes).
- Run 2: diagnóstico refeito, nenhum novo PR.

### 2026-08-11 — Code review de PR #46 + fix workflow YAML

- Code review completo do PR #46 — aprovado.
- Workflow YAML corrigido.

### 2026-08-09 — Loop detectado

- Loop identificado. PR #48 aberto com diagnóstico e este documento.

---

*Atualizado em: 2026-08-16 (9º dia consecutivo sem ação do dono)*
