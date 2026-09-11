# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 AÇÃO URGENTE — Leia primeiro

### [2026-08-09 → 2026-09-11] LOOP CRÍTICO — 90 PRs abertos, projeto parado há 33 dias

**Contexto:**
O builder autônomo roda 3×/dia mas lê o ROADMAP.md da `main`. Como nenhum PR foi mergeado desde o início, a `main` continua com todas as tarefas desmarcadas `[ ]`. Cada rodada confirma o bloqueio. O projeto tem **zero código em produção**.

**Log de runs (mais recente no topo):**
- **2026-09-11 (run atual):** confirmou bloqueio. 90 PRs abertos. Código pronto para Fase 0.1→1.5 (e 2.1). NÃO criou novo PR — já existem 90. Enviou notificação. **33º dia sem ação do dono.**
- **2026-09-10 (PR #89):** docs de estado criados — ainda sem merge.
- **2026-09-10 (PR #90):** feat(0.3) analytics — ainda sem merge.
- 2026-09-08 (PR #86): docs de estado — ainda sem merge.
- 2026-09-07 (PR #85): feat(fase-0.1) email — sem merge.
- 2026-09-07 (PR #84): feat(fase-0.1+0.2) — sem merge.
- 2026-09-05 (PR #83): feat(0.2) referral — sem merge.
- 2026-09-04 (PR #82): URGENTE plano de merge — sem merge.
- 2026-09-04 (PR #81): docs 3 decisões críticas — sem merge.
- 2026-09-03 (PR #80): fix deploy Z-API — sem merge.
- 2026-09-02 (PR #79): docs estado real — sem merge.
- 2026-09-02 (PR #78): fix auth — sem merge.
- 2026-09-01 (PR #77): docs estado real — sem merge.
- 2026-08-31 (PR #76): fix CI — sem merge.
- 2026-08-29 (PR #75): feat(0.1) email confirmado — sem merge.
- 2026-08-29 (PR #74): docs estado real — sem merge.
- 2026-08-28 (PR #73): docs estado real — sem merge.
- 2026-08-27 (run): confirmou bloqueio, NÃO criou novo PR, atualizou log. **18º dia sem ação do dono.**
- 2026-08-26 (PR #72): docs de estado — sem merge.
- 2026-08-23 (PR #66): docs de estado — sem merge.
- 2026-08-22 (PR #64): docs de estado — sem merge.
- 2026-08-20 (PR #60): docs de estado — sem merge.
- 2026-08-09: loop detectado, PR #48 aberto com este documento.

**Estado real do projeto:**
- `main`: estrutura base + app dealscanner existente. Zero das novas fases implantadas.
- **90 PRs abertos aguardando merge** — nenhum mergeado desde o início
- Código pronto (aguardando merge + infra): Fase 0.1, 0.2, 0.3, 0.4, 1.1, 1.2, 1.3, 1.4, 1.5, 2.1

---

## ✅ O QUE FAZER — 3 passos, por ordem

### Passo 1 — Resolver infraestrutura (BLOQUEANTE para tudo)

Custo: ~$5/mês + $12/ano. Passos:
1. Criar projeto no **Supabase** (gratuito): https://supabase.com
2. Escolher hosting backend: **Railway** (~$5/mês) ou **Render** (grátis com cold start)
3. Registrar domínio: **clubeusa.com** no Cloudflare Registrar (~$12/ano)
4. Dar as credenciais ao Claude: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, domínio

### Passo 2 — Fechar PRs duplicados (reduzir 90→5)

https://github.com/contaecom23-ai/ClubeUSA/pulls

Manter apenas os PRs das últimas versões de cada fase:
- **Fase 0.1+0.2:** PR #87 (feat(fase-0): email + referral)
- **Fase 0.3:** PR #90 (feat(0.3): analytics)
- **Fase 0.4:** PR mais recente de `claude/fase-0.4-valid-registration`
- **Fase 1.x:** PR mais recente de `claude/fase-1.5-moradia` (cumulativo)
- **Fase 2.1:** PR #68 (feat(2.1): assinatura)

Fechar todos os outros com: `duplicado, substituído por versão mais recente`

### Passo 3 — Mergear em ordem

1. PR Fase 0.1+0.2 (auth + referral)
2. PR Fase 0.3 (analytics)
3. PR Fase 0.4 (validação)
4. PRs Fase 1.x em sequência
5. Configurar `.env` com as credenciais do Passo 1
6. Deploy → primeiros usuários

---

## Decisões Técnicas Pendentes (aguardam ação do Passo 1)

### [2026-08-05] Credenciais Supabase

**Contexto:** Backend de auth implementado mas precisa de credenciais reais para funcionar.

**Pergunta:** Você já tem projeto Supabase criado para o Clube USA?

**Opções:**
- **A — Já existe:** passe SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET. Claude configura o resto.
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

*Atualizado em: 2026-09-11 (33º dia sem ação do dono — log atualizado, nenhum novo PR criado)*
