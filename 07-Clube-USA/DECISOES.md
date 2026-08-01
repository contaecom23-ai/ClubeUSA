# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-08-01] Provedor de email para envio de confirmação de conta

**Contexto:** A Fase 0.1 está pronta: registro, confirmação de email e login funcionam. O backend já tem o código para envio via SMTP, mas precisa de um provedor configurado. Em modo dev (sem SMTP configurado), o link de confirmação é logado no console — OK para testes, mas não para produção.

**Pergunta:** Qual provedor de email usar para envio transacional (confirmação de conta, recuperação de senha)?

**Opções:**

- **A. SendGrid (gratuito até 100 emails/dia):**
  - Prós: tier gratuito suficiente para os primeiros 1k usuários; integração simples via SMTP; boa entregabilidade; dashboard com métricas
  - Contras: depende de conta externa; precisa de domínio verificado para melhor entregabilidade
  - Custo: $0 até 100 emails/dia; $19.95/mês para 40k/mês depois

- **B. AWS SES (mais barato em escala):**
  - Prós: $0.10/1000 emails (praticamente grátis em toda escala); confiável
  - Contras: configuração mais complexa; precisa sair do sandbox para enviar para qualquer email; exige conta AWS
  - Custo: quasi-zero ($0.10/1k = $1 para 10k emails)

- **C. Resend (novo, dev-friendly):**
  - Prós: 3k emails/mês grátis; API simples; boa UX para devs
  - Contras: menos provado em escala; empresa mais nova
  - Custo: $0 até 3k/mês; $20/mês depois

- **D. Supabase Auth (abandona custom auth, usa o nativo):**
  - Prós: zero config de email; Supabase cuida de tudo
  - Contras: **não recomendado** — já implementamos auth customizado com controle total, segurança multi-tenant, refresh token rotation. Migrar agora seria retrabalho sem ganho real.

**Recomendação:** **A (SendGrid)** para começar — tier gratuito cobre os primeiros 1k usuários com folga, integração em 10 minutos via SMTP, boa entregabilidade. Quando chegar em 40k/mês, migrar para AWS SES pelo custo.

**Ação necessária do dono:**
1. Criar conta em sendgrid.com
2. Gerar API key
3. Verificar domínio remetente (ex: noreply@clubeusa.com)
4. Configurar nas env vars: `SMTP_HOST=smtp.sendgrid.net`, `SMTP_PORT=587`, `SMTP_USER=apikey`, `SMTP_PASSWORD=<sua-api-key>`, `SMTP_FROM=noreply@clubeusa.com`

**Status:** PENDENTE

---

### [2026-08-01] Infraestrutura de deploy: onde hospedar backend + frontend

**Contexto:** Backend FastAPI e frontend HTML precisam de um lugar para rodar. Ainda não há servidor configurado.

**Pergunta:** Onde hospedar para o lançamento inicial (1k usuários)?

**Opções:**

- **A. Railway.app (recomendado para iniciar rápido):**
  - Prós: deploy de FastAPI em minutos via GitHub; free tier disponível; escala automaticamente; sem ops
  - Contras: free tier tem limitações de CPU/sleep; ~$5-20/mês em produção real
  - Frontend: servir HTML via FastAPI static files ou Cloudflare Pages (gratuito)

- **B. Render.com:**
  - Similar ao Railway; free tier também com sleep; boa alternativa
  - Custo: ~$7/mês pro plano básico

- **C. VPS (DigitalOcean/Linode $6/mês):**
  - Prós: controle total; sem cold starts
  - Contras: requer ops manual (nginx, certbot, deploys); mais tempo de setup

- **D. Vercel (frontend) + Railway (backend):**
  - Frontend no Vercel (gratuito, CDN global) + backend no Railway
  - Melhor separação de concerns; recomendado quando o produto crescer

**Recomendação:** **A (Railway para backend + Cloudflare Pages para frontend)** para o lançamento. Custo ~$10/mês. Quando chegar em 10k usuários, avaliar migração para VPS ou Fly.io.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-01*
