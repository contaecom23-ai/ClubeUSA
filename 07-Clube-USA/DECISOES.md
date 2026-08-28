# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## 🚨 ALERTA CRÍTICO — 2026-08-28

**31 PRs abertos, zero mergeados desde o início do projeto.**

O agente rodou 3x/dia por semanas gerando código de qualidade — auth, referral, analytics, promoções, empregos, moradia, assinaturas — mas nada entrou no main. O sistema está em loop morto: produz trabalho que nunca é integrado. Isso é um problema de processo, não de código.

**A principal coisa que precisa acontecer é você revisar e mergear o PR #46.**

---

## Decisões Pendentes

### [2026-08-28] URGENTE: O que fazer com os 31 PRs sem merge

**Contexto:** 31 PRs cobrem Fases 0.1 até 2.1. O main não tem nenhum feature code. Há PRs duplicados para o mesmo item (ex: Fase 0.1 em PRs #46, #54, #62 — variações e correções ao longo do tempo). PRs mais novos às vezes corrigem problemas dos mais antigos.

**Pergunta:** Como quer resolver o backlog?

**Opções:**

- **Opção A — Mergear em ordem, PR #46 primeiro** ← Recomendado
  - PR #46 ("feat: Fase 0.1") é o mais antigo, não-draft, pré-requisito de tudo
  - Prós: histórico limpo, começa a desbloquear a cascata
  - Contras: PRs subsequentes terão conflitos que o Claude resolve automaticamente
  - **Estimativa: 30 min do seu tempo para revisar e mergear o #46**

- **Opção B — Fechar todos e consolidar em 1 PR**
  - Fechar os 31 PRs e pedir ao Claude para criar UM PR consolidado com o melhor código de cada fase
  - Prós: limpo, sem conflitos cruzados, um histórico único
  - Contras: perde histórico dos PRs individuais; Claude precisa de 1 sessão longa para fazer

- **Opção C — Continuar como está**
  - Não recomendada. O agente continuará gerando PRs que nunca entram no main, ficando cada vez mais stale.

**Recomendação:** Opção A. 30 minutos hoje. Mergear o PR #46. O Claude resolve os conflitos dos próximos PRs automaticamente a cada rodada.

**Status:** PENDENTE — aguardando decisão do dono

---

### [2026-08-28] Deploy: onde hospedar a API

**Contexto:** O repo tem `render.yaml` configurado para Render.com. Sem merge no main, nenhum deploy acontece. Mesmo após mergear, é preciso criar conta no Render, configurar env vars (Supabase URL/key, Stripe keys, JWT secret, SMTP) e apontar o domínio.

**Pergunta:** Quer usar Render.com ou outra plataforma?

**Opções:**
- **Render.com** (já configurado): gratuito para começar, auto-deploy da main. Recomendado para os primeiros 1.000 usuários.
- **Railway**: similar, ligeiramente mais estável, tem custo mínimo.
- **VPS próprio (DigitalOcean $6/mês)**: mais controle, mais trabalho de setup.

**Recomendação:** Render.com. Custo zero até escalar. O Claude finaliza o render.yaml após o merge.

**Status:** PENDENTE — aguardando decisão do dono

---

### [2026-08-26] Supabase e Stripe: contas configuradas?

**Contexto:** A plataforma precisa de Supabase (banco + auth) e Stripe (pagamentos futuros). Sem as chaves, o deploy não funciona mesmo após o merge.

**Pergunta:** Contas Supabase e Stripe já criadas? As chaves estão disponíveis para configurar nas env vars do Render?

**Status:** PENDENTE — sem confirmação do dono

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, produto/negócio, gasto, chaves externas, direção estratégica, irreversível ou com custo), ele registra aqui e segue para outra tarefa. Você revisa 1x/dia.

---

*Atualizado em: 2026-08-28*
