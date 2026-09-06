# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ DECISÕES PENDENTES

---

### [2026-09-06] D-001: 30 PRs sem merge — projeto parado há 75 dias — PLANO DE AÇÃO CONCRETO

**Status:** PENDENTE — requer ação humana

**Contexto:**
Desde 23/06/2026 (75 dias), nenhum PR foi mergeado. O `main` está desatualizado e este DECISOES.md ainda está vazio no main. O agente Claude abriu 30 PRs (features + docs) — mas sem merge, o produto não avança. Cada nova rodada abre mais PRs sobre o mesmo problema.

Com 30 PRs acumulados:
- PRs de docs TODAS conflitam entre si (editam os mesmos arquivos)
- Alguns PRs de feature duplicam a mesma funcionalidade (ex: 0.1 email foi feito 2x)
- O agente está em loop: abre PR → não mergeia → abre PR sobre o PR anterior

**Pergunta:** O que fazer para desbloquear?

---

**Opção A — Merge seletivo (RECOMENDADO):**

**PASSO 1 — Fechar estes PRs (docs duplicados, todos conflitam entre si):**
Vá em cada um e clique "Close pull request":
- #53, #59, #60, #64, #66, #69, #71, #72, #73, #74, #76, #77, #79, #81
- Motivo: todos só editam ROADMAP.md/DECISOES.md, conflitam entre si, e este PR tem a versão mais recente.

**PASSO 2 — Fechar estes PRs de feature (duplicados por versões mais novas):**
- #54 → supera por #75 (mesma feature 0.1, versão mais completa)
- #55 → supera por #67 (mesma feature analytics)
- #70 → supera por #62 (mesma consolidação 0.2+0.3)

**PASSO 3 — Merge dos feature PRs em ordem (↑ primeiro = sem conflito):**
1. **#56** — ci: pytest workflow (base para CI rodar nos próximos PRs)
2. **#75** — feat(0.1): email confirmation (Phase 0.1 — base de tudo)
3. **#57** — fix(referral): captura de ?ref= no frontend (Phase 0.2)
4. **#62** — feat: consolida 0.2 + 0.3 + segurança webhook (Phase 0.2/0.3)
5. **#58** — feat(0.4): cadastro válido + anti-fraude
6. **#63** — test: auth + isolamento de segurança
7. **#61** — fix(security): verificar token Z-API no webhook
8. **#80** — fix(deploy): Z-API obrigatório no startup
9. **#65** — feat(1.2): busca por ZIP + raio geográfico
10. **#67** — feat: analytics GET /admin/analytics (Phase 0.3)
11. **#78** — fix(auth): VIP plan perdido no re-login
12. **#68** — feat(2.1): diretório de empresas + Stripe

**PASSO 4 — Merge este PR** (PR #82 — atualiza ROADMAP.md e DECISOES.md no main)

**AVISO:** Mesmo na ordem acima, podem aparecer conflitos pequenos em `api/main.py` ou `requirements.txt`. Se aparecer conflito, diga ao Claude para resolver.

---

**Opção B — Reset e consolidação:**
Criar uma única branch com tudo junto. Mais limpo, mas requer ~4h de trabalho do Claude para consolidar sem perder nada. Viável se você preferir histórico limpo.

**Opção C — Manter status quo:**
Projeto para completamente. Não recomendado.

---

**Recomendação do Claude:** Opção A. Comece pelo PASSO 1 (fechar 14 docs PRs) — leva 5 minutos e já limpa a fila. Depois PASSO 3 na ordem listada.

**Ação necessária:** Você. O Claude não pode mergear ou fechar PRs.

---

### [2026-09-06] D-002: O app está deployado em produção?

**Status:** PENDENTE

**Contexto:** Não há evidência de que a aplicação (FastAPI + Supabase) esteja deployada. O `DEPLOYMENT.md` e `render.yaml` existem mas não há URL de produção conhecida pelo agente.

**Pergunta:** O app está live? Qual é a URL de produção?

**Motivo:** Sem saber se está deployado, o agente não pode testar features end-to-end nem priorizar corretamente (fixes de deploy vs. novas features).

**Ação:** Confirme a URL ou diga "não está deployado ainda".

---

*Atualizado em: 2026-09-06*
