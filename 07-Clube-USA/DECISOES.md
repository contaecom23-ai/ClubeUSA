# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-08-07] Credenciais do Supabase para conectar o backend

**Contexto:** O backend da Fase 0.1 está pronto. Ele lê `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` do ambiente (`.env`). Sem esses valores, o servidor não conecta ao banco.

**Pergunta:** Você tem um projeto Supabase criado? Se sim, pode compartilhar as credenciais no arquivo `.env` (nunca no git)?

**O que fazer:**
1. Acesse [supabase.com](https://supabase.com) → seu projeto → Settings > API
2. Copie **Project URL** → `SUPABASE_URL`
3. Copie **service_role key** (não a anon key!) → `SUPABASE_SERVICE_KEY`
4. Rode o SQL de `07-Clube-USA/db/001_schema_inicial.sql` no SQL Editor do Supabase
5. Crie `.env` copiando `.env.example` e preenchendo os valores

**Status:** PENDENTE

---

### [2026-08-07] Serviço de email para confirmação de cadastro

**Contexto:** O backend envia email de confirmação via SMTP. Em modo dev (`EMAIL_ENABLED=false`), loga o link no console — funciona para testar. Para produção, precisa de credenciais reais.

**Pergunta:** Qual serviço de email quer usar?

**Opções:**
- **Opção A — SendGrid** (recomendada): 100 emails/dia grátis; configure `SMTP_HOST=smtp.sendgrid.net`, `SMTP_USER=apikey`, `SMTP_PASSWORD=SG.sua_chave`. Fácil, confiável para transacional.
- **Opção B — AWS SES**: $0.10/1000 emails; melhor custo em escala, mas exige configuração de DNS e aprovação de sandbox.
- **Opção C — Gmail SMTP**: grátis até certo ponto; não recomendado para produção (limite baixo, deliverability ruim).

**Recomendação:** Opção A (SendGrid) para o lançamento inicial. Troca para SES quando passar de 5.000 emails/mês.

**Status:** PENDENTE

---

### [2026-08-07] Domínio e URL de produção

**Contexto:** O link de confirmação de email aponta para `FRONTEND_URL` (padrão: `http://localhost:8080`). Em produção, precisa ser o domínio real.

**Pergunta:** Qual será o domínio do Clube USA? (ex: `clubeusa.com`, `app.clubeusa.com`)

**O que fazer após definir:**
- Configurar `FRONTEND_URL=https://seudominio.com` no `.env` de produção
- Configurar `ALLOWED_ORIGINS=https://seudominio.com` para o CORS

**Status:** PENDENTE

---

### [2026-08-07] Rate limiting em memória vs Redis

**Contexto:** O rate limiting atual (5 req/min no registro, 10 req/min no login) é in-memory (por instância do servidor). Para 1.000 usuários com uma instância, funciona perfeitamente. Se escalar para múltiplas instâncias (Kubernetes, etc.), o rate limit deixa de ser exato — cada instância tem seu próprio contador.

**Pergunta:** Para o lançamento, uma instância é suficiente?

**Opções:**
- **Opção A — In-memory (atual):** simples, zero custo. Funciona até ~50k req/min (estimativa conservadora). OK para 1k–10k usuários.
- **Opção B — Redis:** correto para multi-instância; custo extra (~$15/mês Upstash). Necessário se escalar para mais de 1 instância.

**Recomendação:** Opção A agora. Trocar para Redis quando precisar de múltiplas instâncias (provavelmente nunca antes de 50k usuários).

**Status:** PENDENTE (informativo — nenhuma ação necessária agora)

---

*Atualizado em: 2026-08-07*
