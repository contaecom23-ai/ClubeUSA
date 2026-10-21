# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 SITUAÇÃO ATUAL DO PROJETO (2026-08-17)

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
| #9 | fix(security): senha forte + security headers | Fechar — já incluído em #46 |
| #3 | Fase 0.2 — Referral rastreável | ⚠️ Fechar e reconstruir (ver abaixo) |
| #4 | Fase 0.3 — Analytics básico | ⚠️ Fechar e reconstruir (ver abaixo) |
| #5 | Fase 0.4 — Cadastro válido + anti-fraude | ⚠️ Fechar e reconstruir (ver abaixo) |
| #12 | Fase 1.1 — Promoções/Achados | ⚠️ Fechar e reconstruir (ver abaixo) |
| #14 | Fase 1.2 — Busca por ZIP + raio | ⚠️ Fechar e reconstruir (ver abaixo) |
| #16 | Fase 1.3 — Influenciadores pago por resultado | ⚠️ Fechar e reconstruir (ver abaixo) |
| #19 | Fase 1.4 — Empregos (seed manual) | ⚠️ Fechar e reconstruir (ver abaixo) |
| #20 | Fase 1.5 — Moradia (quartos/roommates) | ⚠️ Fechar e reconstruir (ver abaixo) |

---

## ✅ AÇÃO NECESSÁRIA — 2 cliques (estimativa: 5 minutos)

**1. Mergear PR #51** (corrige workflow YAML + atualiza DECISOES.md na main):
→ https://github.com/contaecom23-ai/ClubeUSA/pull/51

**2. Mergear PR #46** (Fase 0.1 completa — backend FastAPI + auth Supabase + 24 testes):
→ https://github.com/contaecom23-ai/ClubeUSA/pull/46

Após esses 2 merges, o próximo run fecha os PRs #3–20 e reconstrói Fase 0.2 corretamente sobre a base da 0.1.

---

## Decisões Pendentes

### [2026-08-16] 🔴 BLOQUEANTE — Mergear PR #51 e PR #46

**Contexto:**
O builder está travado há 10 dias. A cada rodada lê o ROADMAP.md da `main`, vê tudo desmarcado, não tem código para avançar.

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
- FK `user_id → auth.users(id) ON DELETE CASCADE`: corrigido em 2026-08-16 ✅
- Schema SQL válido: RLS habilitado, políticas corretas ✅
- Testes mockam Supabase corretamente, nenhuma chamada real ocorre em CI ✅
- **Conclusão: PR #46 está pronto para merge.**

**Status:** PENDENTE — **10º DIA CONSECUTIVO SEM AÇÃO DO DONO**

---

### [2026-08-16] ⚠️ Conflito arquitetural entre Fase 0.1 (PR #46) e Fases 0.2–1.5 (PRs #3–20)

**Contexto:** Auditado em run 2 de 2026-08-16.

As Fases 0.2–1.5 (PRs #3–20) foram construídas sobre a `main` vazia, **sem a base da Fase 0.1**. Resultado: arquiteturas incompatíveis.

**Opções:**
- **A) Fechar PRs #3–20 + reconstruir do zero** (recomendado): próximo run após merge de #46 cria Fase 0.2 corretamente sobre a base estabelecida. Sem dívida técnica.
- **B) Refatorar PRs existentes**: rebase + ajuste de imports em 9 PRs. Trabalhoso e arriscado.

**Recomendação:** Opção A. A lógica de negócio dos PRs antigos (algoritmo de referral, schema de empregos, etc.) serve de referência, mas a estrutura de código é reconstruída limpa.

**Status:** PENDENTE (depende do merge de #46 primeiro)

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

### 2026-08-17 — 10º dia consecutivo sem ação do dono

- Leu DECISOES.md na branch `docs/decisoes-2026-08-14` (PR #51).
- Situação idêntica: main sem código, PR #46 e #51 aguardando merge do dono.
- Nenhum PR novo criado (bloqueio reconhecido).
- Notificação enviada ao dono via PushNotification.

### 2026-08-16 (run 2) — 9º dia consecutivo sem ação do dono

**Novas descobertas:**
- **Conflito arquitetural confirmado:** Fase 0.2 (PR #3) tem estrutura incompatível com Fase 0.1 (PR #46). PRs #3–20 precisam ser reconstruídos após merge de #46.
- **YAML do workflow em PR #51 verificado:** YAML corrigido é válido.
- Nenhum código novo criado (sem tarefa desbloqueada sem os merges).

### 2026-08-16 (run 1) — 9º dia consecutivo sem ação do dono

- Auditoria completa PR #46 ponta a ponta.
- Bug encontrado e corrigido: FK `user_id → auth.users(id)` ausente no schema SQL.
- Verificação do workflow YAML em main: completamente quebrado. PR #51 tem o YAML corrigido.

### 2026-08-15 (runs 1 e 2) — 7º dia consecutivo sem ação do dono

- Situação idêntica. Nenhum PR mergeado. Nenhum PR novo criado.

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

*Atualizado em: 2026-08-17 (run — 10º dia consecutivo sem ação do dono)*
