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

### [2026-10-13] D-001 — PARALISIA DE MERGE: 30 PRs parados, projeto bloqueado

**Contexto:**

O agente autônomo está rodando 3x/dia desde junho/2026. Hoje há **30+ PRs abertos**, todos aguardando merge pelo dono. A branch `main` ainda está no estado original de junho/2026 — nenhuma linha de código das Fases 0–1 foi incorporada. Cada sessão nova entra, não encontra progresso na main, e recria o mesmo trabalho: email confirmation, referral links, analytics. O problema não é técnico — o código existe e está pronto. O problema é de processo.

**Diagnóstico dos PRs mais relevantes:**

| PR | Branch | Cobre | Estado |
|----|--------|-------|--------|
| [#125](https://github.com/contaecom23-ai/ClubeUSA/pull/125) | `feat/fase-0-CONSOLIDADA` | Fases 0.1+0.2+0.3+0.4 completas | ✅ Pronto, não-draft, clean |
| [#130](https://github.com/contaecom23-ai/ClubeUSA/pull/130) | `feature/fase0.1-email-confirmation` | Fase 0.1 apenas | Draft, subconjunto do #125 |
| #102–#124, #126–#129 | Várias | Variantes dos mesmos temas | Duplicatas ou superadas pelo #125 |

**Pergunta objetiva:**

Você quer continuar com este projeto? Se sim, precisa **fazer merge de pelo menos 1 PR agora**.

**Opções:**

- **Opção A — RECOMENDADA:** Fazer merge do PR #125 (o mais completo) → fechar os demais como duplicatas → agente avança para Fase 1 na próxima sessão.
- **Opção B:** Revisar um PR diferente e fazer merge dele. Qualquer PR funciona melhor do que continuar sem merge.
- **Opção C:** Fechar todos os PRs e pausar o agente autônomo até ter capacidade de revisar. Melhor do que acumular mais código sem uso.

**Prós/Contras:**

| | A | B | C |
|---|---|---|---|
| Tempo | 2 min | 30+ min (revisar 30 PRs) | 5 min |
| Preserva trabalho feito | ✅ Sim | ✅ Parcialmente | ❌ Perde tudo |
| Desbloqueia o projeto | ✅ Hoje | ✅ Hoje | — |
| Risco | Baixo — migrações SQL idempotentes | Médio — pode conflitar | Nenhum |

**Recomendação do agente:**

**Opção A.** O PR #125 tem checklist de segurança completo, migrações idempotentes (seguro re-executar), cobre Fase 0 inteira e está pronto para merge. Leva 2 minutos para você fazer o merge no GitHub. Depois o agente avança para Fase 1 na próxima sessão.

Após o merge de #125, os PRs #102–#124 e #126–#130 podem ser fechados com a mensagem "superado pelo PR #125".

**Consequência de não agir:**

O agente continuará abrindo PRs de Fase 0 indefinidamente (já são mais de 15 versões do mesmo código). Cada sessão desperdiça tokens e cria mais ruído sem valor.

**Link direto para merger:** https://github.com/contaecom23-ai/ClubeUSA/pull/125

**Status:** PENDENTE — aguardando ação do dono

---

### [2026-10-13] D-002 — SMTP: qual provedor de email usar em produção?

**Contexto:**

O código de confirmação de email (já implementado no PR #125) suporta qualquer provedor SMTP. Em desenvolvimento, loga o link no console sem precisar de credenciais. Em produção, precisa de um provedor configurado via variáveis de ambiente.

**Pergunta:** Qual provedor SMTP usar?

**Opções:**

- **SendGrid** — free até 100 emails/dia, suporte PT-BR, integração simples. Cobre os primeiros 1.000 usuários sem custo. **Recomendado para começar.**
- **AWS SES** — mais barato em escala ($0.10/1000 emails), mas exige conta AWS e processo de verificação de domínio.
- **Resend.com** — novo, API moderna, free tier 100/dia, fácil de configurar.

**Recomendação:** SendGrid para os primeiros 1.000 usuários (free tier, configuração em 10 min). Migrar para AWS SES ou Resend quando ultrapassar 100 emails/dia.

**O que você precisa fazer:** Criar conta no SendGrid → gerar API key → configurar nas env vars do servidor.

**Status:** PENDENTE — depende de D-001 ser resolvido primeiro

---

*Atualizado em: 2026-10-13*
