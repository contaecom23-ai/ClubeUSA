# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-07-10] D-001: Serviço de email transacional

**Contexto:** A Fase 0.1 (cadastro + confirmação de email) está construída e pronta para deploy. Para os emails funcionarem, você precisa escolher um serviço de email transacional e fornecer as credenciais SMTP no `.env`. Sem isso, os emails são apenas logados no console (modo dev, não funciona em produção).

**Pergunta:** Qual serviço de email usar para os emails transacionais (confirmação de conta, boas-vindas)?

**Opções:**

- **Opção A — Resend.com** (recomendado)
  - Prós: API moderna, excelente deliverability, $0 até 100 emails/dia / $20/mês para 50k; integração SMTP simples; dashboard bonito; domínio verificado com 1 clique
  - Contras: serviço novo (fundado 2022), menos market share que SendGrid
  - Como usar: criar conta em resend.com → verificar domínio → gerar API key → usar SMTP relay

- **Opção B — SendGrid (Twilio)**
  - Prós: mercado consolidado, free tier 100/dia, muito documentado
  - Contras: interface complexa, pricing sobe rapidamente, suporte fraco no free
  - Como usar: criar conta → verificar sender → gerar API key → SMTP_USER=apikey, SMTP_PASSWORD=<sua_api_key>

- **Opção C — Mailgun**
  - Prós: robusto, bom deliverability, free trial 3 meses
  - Contras: sem free tier permanente, UI mais técnica

- **Opção D — SMTP próprio (Gmail/Outlook)**
  - Prós: gratuito, sem cadastro extra
  - Contras: deliverability ruim em produção, limite de envio baixo, não recomendado para produção

**Recomendação:** Opção A (Resend). Melhor experiência de desenvolvedor, pricing justo para o volume inicial, deliverability excelente. Para os primeiros 1.000 usuários, o plano gratuito basta.

**Ação necessária:** Criar conta no Resend → verificar o domínio clubeusa.com → fornecer ao Claude: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM para adicionar ao `.env`.

**Status:** PENDENTE

---

### [2026-07-10] D-002: Projeto Supabase + credenciais

**Contexto:** O backend usa Supabase como banco de dados PostgreSQL. Para fazer o deploy, precisamos das credenciais do projeto Supabase. A migração SQL está em `07-Clube-USA/api/migrations/001_users.sql`.

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA?

**Opções:**

- **Opção A — Criar projeto novo no Supabase**
  - Acesse app.supabase.com → New Project
  - Escolha região US East (mais próximo da maioria dos imigrantes brasileiros)
  - Plano Free funciona para os primeiros 1.000 usuários (500MB banco, 50MB storage)
  - Prós: gratuito até ~500 usuários ativos, fácil setup
  - Contras: limite de conexões no free (sem pooler)

- **Opção B — Já tem projeto existente**
  - Fornecer as credenciais diretamente

**Ação necessária (qualquer opção):** Fornecer ao Claude:
1. `SUPABASE_URL` (ex: `https://xyzxyz.supabase.co`)
2. `SUPABASE_SERVICE_KEY` (chave "service_role" em Settings > API — NÃO a anon key)
3. Executar a migração `001_users.sql` no SQL Editor do Supabase

**Status:** PENDENTE

---

### [2026-07-10] D-003: Domínio e hospedagem do frontend + API

**Contexto:** O frontend (HTML estático) e a API FastAPI precisam de hosting para funcionar em produção. A variável `FRONTEND_URL` no `.env` determina os links nos emails de confirmação.

**Pergunta:** Onde hospedar o frontend e a API?

**Opções para o frontend (HTML estático):**
- **Vercel / Netlify** (recomendado): gratuito, deploy automático por git push, CDN global
- **Cloudflare Pages**: gratuito, rápido, mas sem forms nativo
- **AWS S3 + CloudFront**: mais controle, pequeno custo

**Opções para a API FastAPI:**
- **Railway.app** (recomendado): $5/mês base, deploy simples via Docker/git, bom para começo
- **Render.com**: free tier mas dorme após inatividade (ruim para produção)
- **Fly.io**: free tier generoso, mas mais complexo
- **AWS/GCP/Azure**: overkill para 1.000 usuários iniciais, custo variável

**Recomendação:** Frontend na Vercel (grátis) + API no Railway ($5/mês). Total: $5/mês para os primeiros 1.000 usuários. Escala sem refatoração até 10k+ usuários.

**Ação necessária:** Confirmar o domínio (`clubeusa.com` ou outro?) e a escolha de hosting para que o Claude possa configurar as variáveis de ambiente e, se necessário, os arquivos de deploy (Dockerfile, railway.toml, vercel.json).

**Status:** PENDENTE

---

*Atualizado em: 2026-07-10*
