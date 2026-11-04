# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
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

**Contexto:** A Fase 0.1 implementa confirmação de email. O código abstrai o envio com hierarquia: Resend > SMTP > log-dev. Em produção, um provider é obrigatório para os emails chegarem ao usuário.

**Pergunta:** Qual provider de email usar em produção?

**Opções:**
- **Resend** (recomendado): grátis até 3.000 emails/mês; API simples (um header Bearer); domínio próprio necessário para não cair em spam. Adicionar `RESEND_API_KEY` e `EMAIL_FROM` no env do Render.
  - Prós: fácil integração, boa deliverability, plano grátis suficiente para 1k usuários
  - Contras: requer verificação de domínio (clubeusa.com)
- **SendGrid**: grátis até 100 emails/dia (limite apertado); mais burocrático.
  - Prós: consolidado no mercado
  - Contras: limite baixo no free tier, não cobre 1k usuários no free
- **SMTP via Gmail/Zoho**: gratuito, mas com limites e menos deliverability.
  - Prós: sem custo inicial, configuração simples via `SMTP_HOST`
  - Contras: risco de spam, limite 500/dia Gmail

**Recomendação:** Resend. Criar conta em resend.com, adicionar domínio `clubeusa.com`, setar `RESEND_API_KEY` e `EMAIL_FROM=noreply@clubeusa.com` no painel do Render. Leva ~30 min.

**O que fazer:**
1. Criar conta em resend.com
2. Verificar o domínio `clubeusa.com` (DNS TXT/MX)
3. Adicionar no ambiente de produção (Render):
   ```
   RESEND_API_KEY=re_...
   EMAIL_FROM=noreply@clubeusa.com
   ```
4. Aplicar migration no Supabase SQL Editor: `clubeusa/db/email_confirmation_migration.sql`

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

### [2026-11-04] #003 — PARALISIA DE MERGE: 155 PRs acumulados, projeto parado

> ⚠️ Atualizado em 2026-11-04. Situação piorou de 30 PRs (2026-10-21) para **155 PRs abertos** hoje.

**Contexto:** O Claude roda 3x/dia implementando features corretas com qualidade de produção, mas como nenhum PR jamais foi mergeado, cada sessão encontra `main` desatualizado e reimplementa as mesmas coisas. Resultado: 155 PRs abertos com 10+ implementações duplicadas de cada feature (email confirmation aparece em 10 PRs diferentes, analytics em 4, referral em 6...). O produto não existe em produção.

**Impacto real:** 
- Zero código em produção desde o início do projeto autônomo
- Centenas de horas de trabalho técnico inacessíveis ao usuário final
- O problema se agrava exponencialmente — cada nova sessão adiciona mais divergência

**O que há pronto (esperando merge):**
- **Fase 0.1** ✅ confirmação de email (token criptográfico, expiração 24h, endpoint GET/POST, 11+ testes)
- **Fase 0.2** ✅ referral link rastreável `/i/{CODE}` com atribuição  
- **Fase 0.3** ✅ analytics de crescimento (série temporal, cadastros/dia)
- **Fase 0.4** ✅ cadastro válido verificável + anti-fraude por IP
- **Fase 1.1** ✅ Promoções/Achados (submit comunitário + curadoria admin)
- **Fase 1.2** ✅ busca por ZIP + raio geográfico (17 testes)
- Fixes de segurança (webhook auth, fd leak, rate-limit)

**Ação mínima (10 minutos):**
1. Escolha UM PR não-draft que consolide bem e mergei-o. PRs não-draft ativos:
   - **PR #110**: fix(security) — 3 correções de segurança ← menor e mais seguro
   - **PR #62**: feat consolida 0.2+0.3+segurança ← features prontas
2. Depois que qualquer coisa chegar ao `main`, o Claude para de reimplementar e avança para features novas
3. Configurar `RESEND_API_KEY` no Render (ver DECISOES #001) — independe de merge

**Por que não fechar todos os PRs e abrir um novo?** 
O Claude não faz merge/close em PRs que não criou nesta sessão. É uma ação irreversível que só o dono faz.

**Pergunta direta:** Você quer revisar PRs? Ou prefere parar as execuções automáticas até poder olhar?

**Status:** PENDENTE — BLOQUEIO TOTAL (155 PRs, 0 em produção)

---

*Atualizado em: 2026-11-04*
