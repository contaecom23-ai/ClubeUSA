# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 AÇÃO URGENTE — Leia primeiro

### [2026-08-09 → 2026-08-27] LOOP CRÍTICO — 31 PRs abertos, projeto parado há 18 dias

**Contexto:**
O builder autônomo roda 3×/dia mas lê o ROADMAP.md da `main`. Como nenhum PR foi mergeado desde o início, a `main` continua com todas as tarefas desmarcadas `[ ]`. Cada rodada confirma o bloqueio e não cria novo código duplicado — mas o projeto tem **zero código em produção**.

**Log de runs (mais recente no topo):**
- **2026-08-27 (run atual):** confirmou bloqueio, NÃO criou novo PR duplicado, atualizou log. **18º dia consecutivo sem ação do dono.**
- 2026-08-26 (PR #72): docs de estado criados — ainda sem merge.
- 2026-08-23 (PR #66): docs de estado — ainda sem merge.
- 2026-08-22 (PR #64): docs de estado — ainda sem merge.
- 2026-08-20 (PR #60): docs de estado — ainda sem merge.
- 2026-08-19 (PR #59): docs de estado — ainda sem merge.
- 2026-08-17 (PR #53): docs de estado — ainda sem merge.
- 2026-08-14 (run): leu DECISOES.md, NÃO criou novo PR, atualizou log.
- 2026-08-13 (run 3): leu DECISOES.md, NÃO criou novo PR, atualizou log.
- 2026-08-13 (runs 1-2): criou PR #50 duplicado — não leu DECISOES.md antes.
- 2026-08-12 (run 2): diagnóstico refeito, nenhum novo PR criado.
- 2026-08-11 (run 2): code review completo do PR #46 — aprovado.
- 2026-08-09: loop detectado, PR #48 aberto com este documento.

**Estado real do projeto:**
- `main`: apenas ROADMAP.md + DECISOES.md (zero código, 0 usuários possíveis)
- **31 PRs abertos aguardando merge**
- Todo código de Fase 0.1 → 2.1 já implementado em branches

---

## ✅ AÇÃO NECESSÁRIA — 3 passos AGORA

### Passo 1 — Mergear PR #46 (Fase 0.1 — código pronto para produção)
→ https://github.com/contaecom23-ai/ClubeUSA/pull/46

**Por que este primeiro:** É o único PR não-draft, base na `main`, revisado e aprovado. Contém:
- Backend FastAPI + Supabase auth completo
- Schema SQL com RLS
- 24+ testes passando
- Rate-limiting, CORS restrito, JWT com TTL correto

### Passo 2 — Fechar os PRs duplicados em lote
Vá em: https://github.com/contaecom23-ai/ClubeUSA/pulls
Filtro: `is:open is:pr` → selecione todos EXCETO #46 → Close with comment: "duplicado, PRs mais recentes substituem este"

### Passo 3 — Responder 2 perguntas técnicas (abaixo)
Depois do merge do #46, o próximo run avança automaticamente para Fase 0.2 (Referral).

---

## ✅ Verificação de qualidade do PR #46 (revisão 2026-08-11)
- FastAPI com CORS restrito, docs desabilitados em produção, rate-limiting ativo ✅
- 24+ testes cobrindo registro, login, JWT, logout, perfil ✅
- Isolamento multi-tenant: `user_id` vem sempre do JWT, nunca do body ✅
- Senha com validação forte (mín. 8 chars, letra + número) ✅
- Erro genérico no login (não revela se foi email ou senha) ✅
- Cleanup de usuário órfão se insert de perfil falhar ✅
- **Conclusão: PR #46 está pronto para merge.**

---

## Decisões Técnicas Pendentes (aguardam Fase 0.1 na main)

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

*Atualizado em: 2026-08-27 (18º dia sem ação do dono — projeto parado)*
