# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-10-16] Provedor de email para confirmação (Fase 0.1)

**Contexto:** A confirmação de email foi implementada. Em desenvolvimento, o link só é logado no console. Em produção, o código usa SMTP genérico (vars `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM`). Você precisa escolher e configurar um provedor antes do lançamento.

**Pergunta:** Qual provedor de email usar para emails transacionais (confirmação, recuperação de conta)?

**Opções:**
- **A — Resend** (resend.com): free tier 3.000 emails/mês, API moderna, mais simples de configurar. Requer troca de código (usar SDK, não SMTP). ~$20/mês a partir de 50k emails.
- **B — SendGrid** (sendgrid.com): free tier 100/dia, muito usado no mercado. Configurável via SMTP sem trocar código. Suporte a templates HTML.
- **C — Amazon SES**: $0,10 por 1.000 emails (praticamente grátis até 100k/mês). Requer conta AWS e verificação de domínio. Menor overhead de custo para escalar.
- **D — Brevo (ex-Sendinblue)**: free tier 300/dia, SMTP disponível, interface em português.

**Recomendação:** **C — Amazon SES** para produção (custo mínimo, escala bem até 1M usuários sem mudar nada). Enquanto não configurar, **D — Brevo** é o mais fácil para começar (free tier razoável, SMTP nativo, sem troca de código). Se já tem conta AWS, vá direto para SES.

**O que fazer:** Escolha o provedor, configure as vars de ambiente no Render/servidor e teste com um email real.

**Status:** PENDENTE

---

### [2026-10-16] URL do referral link (Fase 0.2)

**Contexto:** O sistema de referral existe e funciona — cada membro tem um `referral_code` e o link atual é `clubeusa.com?ref=CODIGO`. O roadmap menciona URL `clubeusa.com/i/joao` (slug de nome). Isso requer:
1. Campo `slug` único por membro (ex: "joao-silva-42")
2. Rota pública que lê o slug e redireciona com `?ref=CODE`
3. Ou slug é só o próprio referral_code (mais simples)

**Pergunta:** Qual formato de URL para o link de referral?

**Opções:**
- **A — Manter `?ref=CODE8CHR`** (atual): mais simples, já funciona, sem nova infraestrutura. Código é opaco (sem expor nome). Contra: menos "personalizável", links menos bonitos.
- **B — `clubeusa.com/i/CODIGO`** (rota curta): adiciona rota `/i/{code}` que redireciona para home com o ref. Sem mostrar nome do usuário. Fácil de implementar (1 endpoint).
- **C — `clubeusa.com/i/nome-slug`** (slug personalizado): mais bonito, mas requer campo extra no banco, validação de unicidade, e usuário pode não querer expor o nome. Complexidade maior.

**Recomendação:** **B** — adiciona `/i/{code}` (rota curta) sem expor nome. Links ficam `clubeusa.com/i/ABC12345` — limpos e rastreáveis. O Claude pode implementar isso sem decisão do dono, mas aguarda confirmação do formato antes de abrir novo PR.

**Status:** PENDENTE

---

### [2026-10-16] Recompensa de referral: imediata ou só após "cadastro válido" (Fase 0.4)

**Contexto:** Hoje, pontos de referral (200 pts) são creditados imediatamente no cadastro. A Fase 0.4 define "cadastro válido" = email confirmado + ≥1 ação real. Se recompensar antes da validação, alguém pode criar contas falsas para ganhar pontos.

**Pergunta:** Mudar a lógica para creditar pontos de referral apenas após "cadastro válido"?

**Opções:**
- **A — Manter crédito imediato**: mais simples, melhor experiência. Risco: abuse por contas falsas. Aceitável nos primeiros 1.000 usuários onde o dono conhece quem indica.
- **B — Crédito apenas após email confirmado**: reduz fraude sem ser muito rigoroso. Referral fica em status "pending" até confirmação. Requer alterar `_process_referral` para não pontuar imediatamente.
- **C — Crédito após email confirmado + 1 ação real** (Fase 0.4 completa): mais robusto contra fraude. Mais complexo de implementar. Melhor para quando o sistema estiver aberto ao público geral.

**Recomendação:** **B** por ora — crédito após email confirmado, antes do lançamento público. Implementar C quando Fase 0.4 estiver completa. O Claude pode implementar B, mas aguarda sua aprovação.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-16*
