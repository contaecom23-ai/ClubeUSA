# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## ⚠️ SITUAÇÃO CRÍTICA — 2026-09-12

**90+ PRs abertas sem merge.** O projeto está bloqueado operacionalmente.
Código bom foi escrito mas nunca chegou à `main`. Criar mais PRs não ajuda.

**Ação necessária AGORA (estimativa: 15 minutos):**

Acesse https://github.com/contaecom23-ai/ClubeUSA/pulls e execute:

### PRs a FECHAR (obsoletas/duplicadas/docs) — feche todas exceto as 5 abaixo

A maioria dos PRs com título "docs/estado*", "docs/decisoes*", "docs/plano*", "docs/status*"
são atualizações de status que perderam a validade. Feche-as com a mensagem:
"Fechando — informação obsoleta após triage 2026-09-12."

### 5 PRs CANDIDATAS A MERGE (em ordem):

| Prioridade | PR | O que faz | Risco |
|---|---|---|---|
| 1 | **#88** | fix: JWT TTL 24h→7d + DECISOES preenchido | Baixo — só muda TTL do token |
| 2 | **#62** | feat: consolida 0.2 + 0.3 + segurança webhook | Médio — revise conflitos com main |
| 3 | **#65** | feat(1.2): busca por ZIP + raio geográfico | Médio — 17 testes incluídos |
| 4 | **#87** | feat(0): confirmação de email + /i/ referral | Médio — revise se conflita com main |
| 5 | **#68** | feat(2.1): diretório empresas + Stripe assinatura | Alto — precisa de chaves Stripe configuradas |

**Nota**: Antes de dar merge, verifique conflitos com main (a landing page foi reconstruída em Aug 18).

---

## Decisões Pendentes

---

### [2026-09-12] D-001: Auth email vs. telefone — definição final

**Contexto:**
O ROADMAP original diz "email confirmado" mas a implementação atual (main) usa WhatsApp OTP
como autenticação primária. Há 4+ PRs tentando adicionar confirmação de email de formas
diferentes — todas não mergeadas e conflitando entre si.

**Pergunta:**
A plataforma é **telefone-first** (WhatsApp OTP = auth principal, email opcional) ou
**email-first** (email confirmado = requisito para "cadastro válido")?

**Opções:**

- **Opção A — Telefone-first (recomendação):**
  Manter auth por WhatsApp OTP como principal. Email é campo opcional no perfil, sem
  confirmação obrigatória. "Cadastro válido" = telefone verificado por OTP + ≥1 ação.
  - Prós: Já funciona em main hoje. Fluxo mais simples para imigrante (WhatsApp é universal).
    Nenhuma PR nova necessária para 0.1.
  - Contras: Perder o "email confirmado" do ROADMAP original. Anti-spam mais fraco.

- **Opção B — Email obrigatório para "cadastro válido":**
  Manter OTP para login mas exigir email confirmado para marcar o cadastro como "válido"
  (relevante para o programa de influenciadores em 1.3).
  - Prós: Filtro mais forte contra contas falsas para pagamento de influenciadores.
  - Contras: Precisa de serviço de email (SendGrid/Resend — ver D-002). Adiciona fricção no onboarding.

**Recomendação:** Opção A agora, Opção B na Fase 1.3 quando influenciadores pagos exigirem
verificação mais rigorosa. Responda aqui ou comente na PR.

**Status:** PENDENTE

---

### [2026-09-12] D-002: Serviço de email — qual provider?

**Contexto:**
Múltiplos PRs adicionam envio de email de confirmação mas nenhum tem um provider configurado.
O `.env.example` não tem variável de email.

**Pergunta:** Qual serviço de email usar?

**Opções:**
- **Resend** (resend.com): free tier 3k emails/mês, API simples, recomendado para startups.
- **SendGrid**: free tier 100/dia, mais complexo, mais estabelecido.
- **Supabase Auth nativo**: Supabase já envia emails de confirmação se usar `supabase.auth`.
  Implicaria migrar auth do JWT customizado para Supabase Auth — mudança maior.

**Recomendação:** Resend para começar (3k/mês cobre fase inicial bem), chave fácil de
configurar como env var. Custo: $0 até ~50k emails/mês.

**Status:** PENDENTE (depende de D-001)

---

### [2026-09-12] D-003: Deployment — app está no ar?

**Contexto:**
O `render.yaml` existe e está configurado. O `SETUP_PENDENTE.md` lista variáveis que precisam
ser configuradas. Não há confirmação de que a app esteja deployada e funcionando.

**Pergunta:** O app está deployado em produção? Qual é a URL atual?

**Por que importa:** Todo o código de feature é inútil se a app não está no ar.
O ROADMAP inteiro depende de isso estar resolvido.

**Ação necessária:**
1. Confirme se está deployado em Render (ou outro serviço)
2. Confirme que as variáveis de ambiente estão configuradas:
   - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
   - `SECRET_KEY` (JWT)
   - `ZAPI_INSTANCE`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN` (WhatsApp OTP)
   - `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_VIP_PRICE_ID` (Billing)
3. Confirme que o schema.sql foi aplicado no Supabase

**Status:** PENDENTE — bloqueador para testar qualquer feature em produção

---

*Atualizado em: 2026-09-12 — triage de 90 PRs acumuladas.*
