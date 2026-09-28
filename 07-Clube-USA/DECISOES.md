# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto, aprovação de gasto, chaves externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### D-001 [2026-09-28] PARALISIA DE MERGE — ação humana necessária para o projeto avançar

**Contexto:**
Desde agosto de 2026, o agente autônomo abriu 30+ PRs implementando as Fases 0.1 a 2.1 do roadmap. Nenhum PR foi mergeado. O branch `main` está congelado desde 2026-06-23. O produto não evoluiu de fato.

Esta mensagem foi registrada em PRs anteriores múltiplas vezes (#66, #69, #72, #73, #74, #76, #77, #79, #81, #111, #114). Continuando a gerar código sem merge só aumenta o problema.

**Pergunta objetiva:**
Você quer continuar com PRs (e então precisar mergear), ou prefere outra abordagem?

**Opções:**

**A) Mergear os PRs agora (RECOMENDADO)** — O produto avança, o código real fica em main.

Ordem de merge sugerida (cada um pode ter conflitos com o anterior — GitHub avisa):
1. **PR #110** `fix(security)` — correções de segurança (webhook auth, fd leak, limit validation) — deve vir primeiro
2. **PR #103** `test(api)` — 48 testes de auth, billing, isolamento multi-tenant
3. **PR #115** `feat(0.1/0.2)` — email confirmation + redirect de indicação
4. **PR #117** `feat(0.2)` — link de referral /i/{code} com analytics
5. **PR #109** `feat(0.3)` — analytics de crescimento /admin/analytics/growth
6. **PR #104** `feat(0.4)` — cadastro válido + anti-fraude por IP
7. **PR #113** `feat(1.1)` — Promoções/Achados submit comunitário + curadoria admin
8. **PR #65**  `feat(1.2)` — busca por ZIP + raio geográfico
9. **PR #116** `feat(1.3)` — influencer tier tracking (Parceiro/Embaixador/Hall da Fama)
10. **PR #68**  `feat(2.1)` — diretório de empresas + assinatura Stripe

Depois de mergear esses 10, feche os PRs duplicados restantes.

**B) Trabalhar em `main` diretamente** — Sem PR, sem review. Mais rápido, sem proteção. Possível se o dono entender o risco e confiar no agente.
- Pró: zero atrito de merge, produto evolui a cada run
- Contra: sem review humano, sem rollback fácil, vai contra as regras do próprio projeto
- Recomendo NÃO fazer sem pelo menos criar um branch de staging protegido

**C) Parar de gerar código até fazer o merge** — O agente pára features novas e só documenta e audita.
- Pró: não piora o problema
- Contra: produto não avança

**Minha recomendação:** Opção A. Mergear em ordem. Se algum PR tiver conflito, o GitHub mostra exatamente onde resolver. Se você não sabe como resolver conflitos no GitHub, posso criar um guia passo-a-passo detalhado — diga e faço.

**Ação imediata sugerida:** Abra o PR #110 no GitHub, clique "Merge pull request", repita para #103, #115, #117, #109, #104, #113, #65, #116, #68 nessa ordem.

**Status:** PENDENTE — aguardando decisão do dono

---

### D-002 [2026-09-28] PRs duplicados — fechar ou ignorar?

**Contexto:**
Há PRs duplicados para as mesmas features (ex: 0.1 tem PRs #75, #106, #115 — o mais recente supersede os anteriores). Os obsoletos poluem a lista.

**Pergunta:** Posso criar um PR que fecha os duplicados automaticamente via comentário, ou você prefere fechar manualmente?

**Recomendação:** Fechar manualmente os antigos (não-merge) depois que os novos estiverem em main. Lista a fechar após merge dos 10 acima:
- Fechar (não mergear): #114, #112, #111, #106, #102, #81, #80, #79, #78, #77, #76, #75, #74, #73, #72, #71, #70, #69, #67, #66

**Status:** PENDENTE

---

*Atualizado em: 2026-09-28*
