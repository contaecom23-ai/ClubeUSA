# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-07-22] Provedor de email transacional (confirmação de conta)

**Contexto:**
A Fase 0.1 (cadastro + email confirmado) está implementada. O backend envia o email de confirmação via SMTP configurável. Em modo dev (sem SMTP_HOST), os emails são logados no console — perfeito para testes locais. Para produção, um serviço SMTP externo é necessário.

**Pergunta:**
Qual provedor de email transacional usar para o envio de confirmação de conta?

**Opções:**

- **Opção A — SendGrid (Twilio)**
  - Prós: free tier generoso (100 emails/dia), API HTTP simples, boa entregabilidade, dashboard com métricas, SDK Python disponível
  - Contras: conta gratuita pode ser suspensa se taxa de rejeição for alta; pricing aumenta rápido no volume
  - Config: `SMTP_HOST=smtp.sendgrid.net`, `SMTP_PORT=587`, `SMTP_USER=apikey`, `SMTP_PASSWORD=SG.xxxxx`

- **Opção B — AWS SES**
  - Prós: muito barato em volume ($0.10 por 1000 emails), escala bem, já integra com outros serviços AWS
  - Contras: setup mais complexo (verificar domínio, sair do sandbox requer aprovação AWS), requer conta AWS
  - Config: similar ao SendGrid com credenciais IAM

- **Opção C — Resend (resend.com)**
  - Prós: API moderna e simples, free tier de 100 emails/dia, boa entregabilidade, dashboard limpo
  - Contras: empresa mais nova, menos track record

- **Opção D — Supabase Auth (nativo)**
  - Prós: zero configuração, já incluso no plano Supabase
  - Contras: exigiria migrar autenticação para o Supabase Auth nativo (abandonar nosso JWT customizado), perdendo controle sobre o fluxo; não recomendado por criar lock-in e limitar customização futura

**Recomendação:**
SendGrid (Opção A) para começar — plano gratuito cobre os primeiros 1.000 usuários com folga, setup é 10 minutos, e a migração para AWS SES é simples se crescer. Evite Supabase Auth nativo para manter controle sobre o fluxo de autenticação.

**Ação necessária:**
1. Criar conta em sendgrid.com
2. Verificar domínio de envio (ex: noreply@clubeusa.com)
3. Gerar API key
4. Adicionar `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` nas variáveis de ambiente do servidor

**Status:** PENDENTE

---

### [2026-07-22] Domínio e URL de produção do frontend

**Contexto:**
O backend (`FRONTEND_URL`) e os emails de confirmação precisam apontar para a URL real do frontend para que os links de confirmação funcionem em produção.

**Pergunta:**
Qual é a URL de produção do frontend e do backend?

**Opções:**
- `clubeusa.com` (frontend) + `api.clubeusa.com` (backend)
- Subdomínio: `app.clubeusa.com` (frontend) + `api.clubeusa.com` (backend)
- Vercel/Netlify para frontend + Railway/Fly.io para backend

**Recomendação:**
`clubeusa.com` para o frontend (mais limpo para usuários) e `api.clubeusa.com` para a API. Para hospedagem inicial (1k usuários): Vercel para frontend (gratuito), Railway ou Render para o backend FastAPI (~$5-7/mês).

**Ação necessária:**
Confirmar domínio e atualizar `FRONTEND_URL` e `ALLOWED_ORIGINS` nas env vars de produção.

**Status:** PENDENTE

---

### [2026-07-22] Aplicar migration 001 no Supabase

**Contexto:**
O arquivo `07-Clube-USA/backend/migrations/001_initial_schema.sql` cria as tabelas `users`, `profiles` e `refresh_tokens`. Precisa ser aplicado manualmente no Supabase (SQL Editor com credenciais de admin).

**Pergunta:**
Confirmar execução da migration no projeto Supabase de produção/staging.

**Ação necessária:**
1. Acessar Supabase Dashboard → SQL Editor
2. Colar e executar o conteúdo de `migrations/001_initial_schema.sql`
3. Confirmar que as tabelas foram criadas sem erro

**Status:** PENDENTE

---

*Atualizado em: 2026-07-22*
