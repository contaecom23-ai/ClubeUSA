# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ BLOQUEIO CRÍTICO — AÇÃO NECESSÁRIA HOJE

### [2026-07-21] 28 PRs abertos, ZERO mergeados — loop ativo há 18 dias

**Situação em 2026-07-21 (atualização #3 do mesmo bloqueio):**

O builder roda 3x/dia desde ~2026-07-03. São 18 dias, ~54 execuções. **Nenhum PR foi mergeado.** O `main` continua vazio (só ROADMAP.md e DECISOES.md). Cada execução vê o main vazio e para de criar PRs novos só quando reconhece o bloqueio — mas o problema original permanece.

**O que já existe (pronto para usar):**

| PR | Branch | O que tem |
|---|---|---|
| #2 | `claude/fase-0.1-cadastro-perfil-email` | **Mais completo** — Fases 0.1→1.1 num único branch (auth, referral, analytics, anti-fraude, promoções) |
| #3 | `claude/fase-0.2-referral` | Referral rastreável (base em #2) |
| #4 | `claude/fase-0.3-analytics` | Analytics básico (base em #3) |
| #5 | `claude/fase-0.4-valid-registration` | Cadastro válido + anti-fraude (base em #4) |
| #12 | `claude/fase-1.1-promocoes` | Promoções/Achados (base em #5) |
| #14 | `claude/fase-1.2-busca-zip` | Busca por ZIP + raio |
| #16 | `claude/fase-1.3-influenciadores` | Programa de influenciadores |
| #19 | `claude/fase-1.4-empregos` | Board de empregos com seed |
| #20 | `claude/fase-1.5-moradia` | Moradia/roommates com seed |

**Você tem Fases 0.1 → 1.5 codificadas. Zero deploy. Zero produção.**

---

## AÇÃO MÍNIMA NECESSÁRIA (30 minutos)

### Passo 1 — Mergear o PR base

Abra https://github.com/contaecom23-ai/ClubeUSA/pull/2

Este é o PR #2, branch `claude/fase-0.1-cadastro-perfil-email`. Tem a Fase 0.1 completa (auth + perfil + email confirmado + testes). **Mergee este na main.**

Ou, se preferir a versão mais limpa e recente da Fase 0.1 isolada: **PR #27** (branch `feature/fase-0.1-cadastro-email`).

### Passo 2 — Fechar os outros 27 PRs

Feche todos os outros PRs com a mensagem: *"Duplicata — supersedido pelo PR mergeado"*.

### Passo 3 — Configurar Supabase

- Crie projeto em supabase.com (gratuito)
- Execute a migration SQL no painel (o arquivo está em cada PR em `migrations/001_initial_schema.sql`)
- Configure `DATABASE_URL` e `SECRET_KEY` no ambiente de deploy

### Passo 4 — Configurar email transacional

- Resend.com (gratuito até 3.000/mês) — recomendado
- Gere API key, configure `EMAIL_PROVIDER=resend` e `RESEND_API_KEY=re_xxx`

**Após o Passo 1, o builder retoma automaticamente da Fase 1.2 em diante.**

---

## Por que não criei mais código nesta execução

O código até a Fase 1.5 já existe. Criar mais PRs piora o problema (mais para revisar, mais conflitos). Esta execução atualizou apenas este arquivo e não abrirá novo PR.

Franqueza técnica: o único bloqueio real aqui é uma ação de 5 cliques da sua parte — abrir um PR e clicar em Merge.

---

## Decisões de infraestrutura pendentes (após merge do primeiro PR)

### Supabase

**Ação necessária:**
1. Criar projeto em supabase.com
2. Executar `001_initial_schema.sql` no SQL Editor
3. Configurar `DATABASE_URL=postgresql://...` (Settings > Database > Transaction mode)
4. Gerar `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(64))"`

**Status:** PENDENTE

### Email transacional

**Recomendação:** Resend (resend.com) — gratuito até 3.000 emails/mês, 5 min para configurar.

**Ação:**
1. Criar conta em resend.com
2. Verificar domínio
3. Gerar API Key
4. Configurar `EMAIL_PROVIDER=resend` e `RESEND_API_KEY=re_xxx`

**Status:** PENDENTE

### Decisão de produto — Fase 1.3 (influenciadores)

**Contexto:** O código está pronto, mas o programa requer decisão sobre:
- Valor pago por cadastro válido (sugestão: USD 5–10 por cadastro confirmado)
- Teto de orçamento mensal total
- Selos: Parceiro (50 cadastros) / Embaixador (250) / Hall da Fama (1.000)

**Status:** PENDENTE (pode avançar sem isso por ora — o código já tem os parâmetros configuráveis)

---

*Atualizado em: 2026-07-21 — 28 PRs abertos, bloqueio ativo 18 dias*
