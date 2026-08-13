# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 AÇÃO URGENTE — Leia primeiro

### [2026-08-09 → 2026-08-13] LOOP CRÍTICO — 49 PRs abertos, projeto parado

**Contexto:**
O builder autônomo roda 3×/dia mas lê o ROADMAP.md da `main`. Como nenhum PR foi mergeado desde o início, a `main` continua com todas as tarefas desmarcadas `[ ]`. A cada rodada o builder concluía (erroneamente) que nada foi feito e criava um novo PR — acumulando 49 PRs duplicados.

**Log de runs (mais recente no topo):**
- **2026-08-13 (run atual — 3ª vez hoje):** leu DECISOES.md, confirmou bloqueio, NÃO criou novo PR, atualizou log. **5º dia consecutivo sem ação do dono.**
- 2026-08-13 (run 1): leu este documento, NÃO criou novo PR, atualizou log. Projeto continua bloqueado.
- 2026-08-12 (run 2): diagnóstico refeito, nenhum novo PR criado, este arquivo atualizado
- 2026-08-12 (run 1): criou PR #49 duplicado (não leu este arquivo antes)
- 2026-08-11 (run 2): code review completo do PR #46 — aprovado
- 2026-08-11 (run 1): workflow YAML corrigido
- 2026-08-10: sem ação do dono
- 2026-08-09: loop detectado, PR #48 aberto com este documento

**Estado real do projeto:**
- `main`: apenas ROADMAP.md + DECISOES.md (zero código, 0 usuários possíveis)
- **PR #46** (`feature/fase-0.1-cadastro-auth`): implementação **completa, revisada e aprovada** da Fase 0.1
  - Único PR não-draft entre todos os abertos
  - Contém: backend FastAPI + Supabase auth, schema SQL com RLS, 24+ testes passando
  - Link: https://github.com/contaecom23-ai/ClubeUSA/pull/46

**✅ Verificação de qualidade do PR #46 (2026-08-11):**
- FastAPI com CORS restrito, docs desabilitados em produção, rate-limiting ativo ✅
- 24+ testes cobrindo registro, login, JWT, logout, perfil ✅
- Isolamento multi-tenant: `user_id` vem sempre do JWT, nunca do body ✅
- Senha com validação forte (mín. 8 chars, letra + número) ✅
- Erro genérico no login (não revela se foi email ou senha) ✅
- Cleanup de usuário órfão se insert de perfil falhar ✅
- **Conclusão: PR #46 está pronto para merge.**

---

## ✅ Ação necessária do dono — 3 passos

**1. Mergear o PR #46** (código da Fase 0.1):
→ https://github.com/contaecom23-ai/ClubeUSA/pull/46

**2. Mergear este PR #48** (DECISOES.md atualizado + workflow YAML corrigido):
→ https://github.com/contaecom23-ai/ClubeUSA/pull/48

**3. Fechar os PRs #20–#45, #47, #49** como duplicados.
_(Pode fazer em lote no GitHub: Pull Requests > filtrar "is:open" > selecionar > Close)_

Depois dos merges, o próximo run avança automaticamente para Fase 0.2 (Referral).

**Por que o Claude não faz o merge?**
Merge em main é irreversível — exige aprovação do dono (regra do projeto).

**⚠️ CONSEQUÊNCIA REAL:** Cada run que passa sem merge continua desperdiçando compute e não avança o produto. O projeto tem zero código em produção. A Fase 0.2 (referral rastreável) e toda a tração de usuários dependem de 2 cliques seus.

**Status:** PENDENTE DESDE 2026-08-09 — **SEM AÇÃO HÁ 5 DIAS**

---

## Decisões Pendentes (bloqueadas — aguardam Fase 0.1 na main)

### [2026-08-05] Credenciais Supabase

**Contexto:** Backend de auth implementado mas precisa de credenciais reais para funcionar.

**Pergunta:** Você já tem projeto Supabase criado para o Clube USA?

**Opções:**
- **A — Já existe:** passe SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET para o `.env`. Claude configura o resto.
- **B — Criar novo:** gratuito no tier Free; Claude guia o setup.

**Recomendação:** Opção A se já existe, B caso contrário. Free tier do Supabase é suficiente para os primeiros 1.000 usuários.

**Status:** PENDENTE

---

### [2026-08-05] Hospedagem do backend e frontend

**Pergunta:** Tem preferência de hospedagem ou orçamento?

**Opções:**
- **A — Render.com + GitHub Pages (gratuito):** suficiente para os primeiros 1.000 usuários.
- **B — Railway (~$5/mês):** bom DX, escala um pouco mais suave.
- **C — VPS DigitalOcean/Hetzner (~$6/mês):** mais controle, mais config inicial.

**Recomendação:** Opção A — zero custo para começar, sem compromisso.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-13 (run 3 do dia)*
