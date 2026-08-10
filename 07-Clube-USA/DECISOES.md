# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 AÇÃO URGENTE — Leia primeiro

### [2026-08-10] LOOP CRÍTICO — 48 PRs abertos, projeto parado há semanas

**Contexto:**  
O builder autônomo roda 3×/dia mas lê o ROADMAP.md da `main`. Como nenhum PR foi mergeado desde o início, a `main` continua com todas as tarefas desmarcadas `[ ]`. A cada rodada o builder conclui (erroneamente) que nada foi feito e cria um novo PR para a mesma Fase 0.1 — acumulando 48 PRs duplicados.

**Confirmado em 2026-08-10:** Situação idêntica. Nenhuma ação do dono desde a última verificação (2026-08-09). O builder não criou novo PR neste run — reconheceu o loop e apenas atualiza este documento.

**Estado atual:**
- `main`: apenas ROADMAP.md + DECISOES.md (sem código)
- **PR #46** (`feature/fase-0.1-cadastro-auth`): implementação **completa e verificada** da Fase 0.1
  - Não é draft (único PR aberto que não é draft)
  - Contém: backend FastAPI, frontend HTML, schema SQL com RLS, 24 testes
  - Link: https://github.com/contaecom23-ai/ClubeUSA/pull/46

**Ação necessária (em ordem — 3 cliques no GitHub):**

1. **Mergear o PR #46** → https://github.com/contaecom23-ai/ClubeUSA/pull/46
2. **Fechar os PRs #1–#45 e #47–#48** como duplicados (PR #46 os substitui todos)
3. Depois do merge, o próximo run avançará automaticamente para Fase 0.2 (Referral)

**Por que o Claude não faz o merge?**  
Merge em main é irreversível e exige aprovação do dono (regra do projeto).

**Por que o Claude não fecha os PRs duplicados?**  
Fechar 47 PRs é ação destrutiva em escala — requer autorização explícita do dono.

**Por que o Claude não para de rodar?**  
O schedule continua rodando. A cada run o builder detecta o loop e atualiza apenas este documento, sem criar novo PR.

**Status:** PENDENTE — AÇÃO NECESSÁRIA DO DONO

---

## Decisões Pendentes (bloqueadas por Fase 0.1 não estar na main)

### [2026-08-05] Credenciais Supabase para o projeto Clube USA

**Contexto:** O backend de auth está implementado mas precisa de credenciais reais para funcionar em produção/staging.

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA?

**Opções:**
- **A — Projeto Supabase já existe:** passe as credenciais (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET) para o `.env`. O Claude configura o resto.
- **B — Criar novo projeto Supabase:** gratuito no tier Free para começar; o Claude guia o setup passo a passo.

**Recomendação:** Opção A se já existe, B caso contrário. Plano Free do Supabase é suficiente para os primeiros 1.000 usuários.

**Status:** PENDENTE

---

### [2026-08-05] Hospedagem do backend e frontend

**Contexto:** Com Fase 0.1 mergeada, precisamos de onde hospedar para que usuários reais possam se cadastrar.

**Pergunta:** Você tem preferência de hospedagem ou orçamento para isso?

**Opções:**
- **A — Render.com + GitHub Pages (gratuito):** suficiente para os primeiros 1.000 usuários.
- **B — Railway (~$5/mês):** bom DX, escala um pouco mais suave.
- **C — VPS DigitalOcean/Hetzner (~$6/mês):** mais controle, mais config inicial.

**Recomendação:** Opção A (Render + GitHub Pages) — zero custo para começar, sem compromisso.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-10*
