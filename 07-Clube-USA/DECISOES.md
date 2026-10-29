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

### [2026-10-21] #003 — PARALISIA DE MERGE: 30+ PRs abertos sem revisão

**Contexto:** Situação verificada em 2026-10-21. O repositório acumulou 30+ PRs abertos, a maioria implementando as mesmas features em duplicata (9 PRs diferentes para email confirmation sozinho, contadas em PR #115, #121, #123, #127, #129, #130, #132, #134, #139). O Claude roda 3x/dia abrindo novos PRs mas você não revisa/mergeia, então os PRs acumulam e o `main` nunca avança.

**Impacto real:** Nada chegou ao `main` desde o início do projeto autônomo. O produto **não evoluiu em produção** mesmo com centenas de horas de trabalho técnico gerado. Há risco de perda total do trabalho por divergência crescente.

**Pergunta:** Como desbloquear o fluxo de desenvolvimento para que o código chegue ao `main`?

**Opções:**
- **A. Revisão manual semanal**: você revisa e mergeia PRs 1x/semana. Desbloquearia tudo imediatamente.
  - Prós: você mantém controle total; zero risco de código ruim no main
  - Contras: exige ~30 min/semana de sua atenção

- **B. Mergear PR #125 agora** (CONSOLIDADA 0.1+0.2+0.3+0.4 - não-draft, "PRONTO PARA MERGE"): esse PR já consolidou as features das fases 0.1–0.4 resolvendo os conflitos entre todas as duplicatas. É a ação de menor esforço para desbloquear.
  - Prós: uma ação, resultado imediato; resolve a base para Fase 1
  - Contras: requer que você leia o diff antes de mergear (sempre recomendado)

- **C. Fechar todos os PRs exceto PR #125 + PR #135** (security fix): limpar a fila e manter apenas o que importa.
  - Prós: fila limpa; menor confusão nas próximas sessões
  - Contras: ~10 min para fechar os PRs manualmente

**Recomendação (honesta):** Opção B + C combinadas. **Mergear PR #125** (Fase 0 consolidada) e **PR #135** (fix de segurança), depois fechar todos os outros como "superseded". Em seguida, o Claude retoma normalmente da Fase 1.1. O projeto está tecnicamente pronto para produção nas Fases 0.x — só falta o merge.

**Para fazer AGORA (5 minutos):**
1. Abrir https://github.com/contaecom23-ai/ClubeUSA/pull/125 → revisar → mergear
2. Abrir https://github.com/contaecom23-ai/ClubeUSA/pull/135 → revisar → mergear
3. Configurar `RESEND_API_KEY` no Render (ver DECISOES #001)
4. Rodar a migration SQL no Supabase

**Status:** PENDENTE — BLOQUEIO CRÍTICO (projeto parado em produção)

---

*Atualizado em: 2026-10-21*
