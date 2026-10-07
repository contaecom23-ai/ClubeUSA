# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexta, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

Formato de cada entrada:

```
### [DATA] Título da decisão
**Contexto:** ...
**Pergunta:** ...
**Opções:**
- Opção A: prós / contras
- Opção B: prós / contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## Decisões Pendentes

### [2026-09-27] #001 — Provider de email para confirmação

**Contexto:** A Fase 0.1 implementa confirmação de email. O código abstrai o envio (Resend > SMTP > log-dev). Em produção, um provider é obrigatório para os emails chegarem ao usuário.

**Pergunta:** Qual provider de email usar em produção?

**Opções:**
- **Resend** (recomendado): grátis até 3.000 emails/mês; API simples (um header Bearer); domínio próprio necessário para não cair em spam. Adicionar `RESEND_API_KEY` e `EMAIL_FROM` no env do Render.
  - Prós: fácil integração, boa deliverability, plano grátis suficiente para 1k usuários
  - Contras: requer verificação de domínio (clubeusa.com)
- **Sendgrid**: grátis até 100 emails/dia (limite apertado); mais burocrático.
  - Prós: consolidado no mercado
  - Contras: limite baixo no free tier
- **SMTP via Gmail/Zoho**: gratuito, mas com limites e menos deliverability.
  - Prós: sem custo inicial
  - Contras: risco de spam, limite 500/dia Gmail

**Recomendação:** Resend. Criar conta em resend.com, adicionar domínio `clubeusa.com`, setar `RESEND_API_KEY` e `EMAIL_FROM=noreply@clubeusa.com` no painel do Render. Leva ~30 min.

**O que fazer:**
1. Criar conta em resend.com
2. Verificar o domínio `clubeusa.com` (DNS TXT/MX)
3. Adicionar no ambiente de produção (Render/Supabase):
   ```
   RESEND_API_KEY=re_...
   EMAIL_FROM=noreply@clubeusa.com
   ```
4. Aplicar migration: `clubeusa/db/email_confirm_migration.sql` no Supabase SQL Editor

**Status:** PENDENTE

---

### [2026-09-27] #002 — Slug customizado para influenciadores (/i/joao)

**Contexto:** Fase 0.2 implementa `/i/{CODE}` com o código aleatório de 8 chars (ex: `/i/AB3D5F7G`). O roadmap menciona `/i/joao` — slugs legíveis por nome.

**Pergunta:** Vale a pena suportar slug customizado agora?

**Opções:**
- **A. Manter código aleatório** (implementado): `/i/AB3D5F7G`. Funcional, rastreável, sem conflitos.
  - Prós: zero esforço extra, seguro, já funciona
  - Contras: link feio para influencer divulgar nas redes
- **B. Adicionar campo `referral_slug` opcional** (a fazer): permite que influenciadores registrem `/i/joao`. Exige: coluna `referral_slug TEXT UNIQUE` em members + endpoint de atualização de slug + validação (sem espaços, sem caracteres especiais, sem palavras reservadas).
  - Prós: links atraentes para influencers (Fase 1.3 depende disso)
  - Contras: ~2h de dev extra; colisão de slugs precisa ser tratada

**Recomendação:** Fazer a **Opção B** quando iniciar a Fase 1.3 (Programa de Influenciadores). Não é bloqueante agora — o `/i/{CODE}` já funciona e rastreia corretamente.

**Status:** PENDENTE (adiar para Fase 1.3)

---

*Atualizado em: 2026-10-07*
