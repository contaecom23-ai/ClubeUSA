# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-10-24] D-001: BLOQUEIO CRÍTICO — 30+ PRs parados, projeto paralisado há 3 meses

**Contexto:**

O projeto está em paralisia total desde julho/agosto de 2026. Diagnóstico honesto:

**O que existe em `main` agora:**
- FastAPI rodando com routers de: `forum.py`, `news.py`, `assistant.py`
- Frontend `platform.html` (~130KB)
- Estrutura de banco (`db/`), serviços, utils

**O que NÃO existe em `main` (bloqueado nas branches):**
- Sistema de autenticação / cadastro de usuário
- Confirmação de email (Fase 0.1)
- Sistema de referral (Fase 0.2)
- Analytics básico (Fase 0.3)
- Definição de "cadastro válido" (Fase 0.4)

**Causa raiz da paralisia:**
Nenhum dos 30+ PRs abertos foi mergeado. O loop de 3x/dia do Claude continuou criando novas versões das mesmas features (a maioria é duplicata de email confirmation/Fase 0.1) porque o ROADMAP nunca avançou. Resultado: 30+ branches conflitantes, nenhuma linha nova em produção.

**Estado atual dos PRs (2026-10-24):**
- **PR #125** `feat/fase-0-CONSOLIDADA` — implementa Fase 0.1+0.2+0.3+0.4 completo. É o candidato mais consolidado. Criado em 2026-10-03.
- **PRs #126–142** — todos são variações da mesma coisa (email confirmation, status, analytics) ou docs de alerta. São duplicatas e devem ser fechados.
- **PR #140** — "PARE O LOOP" — alerta anterior ao dono (boa intenção, mas criou mais um PR em vez de parar).

**Pergunta objetiva:**

Você vai revisar e fazer merge dos PRs para desbloquear o projeto?

**Opções:**

**Opção A (RECOMENDADA): Fazer merge do PR #125 e fechar os duplicados**
- ✅ Desbloqueia Fase 0 inteira de uma vez
- ✅ Limpa a fila de PRs
- ✅ Claude pode continuar para Fase 1 na próxima execução
- ⚠️ Você precisa revisar PR #125 no GitHub e aprovar o merge
- ⚠️ Depois fechar PRs #126-142 como "duplicata/obsoleto"
- URL direto: https://github.com/contaecom23-ai/ClubeUSA/pull/125

**Opção B: Fechar TODOS os PRs e pedir rebuild limpo**
- ✅ Começa do zero sem bagagem
- ❌ Perde semanas de trabalho já feito
- ❌ O mesmo código será reescrito novamente

**Opção C: Continuar como está (não recomendada)**
- ❌ Claude continuará criando mais PRs duplicados a cada execução
- ❌ Projeto não avança para usuários reais
- ❌ Acúmulo de debt técnico de branches conflitantes

**Recomendação do Claude:**

**Opção A.** Vá ao PR #125, revise o código (deve levar ~15 minutos), faça merge. Depois feche os PRs #126 a #142 como "not planned" ou "duplicate". Com isso desbloqueado, a próxima execução começa Fase 1 (Promoções/Achados).

Se PR #125 tiver algum problema técnico que te impeça de mergear, responda neste PR ou abra uma issue explicando o bloqueio — o Claude ajusta.

**A ação mais importante que você pode fazer hoje é mergear ou fechar PRs.**

**Status:** PENDENTE — aguarda ação do dono

---

### [2026-10-24] D-002: Email transacional (obrigatório para Fase 0.1 funcionar)

**Contexto:**

Fase 0.1 requer envio de email de confirmação de cadastro. Isso exige uma conta de email transacional configurada como variável de ambiente.

**Pergunta:** Qual serviço de email você quer usar?

**Opções:**
- **Resend** (recomendado): fácil setup, free tier generoso (3k emails/mês), boa DX
- **SendGrid**: mais conhecido, free tier limitado (100/dia)
- **Mailgun**: opção robusta
- **SMTP genérico** (Gmail, etc.): possível mas frágil para produção

**Ação necessária:** Criar conta no serviço escolhido → gerar API key → adicionar como `EMAIL_API_KEY` e `EMAIL_FROM` nas variáveis de ambiente do Render (ou onde está deployado).

**Recomendação:** Resend.com — conta grátis, `/docs` claro, perfeito para 1k–10k usuários.

**Status:** PENDENTE — aguarda decisão + ação do dono

---

*Atualizado em: 2026-10-24*
