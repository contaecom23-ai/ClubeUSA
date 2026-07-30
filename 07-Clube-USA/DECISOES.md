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

## Decisões Pendentes

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

*Atualizado em: 2026-07-30*
