# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.
> Formato: DATA, contexto, pergunta, opções com prós/contras, recomendação, status.

---

## CRÍTICO — D-004: Paralisia de Merge (31 PRs abertos sem merge)
**Data:** 2026-09-21
**Contexto:** O agente criou código de qualidade para os itens 0.1 a 2.1 do roadmap, distribuído em 31 PRs abertos entre agosto e setembro de 2026. Nenhum PR foi revisado ou merged até hoje. Isso significa:
- Nenhuma feature nova está em produção
- Os branches estão divergindo cada vez mais entre si (futuros merge conflicts)
- O agente continua criando PRs duplicados das mesmas features
- O projeto existe só no papel, não para os usuários

**Pergunta:** Qual é o plano de ação para mergear (ou fechar) esses PRs?

**Opções:**
- **A (recomendada)**: Mergear os PRs na ordem do roadmap (0.1 → 0.2 → 0.3 → 0.4 → 1.1...). Para cada grupo de PRs duplicados, escolher o mais recente. Isso levaria ~2 horas de revisão.
- **B**: Fechar todos os PRs antigos e usar apenas os mais recentes de cada fase. Mais limpo, menos confusão.
- **C**: Fazer uma única branch consolidada que une tudo. Mais trabalho, mas resulta num único PR grande para revisar.
- **D**: Continuar como está. **Não recomendado** — o código nunca chega aos usuários.

**Recomendação do Claude:** Opção A ou B. PRs pendentes por ordem de prioridade para merge:
1. `feat/fase-0.1-email-confirm-clean` (criado 2026-09-21 — mais recente para 0.1)
2. `feat(fase-0.2): GET /i/{code}` → PR #102
3. `feat(0.3): analytics` → PR #90 ou #92 (mais recente)
4. `feat(fase-0.4): cadastro válido` → PR #104
5. `feat(1.1): deal urgency` → PR #97
6. `feat(1.3): influencer tiers` → PR #96
7. `feat(1.4): empregos` → PR #93
8. `feat(1.5): moradia` → PR #94
9. `feat(2.1): assinatura empresas` → PR #105

**Status:** PENDENTE — decisão do dono

---

## D-003: SMTP/Serviço de E-mail para Fase 0.1
**Data:** 2026-09-21
**Contexto:** A confirmação de e-mail (Fase 0.1) está implementada na API, mas precisa de um servidor SMTP real para enviar e-mails em produção. Em dev, o link é apenas logado no console.

**Pergunta:** Qual serviço de e-mail usar?

**Opções:**
- **A (recomendada)**: **Mailgun** — free tier generoso (100 e-mails/dia), simples de configurar, SMTP padrão. Custo: $0 para os primeiros 1.000 usuários.
- **B**: **SendGrid** — similar ao Mailgun, free tier de 100/dia, bom dashboard de analytics.
- **C**: **AWS SES** — mais barato em volume ($0.10/1.000 e-mails), mas requer conta AWS e processo de verificação de domínio.
- **D**: **Resend.com** — novo, excelente DX, free tier 3.000/mês. Boa opção moderna.

**Recomendação:** Mailgun ou Resend — simples, rápido de configurar, free para os primeiros 1.000 usuários. Configure `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` nas env vars da plataforma de deploy.

**Status:** PENDENTE — dono configura as env vars

---

## D-002: Deploy em Produção
**Data:** 2026-09-21
**Contexto:** O `render.yaml` está configurado, mas o app nunca foi deployed em produção (nenhuma URL pública funcional).

**Pergunta:** Quando e em qual plataforma deployar?

**Opções:**
- **A (recomendada)**: Render.com — `render.yaml` já existe no repo, é só conectar. Free tier serve os primeiros 1.000 usuários. Deploy em <5 min.
- **B**: Railway.app — similar ao Render, boa DX.
- **C**: VPS (DigitalOcean/Hetzner) — mais controle, mais barato em escala, mais trabalho de configuração.

**Recomendação:** Render.com agora — o arquivo de configuração já existe. O bloqueio real é mergear os PRs (D-004) antes de deployar.

**Status:** PENDENTE — requer merge dos PRs primeiro (D-004)

---

## D-001: Credenciais Externas Necessárias para Produção
**Data:** 2026-09-21
**Contexto:** O app depende de serviços externos que precisam de contas e chaves reais.

**Serviços necessários:**
| Serviço | Para que | Env var | Obrigatório? |
|---------|----------|---------|-------------|
| Supabase | Banco de dados | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | SIM |
| Stripe | Pagamentos VIP | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_VIP_PRICE_ID` | Para pagamentos |
| Z-API | OTP por WhatsApp | `ZAPI_INSTANCE`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN` | Para auth |
| SMTP | E-mail de confirmação | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` | Para 0.1 |

**Status:** PENDENTE — dono precisa criar/configurar as contas e env vars

---

*Atualizado em: 2026-09-21*
