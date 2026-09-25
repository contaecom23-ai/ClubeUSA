# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 Decisões Pendentes

---

### [2026-09-25] D-001: PARALISIA DE MERGE — 30+ PRs abertos, nenhum mergeado

**Contexto:**
O sistema autônomo roda 3x/dia desde setembro e abriu 30+ PRs. Nenhum foi mergeado. O ROADMAP no main mostra Phase 0 inteira como não concluída. A cada sessão, o bot verifica o ROADMAP, vê que Phase 0 não está feita, e cria NOVOS PRs para o mesmo trabalho — gerando duplicatas. Há 4+ PRs diferentes para email confirmation e 5+ para referral redirect. Cada novo PR aumenta a paralisia.

**Estado atual do main (o que está em produção hoje):**
- Auth: WhatsApp OTP (funcional)
- Deals, leaderboard, Stripe billing: funcional
- Email confirmation (Fase 0.1): **ausente** — schema sem coluna `email_confirmed`
- Referral redirect `/i/{code}` (Fase 0.2): **ausente**
- Analytics endpoint (Fase 0.3): **ausente**
- Cadastro válido + anti-fraude (Fase 0.4): **ausente**

**O problema real:** Criar mais PRs não resolve nada. O projeto avança quando você mergeia.

**Pergunta:**
Para cada grupo abaixo, qual PR você quer mergear? (ou: quer fechar todos e criar um consolidado limpo?)

**PRs recomendados para merge, em ordem de prioridade:**

| Prioridade | PR | Título | Por que mergear este |
|---|---|---|---|
| 1º | [#110](https://github.com/contaecom23-ai/ClubeUSA/pull/110) | fix(security): webhook auth + fd leak + limit validation | Segurança em produção — sem risco funcional, só correções |
| 2º | [#106](https://github.com/contaecom23-ai/ClubeUSA/pull/106) | feat(fase-0.1): email confirmation — token seguro + SMTP | O mais recente e mais limpo para Phase 0.1 |
| 3º | [#102](https://github.com/contaecom23-ai/ClubeUSA/pull/102) | feat(fase-0.2): GET /i/{code} referral redirect | Mais simples e focado para Phase 0.2 |
| 4º | [#109](https://github.com/contaecom23-ai/ClubeUSA/pull/109) | feat(fase-0.3): /admin/analytics/growth | Phase 0.3 analytics |
| 5º | [#104](https://github.com/contaecom23-ai/ClubeUSA/pull/104) | feat(fase-0.4): cadastro válido + anti-fraude por IP | Phase 0.4 — fechar o ciclo de validação |
| 6º | [#103](https://github.com/contaecom23-ai/ClubeUSA/pull/103) | test: 48 testes cobrindo auth, billing, alertas | Cobertura de testes — mergear após os features |

**PRs para FECHAR (duplicatas — o trabalho está nos PRs acima):**

Fechar os PRs #83, #84, #85, #87, #88, #89, #90, #91, #92, #93, #94, #95, #96, #97, #98, #99, #100, #101, #105, #107, #108 como duplicatas/supersedidas. São PRs mais antigos que cobrem o mesmo trabalho ou são docs de triage que acumularam.

**Opções:**

- **Opção A (recomendada):** Mergear os 6 PRs da tabela acima na ordem indicada. Fechar os demais como duplicatas. Leva ~30 minutos de revisão. Projeto sai do zero.
- **Opção B:** Fechar TODOS os PRs abertos e começar do zero com um único PR consolidado limpo. Mais demorado mas código mais coeso.
- **Opção C:** Configurar um branch de integração (`develop`) onde o bot mergeia automaticamente, e você só revisa merges de `develop` → `main`. Reduz o atrito de revisão.

**Recomendação do Claude:** Opção A. Os PRs indicados são os mais recentes e mais limpos para cada item. A sequência de merge garante que o mais seguro (correções de segurança) entre primeiro.

**Ação imediata sugerida:**
1. Abrir PR #110 → revisar → mergear
2. Abrir PR #106 → revisar → mergear
3. Fechar os demais PRs duplicados com comentário "Supersedido por #106/#102/etc."

**Status:** PENDENTE — aguardando decisão do dono

---

### [2026-09-25] D-002: Autenticação — WhatsApp OTP vs Email/Senha

**Contexto:**
O sistema atual autentica usuários via WhatsApp OTP (número de telefone). Não há senha. O ROADMAP Phase 0.1 menciona "email confirmado". Há tensão entre:
- O que o sistema tem: auth por WhatsApp OTP (funcional, zero fricção para brasileiro com WhatsApp)
- O que o ROADMAP pede: email confirmado

**Pergunta:**
Email confirmation deve ser:
- (A) Obrigatório para completar cadastro (usuário não acessa sem confirmar email)?
- (B) Opcional — confirma email para desbloquear features extras, mas pode usar o app com só WhatsApp?
- (C) Abandonar email confirmation e focar 100% em WhatsApp OTP (que já funciona)?

**Trade-offs:**
- A: Mais seguro, menos fraude, mas aumenta fricção de onboarding. Risco: usuário desiste antes de confirmar.
- B: Melhor conversão no cadastro, email como feature extra. Recomendado para early-stage (primeiros 1.000 usuários).
- C: Mais simples. Problema: sem email, não tem canal de marketing/reengajamento barato.

**Recomendação do Claude:** Opção B. Para os primeiros 1.000 usuários, maximize conversão. Email é um canal de marketing valioso — colete mas não bloqueie. Implemente "confirme email para ganhar +100 pontos" em vez de bloqueio.

**Status:** PENDENTE — aguardando decisão do dono

---

*Atualizado em: 2026-09-25*
