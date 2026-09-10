# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do agente.
> O agente NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o agente travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ BLOQUEIO CRÍTICO — 2026-09-10

### D-001 — 88 PRs abertas sem merge: projeto está parado há meses

**Contexto:**
O agente roda 3x/dia desde pelo menos agosto de 2026 e abriu 88 pull requests, nenhum foi mergeado. O `main` continua com o estado inicial — ROADMAP com todas as tarefas desmarcadas, DECISOES mostrando "nenhuma até agora". Do ponto de vista do código que importa (o que roda em produção), **nada avançou**.

Cada rodada do agente abre um PR novo partindo do `main`, sem saber o que foi feito nas outras branches. Resultado: pelo menos 5 implementações diferentes de confirmação de email (PRs #75, #84, #85, #87, e partes do #62) que nunca foram integradas. Scope creep, conflitos garantidos, e trabalho jogado fora.

**Diagnóstico real:**
- O `main` está estagnado: sem nenhuma feature de Fase 0 mergeada
- Os PRs acumulam mas não chegam a produção
- O agente continua gerando código que ninguém usa
- Sem merge, o projeto não tem um app funcional — só código em branches mortas

**Pergunta para o dono:**
Você está acompanhando os PRs? Qual o obstáculo para começar a mergear?

**Opções:**

**A) Você mesmo começa a mergear (recomendado)**
- Merge o PR #62 primeiro (não está em draft, marcado "PRONTO PARA MERGE"): `feat/consolida-0.2-0.3-seguranca`
- Depois solicite ao agente uma sessão de consolidação (fechar os PRs duplicados e criar um PR limpo por feature)
- Custo: ~30 minutos do seu tempo
- Prós: projeto volta a andar
- Contras: você precisa revisar o código

**B) Autoriza o agente a criar UM PR consolidado limpo**
- O agente fecha todos os PRs duplicados e cria um único PR por fase (0.1, 0.2, 0.3)
- Você mergeia 3 PRs em vez de 88
- Prós: mais gerenciável
- Contras: o agente não pode fechar PRs alheios sem sua autorização (regra de segurança)
- Para autorizar: responda a este PR dizendo "autorizo consolidação"

**C) Continuar como está**
- Não recomendado: o projeto continua gerando código que ninguém usa e nunca decola

**Recomendação do agente:** Opção A. Vá ao PR #62 agora e faça o merge. É o PR mais maduro, não está em draft, e consolida 0.2 + 0.3 + segurança de webhook. Depois PR #87 para email confirmation (0.1).

**Status:** PENDENTE — aguardando ação do dono

---

### D-002 — Confirmação de email requer serviço de email externo

**Contexto:**
A Fase 0.1 exige "email confirmado". O código para gerar tokens e salvar no banco está implementado em múltiplos PRs (#75, #84, #85, #87). O que está faltando é configurar um serviço real de envio de email (SMTP, SendGrid, Resend, etc.).

**Pergunta:** Qual serviço de email você quer usar?

**Opções:**
- **Resend** (recomendado para início): free até 3.000 emails/mês, API simples, entregabilidade boa. Custo após limite: ~$20/mês
- **SendGrid**: free até 100 emails/dia, mais burocrático para configurar
- **SMTP próprio (Gmail/Workspace)**: gratuito mas baixo limite e deliverability ruim para transacional

**Para desbloquear:** Crie uma conta em resend.com, gere uma API key, e adicione a variável `RESEND_API_KEY` no seu ambiente de deploy (Render/Railway/etc.).

**Status:** PENDENTE — bloqueado em D-001 (precisa mergear código antes)

---

### D-003 — Deploy: onde está rodando hoje?

**Contexto:**
Há um `render.yaml` no repo. Mas não está claro se o app está deployado em algum lugar. Sem deploy ativo, não há como validar que qualquer feature funciona para usuários reais.

**Pergunta:** O Clube USA está deployado e com URL pública? Se sim, qual?

**Para desbloquear:** Compartilhe a URL do deploy (ou confirme que não está deployado ainda) para que o agente possa focar nas tarefas certas.

**Status:** PENDENTE

---

## Decisões Aprovadas

*(nenhuma ainda)*

---

*Atualizado em: 2026-09-10 — Agente autônomo (rodada 3x/dia)*
