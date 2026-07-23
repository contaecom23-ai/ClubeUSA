# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## ⚠️ BLOQUEIO CRÍTICO — AÇÃO NECESSÁRIA (atualizado 2026-07-23)

### 30 PRs abertos, ZERO mergeados — 21 dias parado

**Situação objetiva:**
O builder roda 3× ao dia desde 2026-07-03. São 21 dias, ~63 execuções.
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

### PASSO 2 — Fechar os outros 29 PRs

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

## Auditoria de código — PR #29 (2026-07-23)

Auditei o código do PR #29 (`feat/fase-0.1-cadastro`) nesta execução. **É seguro mergear.**

**O que está correto:**
- bcrypt 12 rounds para senhas; nunca exposta em log
- JWT HMAC-SHA256 via stdlib Python com `hmac.compare_digest` (constant-time)
- `user_id` sempre extraído do token no servidor, nunca do request body
- Rate limit em register (5/min), login (10/min), resend-confirm (3/min), forgot-password (3/min)
- Token de refresh valida campo `type` — não pode ser usado como access token e vice-versa
- Mensagens genéricas em login e forgot-password (anti-enumeração de e-mails)
- Email de confirmação bloqueante antes do login
- SECRET_KEY gera chave efêmera + warning se não configurada; bloqueia em produção
- SQLite bloqueado em `ENVIRONMENT=production`

**Uma issue identificada (não bloqueia merge, resolver antes de conectar Supabase):**

Em `api/auth/service.py`, as comparações de data usam `.replace(tzinfo=timezone.utc)`:
```python
if expires and expires.replace(tzinfo=timezone.utc) < now:
```
Isso funciona com SQLite (que retorna datetimes sem timezone — naive UTC).
Com PostgreSQL/Supabase (que retorna datetimes timezone-aware), o `.replace()` descarta
o timezone existente em vez de converter — comportamento silenciosamente errado.
**Correção:** usar `.astimezone(timezone.utc)` no lugar de `.replace(tzinfo=timezone.utc)`.
Adicionarei esse fix como primeiro commit após o merge do PR #29.

**Decisão de trade-off documentada:**
Os refresh tokens são stateless (JWT), não armazenados no banco. Isso significa que
token comprometido é válido por até 30 dias sem possibilidade de revogação.
Para V0/1.000 usuários, esse trade-off é aceitável. Adicionar tabela de revogação na Fase 1.

## Por que não criei mais código nesta execução

O código até a Fase 1.5 já existe em branches aguardando merge.
Criar PR #31 só piora o bloqueio. Esta execução:
- Auditou o código do PR #29 (resultado: aprovado para merge)
- Identificou e documentou a issue do datetime (fix preparado para após merge)
- Atualizou este arquivo com o estado real (30 PRs, dia 21)

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

*Atualizado em: 2026-07-23 — 30 PRs abertos, bloqueio ativo há 21 dias | PR #29 auditado e aprovado*
