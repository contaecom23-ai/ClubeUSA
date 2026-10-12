# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-10-12] D-001: Paralisia de Merge — 30 PRs abertos bloqueiam todo progresso

**Contexto:**
Existem 31 PRs abertos (incluindo este). O trabalho técnico das Fases 0.1 a 1.4 está 
FEITO em branches. Múltiplas sessões criaram PRs duplicados para as mesmas features 
e docs explicando o problema — sem resolver o blocante: os PRs precisam ser mergeados.

**Análise honesta:**
Criar mais PRs duplicados piora o problema. A partir desta sessão, o agente NÃO criará
PRs para funcionalidades já cobertas por branches existentes. O único desbloqueio real
é você revisar e mergear os PRs válidos.

**Pergunta objetiva:**
Quais PRs você quer que o agente prepare para merge? (rebase, resolve conflito, limpa)
Ou: posso fechar os duplicados e consolidar em PRs limpos?

**Recomendação concreta — 4 passos, ~10 minutos:**

1. **Mergear #110** — `fix(security): 3 correções` (webhook auth, fd leak, limit validation)
   - Sem conflito esperado; bugs reais de segurança; pequeno diff

2. **Mergear #103** — `test(api): 48 testes` cobrindo auth, billing, alertas, multi-tenant
   - Sem conflito esperado; só adiciona testes

3. **Verificar #125** — `CONSOLIDADA 0.1+0.2+0.3+0.4` (email confirm, referral, analytics)
   - Pode ter conflito após 2 meses; se tiver, escreva "rebase #125" aqui e o agente resolve

4. **Fechar como duplicatas** (todos cobertos pelo #125 + outros acima):
   - Email confirm: #106, #115, #121, #123, #127, #129
   - Referral URL: #102, #112, #117, #128
   - Analytics: #109, #119
   - Cadastro válido: #104
   - Docs de estado: #77, #78, #79, #80, #81, #111, #114, #118, #122, #124, #126

**PRs com trabalho real a mergear depois (não são duplicatas):**
- `#120` — Empregos (Fase 1.4)
- `#116` — Influencer tracking (Fase 1.3)
- `#113` — Promoções/Achados (Fase 1.1)
- `este PR` — ZIP search (Fase 1.2)

**Status:** PENDENTE — aguarda aprovação do dono

---

*Atualizado em: 2026-10-12*
