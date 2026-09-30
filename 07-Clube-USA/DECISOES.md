# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-09-30] D-001: PARALISIA DE MERGE — 30+ PRs aguardando sua aprovação

**Contexto:**
O projeto acumulou 30+ PRs abertos desde agosto. Nenhum foi mergeado. Isso significa que a `main` ainda tem o código original de agosto, e todas as features novas (Fase 0.1 a 2.1) existem apenas em branches. O Claude continua abrindo PRs novos (como este, Fase 1.4), mas o valor real só aparece quando você mergear.

**Situação real em main agora (2026-09-30):**
- Auth por WhatsApp OTP ✅
- Deals/scanner ✅
- Referral básico (link `?ref=`) ✅
- Admin panel ✅
- Price alerts ✅
- News/Forum/Assistant ✅
- Email confirmado ❌ (em PR #106/115)
- Referral pretty URL `/i/code` ❌ (em PRs #70/102/112/117)
- Analytics ❌ (em PRs #67/109/119)
- Anti-fraude ❌ (em PR #104)
- Influencer tiers ❌ (em PR #116)
- Promoções comunitárias ❌ (em PR #113)
- Business subscriptions ❌ (em PR #68)
- **Empregos (Jobs) ❌ → este PR #feat/fase-1.4-empregos-jobs**

**Pergunta:**
Você quer mergear os PRs? Se sim, em que ordem e com qual estratégia?

**Opções:**

**Opção A — Mergear em ordem, começando pelos mais antigos de Fase 0:**
- PR #106 (email confirmação, Fase 0.1) → PR #102 (referral, Fase 0.2) → PR #109 (analytics, Fase 0.3) → PR #104 (anti-fraude, Fase 0.4) → demais fases
- Prós: segue o roadmap, menos conflitos
- Contras: pode haver conflitos entre branches antigas; exige revisão de cada PR

**Opção B — Ignorar os 30 PRs antigos e pegar só os mais recentes (1 por feature):**
- Para cada feature, pegar o PR mais recente (ex: #115 para email, #117 para referral, #119 para analytics)
- Fechar os PRs duplicados mais antigos
- Prós: menos conflitos, código mais atualizado
- Contras: perde histórico de PRs mais antigos

**Opção C — Claude cria um branch consolidado com tudo em ordem:**
- Uma branch limpa `release/fase-0` que aplica todas as mudanças de Fase 0 em sequência
- Um único PR para mergear tudo de uma vez
- Prós: um PR só, mais fácil para o dono revisar
- Contras: mais trabalho para o Claude; se algo der errado, é um PR grande

**Recomendação do Claude:**
Opção B é a mais prática. Os PRs mais recentes têm o código mais atual e refinado. Para cada fase:
- Email (0.1): PR #115
- Referral (0.2): PR #117
- Analytics (0.3): PR #119
- Anti-fraude (0.4): PR #104
- Promoções (1.1): PR #113
- Influencers (1.3): PR #116
- Business (2.1): PR #68
- Empregos (1.4): PR atual (feat/fase-1.4-empregos-jobs)

Feche os duplicados mais antigos para limpar a fila.

**Status:** PENDENTE — aguardando decisão do dono

---

*Atualizado em: 2026-09-30*
