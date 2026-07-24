# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 BLOQUEIO CRÍTICO — AÇÃO NECESSÁRIA DO DONO (2026-07-24)

**Contexto:**
O builder automatizado está rodando 3x/dia desde ~2026-07-12. Em **cada** rodada, ele vê o `main` vazio de código (só tem ROADMAP.md e DECISOES.md), recomeça do zero, e abre **mais um PR** para a Fase 0.1.

Resultado: **31 PRs abertos, 0 mergeados, 30+ branches acumuladas.** O loop se perpetua indefinidamente enquanto nenhum PR for mergeado em `main`.

**O código está PRONTO.** O PR mais recente (PR #31) foi avaliado nesta sessão: FastAPI completo, 21 testes passando, schema PostgreSQL com triggers e índices, frontend HTML, segurança correta (anti-enumeração, rate-limit, JWT, bcrypt, CORS restrito). Está apto para produção assim que você configurar as credenciais de infra.

**O que você precisa fazer agora (em ordem):**

1. **Mergear o PR #31** → `feat/fase-0-1-cadastro-perfil-email`
   - É o mais recente (2026-07-23) e o mais bem avaliado tecnicamente
   - Contém: register, confirm-email, login, perfil, 21 testes, migration SQL
   - URL: https://github.com/contaecom23-ai/ClubeUSA/pull/31

2. **Fechar os outros 30 PRs** como duplicatas (PR #22 ao #30)
   - Todos implementam a mesma Fase 0.1 com variações menores
   - Mantê-los abertos só polui o histórico

3. **Configurar as credenciais de infra** (ver decisões abaixo) para que o código possa rodar

Depois disso o builder continua automaticamente pelas fases seguintes (0.2, 0.3, ...).

---

## Decisões Pendentes

### [2026-07-24] Provedor de email transacional

**Contexto:** O backend tem um `email_service.py` plugável via variável de ambiente `EMAIL_BACKEND`. Suporta `console` (dev) e precisa de configuração para `resend` ou `sendgrid` em produção. Sem isso, os emails de confirmação de cadastro não saem.

**Pergunta:** Qual provedor de email usar em produção?

**Opções:**
- **Resend** (recomendado): free tier 3.000 emails/mês, API simples, setup em 10 min. Suficiente para os primeiros 1.000 usuários sem custo.
- **SendGrid**: free tier 100 emails/dia (~3.000/mês). Mais estabelecido, docs extensas, DKIM/SPF mais documentado.
- **AWS SES**: ~$0,10/1.000 emails. Mais barato em escala, mas requer conta AWS e processo de saída do sandbox (pode levar dias).

**Recomendação:** Resend. Setup mais simples, tier gratuito adequado para MVP, API key em 5 minutos.

**Ação:** Criar conta em resend.com → gerar API key → adicionar como variável de ambiente `RESEND_API_KEY` na plataforma de deploy.

**Status:** PENDENTE

---

### [2026-07-24] Credenciais Supabase (DATABASE_URL)

**Contexto:** O backend usa asyncpg com `DATABASE_URL` para conectar ao PostgreSQL. Sem isso, nenhuma rota de dados funciona.

**Pergunta:** Você já tem um projeto Supabase criado? Se sim, qual é a connection string?

**Ação necessária:**
1. Acessar https://supabase.com → criar projeto (ou usar existente)
2. Ir em Settings → Database → Connection String → copiar a string com senha
3. Rodar o arquivo `07-Clube-USA/migrations/001_initial_schema.sql` no SQL Editor do Supabase
4. Adicionar `DATABASE_URL=postgresql://...` como variável de ambiente no deploy

**Status:** PENDENTE

---

### [2026-07-24] Plataforma de deploy

**Contexto:** O código está pronto mas não tem onde rodar. Precisa de uma plataforma que sirva o FastAPI backend e os arquivos HTML do frontend.

**Pergunta:** Onde hospedar o MVP?

**Opções:**
- **Railway** (recomendado): ~$5/mês, deploy em 5 min a partir do repo GitHub, zero cold start, variáveis de ambiente pelo painel. Melhor custo-benefício para MVP.
- **Render (free tier)**: grátis, mas dorme após 15 min de inatividade — causa delay de ~30s no primeiro request, má experiência para cadastro.
- **Fly.io**: gratuito com limites generosos, mas configuração via CLI mais complexa.
- **VPS (DigitalOcean/Vultr $6/mês)**: mais controle, mas requer setup manual de nginx, SSL, systemd — não vale a complexidade no MVP.

**Recomendação:** Railway. Custo de $5/mês é irrelevante vs tempo de setup. Zero config, deploy automático do GitHub, variáveis de ambiente seguras.

**Status:** PENDENTE

---

### [2026-07-24] Domínio / URL de produção

**Contexto:** Os emails de confirmação precisam de uma URL base configurável (`BASE_URL` no .env). Também afeta CORS e a configuração do HTTPS.

**Pergunta:** Já tem um domínio? (ex: clubeusa.com, clube.us, clubeusa.app)

**Opções:**
- Se já tem domínio: apontar DNS para a plataforma de deploy escolhida.
- Se não tem: registrar em Namecheap (~$12/ano para .com) ou Cloudflare Registrar (preço de custo).

**Recomendação:** Se não tem, registre `clubeusa.com` ou `clube.us`. O domínio aparece nos links de referral (Fase 0.2) e nos emails — vale a pena ter algo profissional desde o início.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-24*
