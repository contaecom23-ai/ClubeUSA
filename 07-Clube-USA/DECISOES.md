# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

Formato de cada entrada:

```
### [DATA] Título da decisão
**Contexto:** ...
**Pergunta:** ...
**Opções:**
- Opção A: prós / contras
- Opção B: prós / contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## Decisões Pendentes

---

### [2026-11-05] D-001 — PARALISIA DE MERGE: 157 PRs abertos, nenhum mergiado

**Contexto:**
O builder roda 3x/dia desde junho. Há 157 PRs abertos com implementações reais de Fase 0 e 1, mas nenhum foi mergiado em main. Resultado: o builder vê o ROADMAP.md com as mesmas checkboxes vazias toda vez e continua criando novas implementações duplicadas para os mesmos itens. A lista cresceu sem valor entregue.

**Estado real (2026-11-05):**
- Main branch: tem a API base com OTP/WhatsApp auth + schema com referral_code, mas SEM email confirmation e SEM `/i/{code}` redirect
- **Já implementado em branches (aguardando merge):**
  - Fase 0.1 (email confirmation): PRs #153, #152, #150, #148, #115, #106 (6 implementações)
  - Fase 0.2 (/i/{code} referral redirect): PRs #157, #117, #115, #112, #102 (5 implementações)
  - Fase 0.3 (analytics): PR #109
  - Fase 0.4 (cadastro válido + anti-fraude): PR #104
  - Fase 1.1 (promoções comunitárias): PR #113
  - Fase 1.3 (influencer tiers): PR #116
- **Novo nesta sessão:** PR `fix/security-audit-2026-11-05` — 3 correções de segurança reais (PII em logs, OTP timing attack, CSP header)

**Pergunta:**
Você consegue dedicar 30 minutos para fazer o merge dos PRs críticos e desbloquear o projeto?

**Plano de merge recomendado (ordem):**
1. Merge PR #153 (`feat/fase-0.1-email-confirmado`) — Fase 0.1 ✓
2. Merge PR #157 (`feat/fase-0.2-referral-redirect`) — Fase 0.2 ✓
3. Merge PR #109 (`claude/fase-0.3-analytics-growth`) — Fase 0.3 ✓
4. Merge PR #104 (`feat/fase-0.4-valid-cadastro`) — Fase 0.4 ✓
5. Merge este PR (`fix/security-audit-2026-11-05`) — segurança ✓
6. Fechar os outros PRs duplicados com comentário "duplicado por #XXX"

**Depois do merge:** atualizar o ROADMAP.md com [x] nas fases concluídas para o builder poder avançar para Fase 1.

**Consequência de não agir:**
O builder continuará criando implementações duplicadas para os mesmos itens indefinidamente. Já são 157 PRs. Sem merge, o produto não avança.

**Recomendação:**
Faça o merge dos 5 PRs acima agora. São todos PRs de código novo, sem conflito destrutivo com main. Se algum conflito surgir, é resolvível em minutos.

**Status:** PENDENTE

---

*Atualizado em: 2026-11-05*
