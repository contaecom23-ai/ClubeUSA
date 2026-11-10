# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⛔ BLOQUEIO CRÍTICO — 168 PRs sem merge (ativo desde ~jun/2026)

### [2026-11-10] D-001: Loop de PRs — como desbloquear

**Contexto:**
O agente roda 3×/dia e cria PRs, mas nenhum PR foi mergeado desde o início do projeto (~jun/2026). Resultado: **168 PRs abertos**, código duplicado em ~20 branches de email verification, DECISOES.md vazio em main, ROADMAP com tudo unchecked.

Isto NÃO é um bug do código — é um processo bloqueado. O código para Fase 0.1 (email confirmation) foi escrito corretamente pelo menos 5× nos últimos 2 meses. Continuar criando mais PRs idênticos não resolve nada.

**Estado real do main (2026-11-10):**
- API FastAPI completa: auth via WhatsApp OTP, Stripe, referrals, deal scanner, forum, news
- Schema com tabela `members` (phone_hash, email_hash, referral_code, etc.)
- **Sem** `email_verified` / `email_verification_tokens` — Fase 0.1 incompleta
- Sem código de Fase 0.2–1.x em main

**Pergunta:**
O que você quer que o agente faça enquanto PRs não são mergeados?

**Opções:**

**Opção A (recomendada):** Você dedica 15 minutos para mergear os 3 PRs abaixo em ordem. O agente pode então avançar.

```
Ordem de merge (cada um depende do anterior):
1. PR #110 — fix(security): 3 correções urgentes [base, sem dependências]
2. PR #167 — feat(fase-0.1): verificação de email — tokens seguros, SMTP genérico
3. PR #157 — feat(fase-0.2): referral redirect rastreável
```

Depois de mergear os 3, feche todos os outros PRs de email (152, 153, 160, 161, 162, 163, 164, 165, 166, 168 e os anteriores). Eles são duplicatas dos acima.

*Prós:* Desbloqueia o projeto. O código está pronto.
*Contras:* Exige 15 min de revisão sua.

**Opção B:** Você me diz o que está errado com os PRs (bug específico, estrutura incorreta, decisão técnica diferente). Eu corrijo e reabro.

*Prós:* Resultado mais alinhado com o que você quer.
*Contras:* Exige que você articule a objeção.

**Opção C:** Parar o agente até você ter tempo de revisar PRs.

*Prós:* Sem mais acúmulo de branches.
*Contras:* Projeto para completamente.

**Recomendação:** Opção A. O código do PR #167 é limpo e testado. Os 15 minutos de revisão vão desbloquear meses de trabalho.

**Status:** PENDENTE — sem ação do dono o agente não criará mais PRs de código (apenas este tipo de doc update).

---

### [2026-11-10] D-002: Configuração de SMTP para email verification

**Contexto:**
O PR #167 implementa verificação de email com suporte a SendGrid, Mailgun, AWS SES e SMTP genérico. Mas precisa de credenciais de SMTP para funcionar em produção.

**Pergunta:**
Qual provedor de email você quer usar para enviar emails de verificação?

**Opções:**
- **SendGrid** (Free tier: 100 emails/dia) — mais fácil de configurar, bem documentado
- **AWS SES** (~$0.10/1000 emails) — mais barato em escala, precisa de conta AWS
- **Mailgun** (5000 emails/mês grátis nos primeiros 3 meses) — bom para transacional
- **SMTP genérico** (Gmail, Zoho, etc.) — mais simples mas com limites

**Recomendação:** SendGrid para os primeiros 1.000 usuários. Grátis, fácil, não precisa de verificação de domínio imediata.

**Status:** PENDENTE — sem isso o email verification não vai a produção (mas pode ser testado localmente).

---

*Atualizado em: 2026-11-10*
