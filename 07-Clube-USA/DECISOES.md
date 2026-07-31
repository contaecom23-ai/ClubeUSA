# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

Formato de cada entrada:

```
### [DATA] Título da decisão
**Contexto:** ...
**Pergunta:** ...
**Opções:**
- Opção A: prós / contras
- Opção B: prós / contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## ⚠️ URGENTE — Decisões Pendentes

### [2026-07-31] BLOQUEADOR CRÍTICO: 37 PRs duplicados abertos — o agente está em loop

**Contexto:** O agente autônomo roda 3x ao dia e a cada execução verifica o ROADMAP. Como nenhum PR foi mergeado na `main`, o ROADMAP ainda mostra a Fase 0.1 como `[ ]` (não feita). Resultado: o agente criou **37 PRs de draft abertos** — mais de 25 são cópias quase idênticas de "Fase 0.1: cadastro + perfil mínimo + email confirmado". O código da Fase 0.1 está pronto, mas sem merge na main o agente continua duplicando.

**Situação atual:**
- `main` não tem nenhum código da plataforma (só ROADMAP.md e DECISOES.md)
- PR #37 (`feat/fase-0.1-cadastro-email`, criado em 2026-07-30) é o **mais recente e completo**
- PRs #8 a #36: duplicatas do mesmo conteúdo (muitas variações menores da Fase 0.1)
- PRs #12–#20: chegam a Fase 1.4–1.5, mas baseados em branches que nunca foram mergeadas em `main`

**O que o PR #37 contém (revisado e confirmado):**
- Backend FastAPI: `app/auth/`, `app/users/`, `app/email/`, `config.py`, `database.py`, `deps.py`, `models.py`, `rate_limit.py`, `schemas.py`, `main.py`
- Migrations SQL: `migrations/001_initial_schema.sql`
- Frontend HTML: página de cadastro, login e confirmação de email
- Testes: suite pytest com isolamento multi-tenant
- `.env.example` com todas as variáveis necessárias
- 4 decisões pendentes documentadas (Supabase URL, SMTP, domínio, JWT storage)

**Pergunta:** O que fazer com os 37 PRs?

**Opções:**

- **Opção A (RECOMENDADA):** Mergear PR #37 → fechar manualmente os PRs #8 a #36 como "não será mergeado" (stale/duplicado). Isso desbloqueia o agente, que marcará Fase 0.1 como `[x]` e avançará para 0.2 (REFERRAL).
  - Prós: limpo, histórico preservado, código verificado.
  - Contras: requer sua ação em ~15 min para fechar os outros 36 PRs.

- **Opção B:** Ignorar e mergear apenas o PR #37. Os outros permanecem abertos mas sem efeito prático. O agente parará de duplicar após o merge na main.
  - Prós: mais rápido (só 1 ação).
  - Contras: deixa lixo visual de 36 PRs abertos no repositório.

- **Opção C:** Não agir — o agente continuará criando ~3 novos PRs por dia indefinidamente.
  - Prós: nenhum.
  - Contras: PR #38, #39... serão criados nas próximas execuções. Ruído total.

**Recomendação:** **Opção A** — mergear o PR #37 primeiro, depois fechar os outros como "stale". GitHub permite fechar vários PRs em sequência rapidamente. Assim o projeto avança para Fase 0.2 e o agente para de loops.

**Próxima ação do dono:**
1. Acesse: https://github.com/contaecom23-ai/ClubeUSA/pull/37
2. Revise o código
3. Preencha `.env` com as credenciais (veja decisões abaixo)
4. Mergee o PR #37
5. Feche os PRs #8 a #36 como "stale"

**Status:** PENDENTE — BLOQUEADOR

---

### [2026-07-30] Credenciais do Supabase (DATABASE_URL)

**Contexto:** O backend (Fase 0.1) está pronto mas precisa de uma string de conexão PostgreSQL para rodar. Supabase é o banco escolhido.

**Pergunta:** Qual é a `DATABASE_URL` do projeto Supabase do Clube USA?

**O que precisa:**
- Acesse app.supabase.com → seu projeto → Settings → Database → Connection string (Transaction mode, porta 6543)
- Copie e cole no arquivo `07-Clube-USA/backend/.env` como `DATABASE_URL=...`
- Execute `07-Clube-USA/backend/migrations/001_initial_schema.sql` no SQL Editor do Supabase

**Status:** PENDENTE

---

### [2026-07-30] Provedor de email SMTP para confirmação de cadastro

**Contexto:** O sistema de confirmação de email está implementado, mas sem credenciais SMTP, os links de confirmação só aparecem no log do servidor (modo dev). Em produção, é necessário um provedor real.

**Pergunta:** Qual provedor de email usar para envio transacional (confirmação de cadastro, etc)?

**Opções:**
- **SendGrid** (grátis até 100 emails/dia): confiável, fácil de configurar, recomendado para MVP. Prós: suporte, analytics de entrega. Contras: gera custo ao escalar.
- **Resend** (gratuito até 3.000 emails/mês): moderno, excelente DX, mais barato. Prós: SMTP compatível, preço. Contras: menor reputação que SendGrid.
- **Amazon SES**: mais barato em escala ($0,10/1k emails), mas mais complexo de configurar (verificação de domínio, reputação).

**Recomendação:** Comece com **Resend** (grátis e generoso para MVP). Migre para SES quando escalar além de 10k usuários ativos.

**O que precisa após decidir:** Preencher `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` no `.env`.

**Status:** PENDENTE

---

### [2026-07-30] Domínio e URL de produção (APP_URL)

**Contexto:** O `APP_URL` no `.env` determina o link que aparece nos emails de confirmação. Em dev é `http://localhost:8000`, mas em produção precisa ser o domínio real.

**Pergunta:** Qual é o domínio de produção do Clube USA? (ex: `https://clubeusa.com` ou subdomínio de API como `https://api.clubeusa.com`)

**O que precisa:** Preencher `APP_URL=https://seudominio.com` no `.env` de produção.

**Status:** PENDENTE

---

### [2026-07-30] Armazenamento de token JWT no frontend (segurança)

**Contexto:** O frontend atual armazena os tokens JWT em `localStorage`. Isso é simples mas vulnerável a XSS — um script malicioso na página poderia roubar o token.

**Alternativa mais segura:** Usar cookies `httpOnly` + `SameSite=Strict`. Imune a XSS, requer proteção CSRF. Mudar isso exige ajuste no backend (endpoints que setam/leem cookies) e complicação na futura API mobile.

**Pergunta:** Para o MVP com 1.000 usuários, localStorage é aceitável dado que:
- O frontend não tem conteúdo gerado por usuários (risco XSS reduzido)
- A troca para cookies pode ser feita depois sem perder usuários
- Uma app mobile futura é mais fácil com Bearer tokens

**Recomendação:** Manter localStorage por enquanto + adicionar Content-Security-Policy no servidor para mitigar XSS. Reavaliar antes de Fase 2 (quando haverá conteúdo de terceiros no site).

**Status:** PENDENTE — precisa de OK do dono para prosseguir com localStorage no MVP.

---

*Atualizado em: 2026-07-31*
