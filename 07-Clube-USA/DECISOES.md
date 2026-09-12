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

## ⚠️ SITUAÇÃO — 91 PRs ABERTOS SEM MERGE

### [2026-09-12] D-003: 91 PRs acumulados — workflow quebrado

**Contexto:** Existem 91 PRs abertos no repositório, nenhum foi mergeado. O Claude cria PRs a cada rodada (3x/dia) mas o dono não revisa. Resultado: PRs conflitantes, histórico confuso, e sessões repetindo trabalho já feito.

**Problema real:** O app completo já foi commitado diretamente na `main` (commit de 2026-08-16). As Fases 0.1, 0.2, 0.3, 1.1 e 1.6 já estão implementadas em `main`. Os 91 PRs são em sua maioria tentativas de coisas já existentes ou docs/status reports.

**Pergunta:** Como você quer gerenciar os PRs daqui pra frente?

**Opções:**
- **A:** Fechar todos os 91 PRs (bulk close via GitHub). Manter apenas o PR mais recente com código novo. Nenhum trabalho útil se perde — tudo relevante já está em `main` ou neste PR atual.
- **B:** Revisar 1 por 1 (trabalho manual seu — não recomendo, são 91 PRs).
- **C (recomendado):** Fechar em bulk os PRs com branches `docs/`, `fix/decisoes`, `feat/consolida`, `docs/estado` etc (são só status reports). Avaliar apenas os PRs com código real: `feat/fase-1.2-zip-search` (#65), `feat/fase-2.1-business-subscriptions` (#68), `test/auth-member-security` (#63), `fix/relogin-vip-plan-token` (#78).

**Recomendação:** Opção C. Os 4 PRs com código real valem revisão rápida. O resto pode ser fechado sem perda.

**Status:** PENDENTE

---

## Decisões Aprovadas

*(nenhuma ainda)*

---

*Atualizado em: 2026-09-12*
