# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-10-30] Provedor de email para confirmação de cadastro

**Contexto:**
A Fase 0.1 adicionou fluxo de confirmação de email. A infraestrutura está pronta (`utils/email.py`) com suporte a Resend, SMTP genérico e modo dev (log). Em prod, o `EMAIL_PROVIDER` precisa ser configurado — sem ele, os emails NÃO são enviados.

**Pergunta:**
Qual provedor de email usar para emails transacionais (confirmação de cadastro, futuramente alertas)?

**Opções:**

- **A — Resend** (`EMAIL_PROVIDER=resend`, variável `RESEND_API_KEY`)
  - Pros: API simples, free tier 3.000 emails/mês, excelente deliverability, developer-friendly
  - Contras: serviço externo pago a partir de escala (~$20/mês após free tier)

- **B — Amazon SES** (`EMAIL_PROVIDER=smtp` + credenciais SES)
  - Pros: muito barato em escala ($0,10/1.000 emails), boa deliverability
  - Contras: setup mais complexo (verificar domínio, sair do sandbox), requer conta AWS

- **C — Brevo (ex-Sendinblue)**
  - Pros: free tier 300/dia, SMTP nativo (sem troca de código), interface em português
  - Contras: free tier baixo, custo cresce rápido

**Recomendação:** **A — Resend** para os primeiros 1.000 usuários. Free tier suficiente, sem custo até escalar. Migrar para SES quando ultrapassar 3k emails/mês.

**Ação necessária pelo dono:**
1. Criar conta em resend.com
2. Verificar domínio clubeusa.com
3. Criar API key
4. Adicionar no Render: `EMAIL_PROVIDER=resend`, `RESEND_API_KEY=re_...`, `EMAIL_FROM=Clube USA <noreply@clubeusa.com>`

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

**Recomendação:** **B** — adiciona `/i/{code}` (rota curta) sem expor nome. Links ficam `clubeusa.com/i/ABC12345` — limpos e rastreáveis. O Claude pode implementar isso após confirmação do formato.

**Status:** PENDENTE

---

### [2026-10-16] Recompensa de referral: imediata ou só após "cadastro válido" (Fase 0.4)

**Contexto:** Hoje, pontos de referral (200 pts) são creditados imediatamente no cadastro. A Fase 0.4 define "cadastro válido" = email confirmado + ≥1 ação real. Se recompensar antes da validação, alguém pode criar contas falsas para ganhar pontos.

**Pergunta:** Mudar a lógica para creditar pontos de referral apenas após "cadastro válido"?

**Opções:**
- **A — Manter crédito imediato**: mais simples, melhor experiência. Risco: abuso por contas falsas. Aceitável nos primeiros 1.000 usuários onde o dono conhece quem indica.
- **B — Crédito apenas após email confirmado**: reduz fraude sem ser muito rigoroso. Referral fica em status "pending" até confirmação. Requer alterar `_process_referral`.
- **C — Crédito após email confirmado + 1 ação real** (Fase 0.4 completa): mais robusto contra fraude. Melhor quando o sistema estiver aberto ao público geral.

**Recomendação:** **B** por ora — crédito após email confirmado. Implementar C quando Fase 0.4 estiver completa. O Claude pode implementar B, mas aguarda aprovação.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-30*
