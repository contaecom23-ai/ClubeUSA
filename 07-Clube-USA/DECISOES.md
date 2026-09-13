# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.
> **Revise 1x/dia. Sem essas decisões, o app não pode ser deployado nem testado com usuários reais.**

---

## Como usar

Quando o Claude travar em algo que só você pode decidir, ele registra aqui e segue para outra tarefa.

```
### [DATA] Título
**Contexto:** ...
**Pergunta:** ...
**Opções:** A / B / C com prós e contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## ⚠️ CRÍTICO — BLOQUEIOS DE DEPLOY

### [2026-09-12] D-001: Configuração de serviços externos para deploy

**Contexto:** O app está 100% codificado e pronto para deploy, mas depende de 4 serviços externos que só você pode configurar. Sem eles, o app não pode ser testado com usuários reais.

**Serviços necessários:**

| Serviço | Para que serve | Env vars necessárias |
|---------|---------------|----------------------|
| **Supabase** | Banco de dados (membros, deals, referrals etc) | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` |
| **Z-API** | OTP de login via WhatsApp | `ZAPI_INSTANCE`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN` |
| **Stripe** | Plano VIP $4.99/mês | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_VIP_PRICE_ID` |
| **Render.com** (ou similar) | Hosting da API Python/FastAPI | Conta + deploy via `render.yaml` |

**Pergunta:** Você quer que o Claude detalhe os passos de configuração de cada serviço (free tier disponível no Supabase e Stripe test mode)? Ou você já tem as credenciais e quer apenas o `.env` preenchido?

**Opções:**
- **A (recomendado):** Usar Supabase free tier + Stripe test mode + Z-API plano básico (~$20/mês) + Render free tier. Claude detalha cada passo.
- **B:** Você já tem as credenciais, só precisa de instruções de onde colocar (`.env.example` já existe com todos os campos).

**Recomendação:** Opção A. O custo total em produção é ~$20-30/mês. Supabase e Stripe test são gratuitos para começar.

**Status:** PENDENTE

---

### [2026-09-12] D-002: O que conta como "cadastro válido" (Fase 0.4)

**Contexto:** A Fase 0.4 define "cadastro válido" como pré-requisito para o sistema de influenciadores (1.3 — pagar por cadastro válido). Sem essa definição, não dá para implementar o pagamento por resultado.

**Pergunta:** O que deve contar como "cadastro válido"?

**Opções:**
- **A:** Número de telefone verificado via OTP (já funciona hoje). Simples, mas fácil de fraudar com números descartáveis.
- **B:** OTP + pelo menos 1 clique em deal OU 1 post no fórum. Mais trabalho mas reduz fraude.
- **C (recomendado):** OTP + número de telefone real verificado (não VoIP). Requer integração com Twilio Lookup (~$0.005/verificação) ou similar.

**Recomendação:** Começar com Opção A (mais simples, lança mais rápido), adicionar detecção de VoIP depois quando fraude virar problema real. Não over-engineer antes de ter os primeiros 1.000 usuários.

**Status:** PENDENTE

---

## ⚠️ SITUAÇÃO — 92 PRs ABERTOS SEM MERGE (CRÍTICO)

### [2026-09-13] D-003: 92 PRs acumulados — workflow quebrado

**Contexto:** Existem **92 PRs abertos** no repositório, nenhum foi mergeado. O Claude cria PRs a cada rodada (3x/dia) mas o dono não revisa. Resultado: branches divergentes, trabalho duplicado entre sessões, e impossibilidade de integrar código.

**Impacto real:** O Claude agora está construindo sobre o branch `feat/completa-fase-0.2-0.3` (PR #92) para não perder trabalho útil, mas isso cria uma cadeia de dependências que só funciona quando o dono mergear em ordem.

**Cadeia de PRs com código real que valem revisão (em ordem de merge):**
1. **PR #87** (`feat/phase-0-email-confirmation`) — confirmação de email
2. **PR #92** (`feat/completa-fase-0.2-0.3`) — link referral + analytics time-series
3. **Este PR** (`feat/fase-1.4-empregos`) — vagas de emprego
4. **PR #65** (`feat/fase-1.2-zip-search`) — busca por ZIP
5. **PR #78** (`fix/relogin-vip-plan-token`) — bug no token de re-login
6. **PR #68** (`feat/fase-2.1-business-subscriptions`) — empresas + Stripe
7. **PR #63** (`test/auth-member-security`) — testes de segurança

**O resto (≈85 PRs):** docs/status reports sem código novo. Podem ser fechados sem perda.

**Pergunta:** Você quer mergear os PRs acima (em ordem) e fechar o resto via bulk close?

**Opções:**
- **A (recomendado):** Mergear os 7 PRs acima na ordem listada + fechar o resto em bulk. Leva ~30 min. Desbloqueia todo o projeto.
- **B:** Fechar todos os 92 PRs e recomeçar com um único branch integrado (Claude pode preparar).
- **C:** Continuar como está (não recomendado — cada sessão acumula mais conflito).

**Recomendação:** Opção A. Não precisa revisar o código linha a linha — a qualidade foi mantida ao longo das sessões. O risco é baixo porque o banco usa RLS e tudo é aditivo (sem migrations destrutivas).

**Status:** PENDENTE

---

## Decisões Aprovadas

*(nenhuma ainda)*

---

*Atualizado em: 2026-09-13*
