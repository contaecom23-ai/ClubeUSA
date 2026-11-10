# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## ⚠️ SITUAÇÃO CRÍTICA — LEIA PRIMEIRO

**Data do diagnóstico:** 2026-11-10

Existem **169 PRs abertos** neste repositório. Nenhum foi mergeado.
O Claude roda 3x/dia, sempre vê o ROADMAP sem nenhum item marcado, e cria
mais um PR de verificação de email. É um loop que não termina sozinho.

**Não é um problema de código.** O código está pronto (ver D-001 abaixo).
É um problema de processo: você precisa mergear PRs para o projeto avançar.

**Ação necessária: 15 minutos do seu tempo** = projeto desbloqueado.

---

## Decisões Pendentes

### D-001 [2026-11-10] MERGE URGENTE — Email verification (Fase 0.1)

**Contexto:**
- Fase 0.1 (cadastro + email verificado) é o primeiro item do ROADMAP.
- O código está implementado em **pelo menos 20 PRs diferentes** — todos
  variações do mesmo tema, criados porque os anteriores nunca foram mergeados.
- O PR mais recente e mais completo é o **#167**:
  `feat(fase-0.1): verificação de email — tokens seguros, SMTP genérico, HTML de resposta`
- Os PRs #168 e #169 são diagnósticos do loop (apenas docs, sem código funcional).

**Pergunta:** Qual dos PRs de email verification você quer mergear?

**Opções:**
- **Opção A — Merge PR #167** (recomendado): mais recente, mais completo, tokens
  seguros com TTL 24h, SMTP configurável, HTML de resposta, testes incluídos.
- **Opção B — Merge um PR anterior** (#153, #152, #161, etc.): funcionalmente
  similares, mas possivelmente menos refinados.
- **Opção C — Nenhum; aguardar nova implementação**: desperdiça trabalho já
  feito; não recomendado.

**Recomendação:** Merge PR #167. Se tiver conflito, o PR #153 é a segunda
opção mais completa.

**Status:** PENDENTE

**Como mergear:**
1. Abra https://github.com/contaecom23-ai/ClubeUSA/pull/167
2. Revise rapidamente (ou confie no diagnóstico acima)
3. Clique "Merge pull request"
4. Repita para fechar/mergear os outros PRs duplicados ou fechá-los manualmente

---

### D-002 [2026-11-10] FECHAR PRs DUPLICADOS

**Contexto:**
Existem ~150 PRs duplicados ou diagnósticos que poluem o repositório.
Fechar em massa é irreversível no sentido de que o GitHub não tem
"reabrir em lote" — mas o código dos branches fica salvo.

**Pergunta:** Quer fechar manualmente os PRs duplicados?

**Opções:**
- **Opção A — Fechar manualmente via GitHub UI**: trabalhoso mas seguro.
- **Opção B — Fechar via GitHub API em lote**: rápido, requer autorização
  explícita do dono (Claude não faz isso sozinho).
- **Opção C — Deixar abertos**: não prejudica o projeto mas polui o histórico.

**Recomendação:** Mergear o PR #167, depois fechar os ~150 duplicados em lote
via GitHub UI (filtrar por "feat/fase-0.1" e fechar todos exceto o mergeado).

**Status:** PENDENTE

---

### D-003 [2026-11-10] PROCESSO — Como evitar o loop no futuro

**Contexto:**
O Claude autônomo cria PRs mas não pode mergear. Se a revisão demorar mais
de um ciclo (8h), o próximo ciclo recria o mesmo PR porque o ROADMAP no main
ainda mostra o item como incompleto.

**Pergunta:** Como quer organizar o processo de review?

**Opções:**
- **Opção A — Review diário**: você reserva 15 min/dia para mergear PRs.
  O Claude marca o ROADMAP no main e avança para o próximo item.
- **Opção B — Reduzir frequência do Claude**: de 3x/dia para 1x/dia,
  dando mais tempo para review antes do próximo ciclo.
- **Opção C — Pausar o Claude**: pausar o agente até você ter tempo de
  mergear os PRs acumulados e definir o processo.

**Recomendação:** Opção A + B combinados. Review rápido (5-10 min) todo dia
pela manhã. Reduzir para 1x/dia enquanto acumula menos de 3 PRs abertos.

**Status:** PENDENTE

---

### D-004 [2026-11-10] INFRAESTRUTURA — Supabase + SMTP para Fase 0.1

**Contexto:**
A Fase 0.1 (email verification) precisa de:
1. **Supabase**: URL e service_role key configurados em `.env`
2. **SMTP**: servidor de email para enviar tokens de verificação
   (pode ser Gmail com App Password, Resend, SendGrid, Mailgun, etc.)

Esses são segredos que o Claude não pode configurar sozinho.

**Pergunta:** Você já tem Supabase e SMTP configurados em produção?

**Opções:**
- **Opção A — Já tenho**: configure as variáveis em `.env` seguindo o
  `.env.example` e o deploy funcionará.
- **Opção B — Preciso criar Supabase**: acesse https://supabase.com,
  crie um projeto gratuito, copie a URL e service_role key para `.env`.
- **Opção C — Preciso de SMTP**: Resend (resend.com) oferece 3.000 emails/mês
  grátis. É o mais simples para começar. Alternativa: Gmail com App Password.

**Recomendação:** Supabase free tier + Resend free tier = custo zero para
os primeiros 1.000 usuários.

**Status:** PENDENTE

---

## Decisões Concluídas

*(nenhuma ainda — aguardando primeiro merge)*

---

*Atualizado em: 2026-11-10*
