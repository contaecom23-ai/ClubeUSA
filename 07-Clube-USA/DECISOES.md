# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ ALERTA CRÍTICO — 2026-09-09

**O projeto está travado há semanas.** 30+ PRs foram abertos, nenhum foi mergeado. Como DECISOES.md no main estava vazio, cada sessão do agente começava sem saber disso e abria mais um PR. Este arquivo resolve esse ciclo vicioso.

**Ação imediata necessária:** Responda à D-001 abaixo.

---

## Decisões Pendentes

### [2026-09-09] D-001: Como desbloquear os 30 PRs acumulados?

**Contexto:**
- 30+ PRs estão abertos (PR #58 a #87), nenhum mergeado
- O código do produto está dividido entre branches e o main não evoluiu
- O agente continua criando PRs sem que o dono revise/merge
- Sem resolução, o projeto permanece em standby indefinido

**Pergunta:** Como você quer destravar o desenvolvimento?

**Opções:**

**Opção A — Merge em ordem (RECOMENDADO)**
Mergear 3 PRs essenciais agora, fechar o resto como duplicatas:
1. Merge PR #75: `feat/fase-0-1-email-confirmacao` — email confirmation (Fase 0.1)
2. Merge PR #83: `feat/0-2-referral-link` — link /i/{code} (Fase 0.2)
3. Merge PR #67: `feat/0.3-analytics-basico` — analytics (Fase 0.3)
4. Fechar como duplicatas: PRs #84, #85, #87 (email), #70, #71 (referral), #66, #64 (docs)
5. Revisar e decidir: PRs #61, #62, #63, #65, #68, #58 (features adicionais)

*Prós:* Produto avança com base sólida; código testado entra no main.
*Contras:* Requer ~30 min do seu tempo para revisar e mergear.

**Opção B — Reset de workflow: commits diretos em branches pequenas**
Fechar TODOS os 30 PRs sem mergear. Adotar branches de 1-2 arquivos por sessão com commits diretamente na branch base (sem acumular).

*Prós:* Elimina o backlog imediatamente; mais simples.
*Contras:* Perde o trabalho feito nos 30 PRs (código de email confirmation, referral, analytics, etc.).

**Opção C — Deploy manual: você faz o merge localmente**
```bash
git fetch origin feat/fase-0-1-email-confirmacao
git merge origin/feat/fase-0-1-email-confirmacao
# repetir para os outros
git push origin main
```
*Prós:* Você controla o que entra sem depender do GitHub PR interface.
*Contras:* Mais trabalhoso; bypassa revisão de código.

**Recomendação:** Opção A. Leva 30 min mas preserva semanas de trabalho. Se não tiver tempo agora, diga "resetar" e vou para a Opção B.

**Status:** PENDENTE — aguardando resposta do dono

---

### [2026-09-09] D-002: Autenticação — telefone ou email?

**Contexto:**
O sistema atual usa autenticação por telefone via OTP WhatsApp (Z-API). Os 30 PRs parados incluem ~5 PRs tentando adicionar confirmação de email por cima.

**Pergunta:** Qual é o método de autenticação principal?

**Opções:**
- **A — Manter telefone/WhatsApp (atual):** Sem dependência de email; perfeito para imigrantes que têm WhatsApp. Não requer SMTP/SendGrid. Z-API custa ~$15/mês.
- **B — Migrar para email:** Mais fácil de testar; sem custo de WhatsApp; mas perde o "magic" do onboarding via WhatsApp que é diferencial para brasileiros.
- **C — Ambos (telefone como primário, email opcional):** Mais robusto mas mais complexo.

**Recomendação:** Opção A (manter telefone). O WhatsApp é o canal natural para brasileiros nos EUA. Adicionar email só se Z-API criar problemas de custo/confiabilidade.

**Status:** PENDENTE

---

### [2026-09-09] D-003: Deploy — o app está rodando em produção?

**Contexto:**
Existe render.yaml e DEPLOYMENT.md no repositório, mas não há confirmação de que o app está deployado. SETUP_PENDENTE.md cita várias configurações ausentes.

**Pergunta:** O Clube USA está rodando em algum servidor com usuários reais?

**Opções:**
- **A — Sim, está no Render:** Informe a URL e o agente pode validar o health check.
- **B — Não, ainda não deployado:** O agente pode preparar o checklist de deploy.
- **C — Outro servidor:** Informe onde.

**Status:** PENDENTE

---

## Decisões Resolvidas

*(nenhuma ainda)*

---

*Atualizado em: 2026-09-09*
