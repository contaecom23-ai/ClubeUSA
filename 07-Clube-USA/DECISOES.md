# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ✅ Verificação 2026-07-11 — build rodou, testes passando, fix aplicado

**Run automático em 2026-07-11.** Verificações feitas:
- 25 testes passando (21 originais + 4 novos para o mecanismo de refresh de token)
- Fix aplicado: mecanismo de refresh token estava faltando (regra obrigatória: "tokens com TTL curto + refresh"). Adicionado `/auth/refresh` com segregação por claim `type`. Access token agora 1 dia; refresh token 7 dias.
- Código de qualidade de produção confirmado: segurança, IDOR, rate-limit, XSS, RLS, bcrypt rounds=12 — tudo OK.
- **Nenhuma nova tarefa desbloqueada.** Tudo ainda aguarda merge do PR #17 e credenciais de infra (D-001, D-002, D-003).

---

## ⚠️ ATENÇÃO IMEDIATA — Acúmulo de PRs (D-004)

### [2026-07-10] D-004: 17 PRs abertos sem revisão — ação necessária HOJE

**Contexto:** O builder autônomo rodou ~10 vezes nos últimos dias. Como o ROADMAP no `main` ainda mostra tudo como `[ ]`, cada rodada concluiu que precisava reimplementar tudo do zero. Resultado: 17 PRs acumulados, nenhum merged. Código de qualidade existe, mas está parado.

**Situação técnica atual (verificada em 2026-07-10):**
- Branch `feature/fase-0-1-cadastro` (PR #17): **21 testes passando**, código de produção pronto para Fase 0.1
- Código auditado: segurança OK (bcrypt rounds=12, JWT 7d, rate-limit, IDOR impossível, XSS bloqueado, RLS habilitado)
- PRs para outras fases existem mas NÃO foram auditados nesta rodada

**O que acontece se você não agir:** O builder continua criando PRs duplicados a cada rodada. A cada 8h, mais um PR de Fase 0.1 aparece. O repositório vira um cemitério de branches.

**Plano de ação (60 minutos da sua parte):**

**Passo 1 — Mergear este PR primeiro (PR #17):**
1. Abra https://github.com/contaecom23-ai/ClubeUSA/pull/17
2. Revise o diff (32 arquivos, backend + frontend + testes)
3. Marque como "Ready for review" → Merge

**Passo 2 — Fechar PRs duplicados de Fase 0.1 (7 PRs):**
Feche com comentário "Substituído pelo PR #17" os PRs: #1, #6, #7, #11, #13, #15 (e possivelmente #2)

**Passo 3 — Decidir sobre PRs de fases ainda não implantadas:**

| PR | Fase | Recomendação |
|----|------|-------------|
| #3 | 0.2 Referral | Manter aberto — revisar depois de 0.1 em produção |
| #4 | 0.3 Analytics | Manter aberto — revisar depois de 0.1 em produção |
| #5 | 0.4 Anti-fraude | Manter aberto — revisar depois de 0.1 em produção |
| #9 | Security polish | Manter — melhoras de segurança válidas |
| #10 | Fix workflow YAML | Manter — conserta o YAML do CI (importante) |
| #12 | 1.1 Promoções | ⚠️ Não mergear ainda — Fase 0 deve estar em prod primeiro |
| #14 | 1.2 Busca ZIP | ⚠️ Não mergear ainda — depende de 0.1 deployado |
| #16 | 1.3 Influenciadores | ⚠️ Não mergear ainda — envolve orçamento (ver D-007) |

**Passo 4 — Fornecer credenciais para que o código vá a produção:**
Veja D-001 (email), D-002 (Supabase), D-003 (hosting) abaixo.

**Raiz do problema:** O YAML do workflow GitHub Actions (`.github/workflows/clubeusa-builder.yml`) está malformado e nunca rodou automaticamente. O PR #10 corrige isso. Mergear o PR #10 após o #17 vai normalizar o ciclo automático.

**Status:** PENDENTE — decisão exclusiva do dono

---

## Decisões de Infraestrutura

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

## Decisões de Produto / Negócio

---

### [2026-07-09] D-007: Orçamento para programa de influenciadores (Fase 1.3)

**Contexto:** O PR #16 implementou o sistema técnico de rastreamento de influenciadores (pagamento por cadastro válido). Mas o sistema só pode ser ativado quando você definir:

**Perguntas:**
1. Quanto pagar por cadastro válido? (sugestão: $0,50–$2,00 por cadastro)
2. Qual o teto mensal de budget para influenciadores?
3. Os selos (Parceiro 50 / Embaixador 250 / Hall da Fama 1.000) têm bônus em dinheiro ou só reconhecimento?

**Recomendação:** Comece com $1,00/cadastro válido com teto de $500/mês. Teste por 30 dias e ajuste. Não ative antes de ter Fase 0 em produção (base técnica necessária).

**Status:** PENDENTE — não ativar antes de Fase 0 deployada

---

### [2026-07-09] D-008: Curadoria de Promoções/Achados (Fase 1.1)

**Contexto:** O PR #12 implementou o CRUD de promoções. Mas o produto precisa de decisão sobre:

**Perguntas:**
1. Quem valida as promoções antes de publicar? (auto-publish ou revisão manual?)
2. Quais categorias iniciais? (supermercados, restaurantes, serviços, roupas?)
3. Como seed inicial — você vai alimentar manualmente as primeiras 20–30 promoções?

**Recomendação:** Início com revisão manual (você aprova cada promoção). Automatize depois que tiver volume e confiança na qualidade. Categorias iniciais: Supermercado, Restaurante, Serviços, Vestuário.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-10*
