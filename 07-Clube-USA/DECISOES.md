# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## ⚠️ BLOQUEIO CRÍTICO — AÇÃO NECESSÁRIA (2026-07-22)

### 29 PRs abertos, ZERO mergeados — 20 dias parado

**Situação objetiva:**
O builder roda 3× ao dia desde 2026-07-03. São 20 dias, ~60 execuções.
**Nenhum PR foi mergeado.** O `main` continua só com ROADMAP.md e DECISOES.md.
O código das Fases 0.1 → 1.5 já existe e está escrito. Só falta você agir.

---

## O QUE FAZER AGORA (30 minutos, em ordem)

### PASSO 1 — Mergear UM PR de código

Abra este link no GitHub e clique em **Merge pull request**:

👉 **https://github.com/contaecom23-ai/ClubeUSA/pull/29**

Este é o PR mais recente da Fase 0.1 (branch `feat/fase-0.1-cadastro`).
Contém: API FastAPI + autenticação + email de confirmação + testes + frontend HTML.
É auto-contido, não depende de nenhum outro PR.

### PASSO 2 — Fechar os outros 28 PRs

Vá em https://github.com/contaecom23-ai/ClubeUSA/pulls e feche todos exceto o #29
(que você acabou de mergear). Mensagem sugerida: *"Duplicata — supersedido pelo PR #29"*.

### PASSO 3 — Configurar Supabase (banco de dados)

1. Crie projeto gratuito em https://supabase.com
2. No SQL Editor, execute o arquivo `07-Clube-USA/db/migrations/001_initial.sql` do PR mergeado
3. Em Settings > Database: copie a Connection String (Transaction mode)
4. Configure como secret `DATABASE_URL` no repo (Settings > Secrets > Actions)
5. Gere SECRET_KEY: `python3 -c "import secrets; print(secrets.token_hex(64))"`
   Configure como secret `SECRET_KEY`

### PASSO 4 — Configurar email transacional

**Recomendação: Resend** (https://resend.com — gratuito até 3.000 emails/mês)
1. Crie conta → verifique seu domínio
2. Gere API Key
3. Configure `EMAIL_PROVIDER=resend` e `RESEND_API_KEY=re_xxx` como secrets

**Após o Passo 1, o builder retoma automaticamente a partir da Fase 1.2.**

---

## Por que não criei mais código hoje

O código até a Fase 1.5 já existe em branches aguardando merge.
Criar PR #30 só piora o problema. Esta execução:
- Corrigiu o YAML quebrado do GitHub Actions (`.github/workflows/clubeusa-builder.yml`)
- Atualizou este arquivo para ser visível na main

**Bloqueio técnico real:** o YAML do workflow em `main` estava com indentação completamente errada,
o que impedia o GitHub Actions de disparar corretamente. Esse PR corrige isso também.

---

## Decisões pendentes de produto (responder após merge do Passo 1)

### [2026-07-22] Valor por cadastro válido — Programa de Influenciadores (Fase 1.3)

**Contexto:** O código do programa de influenciadores (PR #16) está pronto.
Parâmetros precisam de decisão de negócio.

**Pergunta:** Qual o valor a pagar por cadastro válido confirmado?

**Opções:**
- **USD 3/cadastro:** mais seguro para o fluxo de caixa, menos atrativo para influenciadores
- **USD 5/cadastro:** equilibrado — recomendado para começar
- **USD 10/cadastro:** mais atrativo, mas risco de fraude maior (precisa anti-fraude robusta)

**Teto mensal sugerido:** USD 500–1.000/mês para começar
**Recomendação Claude:** USD 5/cadastro com teto de USD 500/mês. Ajuste após 30 dias.
**Status:** PENDENTE — o código aceita qualquer valor via env var (`REFERRAL_PAYOUT_USD`)

### [2026-07-22] Domínio e deploy — onde hospedar a API?

**Contexto:** O código está pronto para deploy mas precisa de ambiente.

**Opções:**
- **Railway.app** (free tier generoso, 1-clique deploy com Dockerfile) — recomendado
- **Render.com** (similar, plano gratuito mais limitado)
- **Fly.io** (mais controle, curva maior)
- **Vercel** (só funciona para serverless/Next.js — não adequado para FastAPI)

**Recomendação Claude:** Railway.app para os primeiros 1.000 usuários. Migra para VPS quando custo > USD 50/mês.
**Status:** PENDENTE — decisão de custo (Railway free tier é gratuito para começar)

---

*Atualizado em: 2026-07-22 — 29 PRs abertos, bloqueio ativo há 20 dias*
