# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ BLOQUEIO CRÍTICO — Leia primeiro

**Data:** 2026-11-08  
**Situação:** 163 PRs abertos, **zero merges na main**. O agente roda 3x/dia e continua criando PRs para as mesmas features (email, referral) em loop infinito, pois a main nunca avança.

**Consequência técnica real:** Toda feature de Fase 0 (email confirmado, referral pretty URL, analytics, anti-fraude) já está implementada em código em branches separados. Nenhuma entrou na main. O ROADMAP mostra `[ ]` para itens que têm implementação pronta há meses.

**O que está travando:** Você (o dono) precisa mergear os PRs. O Claude não pode mergear — só abre PRs.

---

## Decisões Pendentes

---

### [2026-11-08] D-001 — Desbloquear o projeto: quais PRs mergear e em que ordem

**Contexto:**  
A main tem uma API FastAPI completa e funcional (auth OTP via WhatsApp, deals, referral via `?ref=`, billing Stripe, admin, rastreador de produtos). O que falta são as features de Fase 0 que estão prontas em PRs não mergeados.

**Problema de arquitetura que precisa da sua decisão:**  
Fase 0.1 diz "email confirmado", mas a auth atual é 100% via OTP pelo WhatsApp (sem senha, sem email obrigatório). Os PRs adicionaram email confirmation de formas diferentes — alguns usam SMTP, outros SendGrid. Qual é o seu plano?

- **Opção A:** Manter auth por WhatsApp OTP. Email é campo opcional no cadastro. Confirmação de email é "bônus" (não bloqueia acesso). → Mais simples, funciona com o que já existe, não requer serviço de email.
- **Opção B:** Adicionar email como obrigatório + confirmação bloqueia acesso até confirmar. → Mais complexo, requer serviço transacional (SendGrid/Resend/SMTP), mais atrito no onboarding.
- **Opção C:** Autenticar por email em vez de WhatsApp (email magic link). → Grande refactor, incompatível com o que existe.

**Recomendação do Claude:** Opção A. O produto é voltado para WhatsApp — isso é a identidade. Email opcional confirma sem bloquear. Isso também desbloquearia imediatamente os PRs de Fase 0.1.

**Se você escolher A, PRs para mergear nesta ordem:**

| Ordem | PR | Branch | O que faz |
|-------|-----|--------|-----------|
| 1 | #163 | fix/cors-secure-default-decisoes-2026-11-08 | CORS seguro (sem wildcard em prod) |
| 2 | #161 | feat/fase-0-1-email-confirmation | Email confirmation (mais recente) |
| 3 | #157 | feat/fase-0.2-referral-redirect | Redirect /i/{code} rastreável |
| 4 | #109 | claude/fase-0.3-analytics-growth | Analytics de crescimento admin |
| 5 | #104 | feat/fase-0.4-valid-cadastro | Cadastro válido + anti-fraude IP |

> ⚠️ Aviso: como esses PRs foram criados em momentos diferentes e partem de commits diferentes da main, **pode haver conflitos**. Se houver, o Claude resolve os conflitos no momento do merge — mas você precisa iniciar o processo.

**Status:** PENDENTE — aguardando sua decisão sobre email (Opção A/B/C) + ok para começar a mergear.

---

### [2026-11-08] D-002 — Fechar PRs duplicados em massa

**Contexto:**  
Existem 163 PRs abertos. A maioria são duplicatas para as mesmas features (ex: 9 PRs diferentes para email confirmation). Isso polui o repositório e torna difícil saber qual PR é "o certo" a mergear.

**Pergunta:**  
Você autoriza o Claude a fechar os PRs duplicados mais antigos, mantendo apenas o mais recente e bem implementado de cada feature?

**Proposta de limpeza:**
- Manter: PRs #163, #161, #157, #113, #116, #109, #104, #110 (os mais recentes e relevantes)
- Fechar: todos os outros (PRs #102–#162 exceto os listados acima)

**Recomendação:** Sim, fechar os duplicados. Ter 163 PRs abertos é ruído, não progresso.

**Status:** PENDENTE — aguardando autorização para fechar duplicados.

---

### [2026-11-08] D-003 — Serviço de email transacional (necessário para Fase 0.1 Opção B)

**Contexto:**  
Se escolher a Opção B da D-001 (email obrigatório), precisará de um serviço transacional. Os PRs existentes implementam diferentes opções.

**Opções:**
- **SendGrid** (usado em alguns PRs): $0 até 100/dia free. Já configurado em alguns PRs. Requer SENDGRID_API_KEY.
- **Resend** (preferível hoje em dia): $0 até 100/dia free, melhor DX, mais moderno. Requer RESEND_API_KEY.
- **SMTP próprio** (Gmail/Zoho): Gratuito mas menos confiável para transacional em escala.

**Recomendação:** Resend se quiser email obrigatório. Mas o Claude recomenda Opção A (email opcional) para não adicionar dependência externa desnecessária agora.

**Status:** PENDENTE — depende da decisão D-001.

---

## Decisões Concluídas

*(nenhuma ainda)*

---

*Atualizado em: 2026-11-08*
