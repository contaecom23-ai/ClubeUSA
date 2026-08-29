# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, arquitetura, gasto, chaves externas, direção estratégica, irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ AÇÃO IMEDIATA — 31 PRs abertos, nenhum mergeado (2026-08-29)

**O que aconteceu:** o agente trabalhou por semanas. O main tem código sólido, mas as features novas ficaram presas em branches. Sem merge, não há progresso real.

**O que existe de bom no main hoje:**
- Auth via WhatsApp OTP (cadastro, login, OTP com TTL, audit log)
- Referral (código único, captura `?ref=`, stats, leaderboard)
- Deals API (curadoria admin → envio WhatsApp → membro vê deals)
- Stripe VIP $4,99/mês (checkout, webhook HMAC, portal de cancelamento)
- Price tracker (Amazon/Walmart/BestBuy, alertas, cupons Playwright)
- Forum, News, AI Assistant (routers separados)
- Admin panel (métricas, membros, deals, alertas)
- Segurança: rate-limit, security headers, CORS restrito, HMAC Stripe

**Plano de merge recomendado — faça isso agora:**

### PASSO 1 — Feche estes PRs (obsoletos ou conflitantes, não mergear):

| PR | Motivo |
|----|--------|
| #46 | Email auth — conflita com WhatsApp OTP do main (ver D-001) |
| #51 | CI YAML inválido — supercedido por #56 |
| #52, #57, #70, #71 | Referral redirect individual — todos supercedidos por #62 |
| #54, #55, #61 | Features individuais — todas supercedidas por #62 |
| #53, #59, #60, #64, #66, #69, #72, #73 | Status docs — informativo, já cumprido |

### PASSO 2 — Mergear nesta ordem:

| Ordem | PR | O que entrega |
|-------|----|---------------|
| 1° | **#62** | `/i/{code}` redirect (0.2) + analytics `/admin/analytics` (0.3) + webhook Z-API seguro + audit login |
| 2° | **#56** | CI pytest automático nos PRs |
| 3° | **#63** | Testes auth + isolamento de segurança |
| 4° | **#58** | Fase 0.4: cadastro válido + anti-fraude (email descartável) |
| 5° | **#65** | Fase 1.2: busca por ZIP + raio geográfico (17 testes) |
| 6° | **#16** | Fase 1.3: programa de influenciadores pago por resultado |
| 7° | **#68** | Fase 2.1: assinatura de empresas $10–30/mês |

> **Nota:** PRs #14, #19, #20 (1.2, 1.4, 1.5) podem ter conflitos com #65 — verificar depois que #65 for mergeado.

---

## Decisões Pendentes

### D-001 [CRÍTICO — DECISÃO DE PRODUTO] Auth: WhatsApp OTP vs Email
**Data:** 2026-08-29
**Contexto:** O main usa WhatsApp OTP como único método de autenticação (sem senha, sem email). PR #46 implementa cadastro com email + confirmação via email — arquitetura incompatível; não podem coexistir sem refactor significativo.

**Pergunta:** Qual é o método de auth canônico do Clube USA?

**Opções:**
- **A — WhatsApp OTP (já no main) ← RECOMENDADO:** Mais simples para o público-alvo (brasileiro nos EUA, 99% tem WhatsApp). Sem gestão de senha. OTP via WhatsApp confirma número real e filtra bots. Sem custo de email provider. Ponto fraco: usuário sem WhatsApp (raro no público).
- **B — Email com confirmação:** Familiar para usuários de outras plataformas. Permite email marketing nativo. Ponto fraco: bounces, spam, custo de email provider (SendGrid ~$15/mês), gestão de senha.
- **C — Ambos:** Alta complexidade, dois flows de auth, dois sistemas de verificação, mais superfície de ataque. Não recomendado nesta fase.

**Recomendação:** **Opção A.** WhatsApp OTP já funciona. Fechar PR #46. Adicionar email como campo opcional de perfil depois (sem tornar auth).

**Status:** PENDENTE

---

### D-002 [BLOQUEADOR DE RECEITA] Deploy em produção
**Data:** 2026-08-29
**Contexto:** O código está pronto para rodar. Não está claro se o app está deployado ou não. Sem deploy, zero usuários, zero receita.

**Pergunta:** O app está no ar? Se não, o que está impedindo?

**O que precisa para ir ao ar (Render.com — `render.yaml` já no repo):**
1. Conta Render.com criada e conectada ao repo
2. Variáveis de ambiente configuradas no Render: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SECRET_KEY` (gerar: `python -c "import secrets; print(secrets.token_urlsafe(32))"`), `ADMIN_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_VIP_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`, `ZAPI_INSTANCE`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN`, `APP_URL`, `ENVIRONMENT=production`
3. Schema SQL rodado no Supabase SQL Editor: `db/schema.sql` + `db/otp_migration.sql`
4. Stripe webhook apontando para `https://[url-render]/billing/webhook`

**Recomendação:** Deploy agora no Render free tier. O app base funciona mesmo sem Stripe/Z-API configurados (falha graciosamente). Depois de deployed: testar fluxo de cadastro → OTP → perfil → deals.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-29*
