# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-09-21] D-007: AÇÃO OBRIGATÓRIA — 30+ PRs abertos sem merge

**Contexto:**  
Em 2026-09-21, o repositório tem 30+ PRs abertos aguardando review e merge.  
Features implementadas (email confirmation, referral redirect /i/{code}, analytics, deal urgency, influencer tiers, jobs, housing) estão todas em branches separadas, NENHUMA mergeada.  
O ROADMAP no main ainda mostra tudo como incompleto.  
O builder continua criando PRs novos a cada rodada, mas o backlog não diminui.

**Pergunta:**  
Qual ação tomar com os PRs acumulados?

**Opções:**

- **Opção A — Merge seletivo (RECOMENDADA):**  
  Faça merge de 3 PRs chave e feche os duplicados.  
  PRs para merge em ordem:  
  1. PR #103 — testes (sem conflito, puro acréscimo)  
  2. PR #100 — feat consolidado 0.2+0.3 (mais completo e recente)  
  3. PR #104 (este PR) — Fase 0.4 anti-fraude  
  Depois feche #74–#99 como "superseded by #100".

- **Opção B — Reset total:**  
  Fecha todos os 30+ PRs. O Claude cria um único PR unificado com todo o trabalho.  
  Custo: 1 rodada extra do builder.

- **Opção C — Status quo:**  
  Continua acumulando PRs. Risco: repositório vira arquivo inativo.

**Recomendação:** Opção A. Leva 10 minutos, desbloqueio imediato.

**Status:** PENDENTE — AÇÃO NECESSÁRIA DO DONO

---

### [2026-09-21] D-005: Confirmar referral só quando indicado se tornar "válido"?

**Contexto:**  
Atualmente pontos de referral (+200) são concedidos NO MOMENTO DO CADASTRO do indicado.  
Fase 0.4 define "cadastro válido" = phone_verified + total_clicks >= 1.  
Risco atual: alguém cria contas falsas via números VOIP → cadastros que nunca clicam → acumulam pontos para o indicador fraudulento.

**Pergunta:**  
Devemos confirmar o referral (e conceder pontos) apenas quando o indicado fizer seu primeiro clique?

**Opções:**

- **Opção A — Pontos após primeiro clique (RECOMENDADA):**  
  Elimina fraude em escala. Alinha com definição de "válido". Afeta apenas novos cadastros.  
  Implementação: mudar `_process_referral` para `status='pending'` e confirmar em `track_click`.

- **Opção B — Manter lógica atual (pontos imediatos):**  
  Sem mudança. Risco: fraude em escala com influenciadores de grande audiência.

**Recomendação:** Opção A. O custo de corrigir depois em produção com dados reais é muito maior.

**Status:** PENDENTE — aguarda decisão do dono

---

### [2026-09-21] D-006: Limite de cadastros por IP (3/24h) — correto?

**Contexto:**  
Fase 0.4 implementa bloqueio de mais de 3 cadastros do mesmo IP em 24h.  
Pode bloquear usuários legítimos em ambientes compartilhados (famílias, escritórios).

**Pergunta:**  
O limite de 3/IP/24h está correto para imigrantes brasileiros nos EUA?

**Opções:** 3 (atual), 5, ou 10 registros por IP por dia.

**Recomendação:** Manter 3 por ora. Fácil ajustar via env var se houver falsos positivos reportados.

**Status:** PENDENTE — informativo, ajuste quando aparecerem reclamações

---

*Atualizado em: 2026-09-21*
