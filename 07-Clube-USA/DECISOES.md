# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.
> **Atualizado em: 2026-09-05** (3ª rodada sem resposta — projeto parado há +30 dias)

---

## ⚠️ BLOQUEIO CRÍTICO — AÇÃO HUMANA NECESSÁRIA

**31 PRs abertos, NENHUM mergeado. O projeto está parado.**

O Claude rodou 3 sessões seguidas (2026-09-04 e 2 sessões em 2026-09-05) sem nada novo para fazer além de registrar este bloqueio. Criar mais PRs não resolve — o problema é decisão, não código.

**O que existe e está esperando:**
- PR #62 ← **NÃO É DRAFT** — consolida 0.2+0.3+segurança, marcado como "PRONTO PARA MERGE"
- PR #75 ← email confirmation (Fase 0.1)
- PR #78 ← fix auth VIP token
- PR #80 ← fix deploy Z-API validation
- 27 outros PRs de features das Fases 0–2

**A app em produção (main) tem o código de junho de 2026 — sem as features das Fases 0–4.**

---

## Decisões Pendentes

### [2026-09-04] D-001: O que fazer com os 31 PRs abertos sem merge

**Contexto:**
- 31 PRs abertos, todos draft (exceto #62), desde agosto de 2026.
- Nenhum foi revisado nem mergeado.
- Fases 0.1, 0.2, 0.3, 0.4, 1.2, 1.3, 2.1 foram implementadas em branches — nada está no main.
- A main só tem: landing page, deal scanner (1.6), forum/news/AI chat.
- Os PRs mais antigos (agosto) podem ter conflitos entre si e com os mais novos.

**Pergunta objetiva:**
Como você quer lidar com os PRs acumulados?

**Opções:**

- **Opção A — Merge seletivo (RECOMENDAÇÃO MÍNIMA)**: Merge imediato dos 4 PRs críticos:
  1. `#62` (consolida 0.2+0.3+segurança — já está "PRONTO PARA MERGE", não é draft)
  2. `#75` (email confirmation — Fase 0.1)
  3. `#78` (fix auth VIP token)
  4. `#80` (fix deploy Z-API)
  Os outros 27 podem ser fechados.

- **Opção B — Cleanup + recomeço limpo**: Fechar todos os 31 PRs. O Claude recomeça as features mais importantes do zero, em um único PR por fase, com código atualizado sem conflitos. (Demora mais, mas começa limpo.)

- **Opção C — Pausa no Claude**: Você não tem tempo agora. Desativar o schedule até ter bandwidth.

- **Opção D — Merge em massa**: Mergear todos de uma vez. Não recomendado — há branches sobrepostas.

**Recomendação do Claude:** **Opção A** (merge seletivo dos 4 PRs críticos). É o caminho mais rápido para ter features reais em produção sem risco.

**Status:** PENDENTE — 3ª sessão sem resposta (2026-09-05)

---

### [2026-09-04] D-002: A plataforma está em produção?

**Contexto:**
- Z-API é obrigatório para OTP. Sem ele, o cadastro não funciona.
- Não há confirmação se a app está rodando em alguma URL pública.

**Pergunta objetiva:**
A plataforma Clube USA tem uma URL pública funcionando hoje?

- **Sim**: Me dê a URL e eu verifico o status.
- **Não (bloqueado por credenciais)**: Configure as env vars no Render (SUPABASE_URL, SUPABASE_KEY, ZAPI_TOKEN) e me informe.
- **Não (intencional)**: Continuamos só com dev local.

**Status:** PENDENTE

---

### [2026-09-04] D-003: O que você quer lançar PRIMEIRO?

**Contexto:** Foco é necessário. Com 31 PRs acumulados, o escopo ficou grande demais.

**Pergunta objetiva:**
Se pudesse ter UMA coisa funcionando para usuários reais nos próximos 7 dias, qual seria?

- **A) Cadastro + email confirmado (0.1)** — base para tudo
- **B) Link de referral (0.2)** — convide pessoas e rastreie quem veio de quem
- **C) Promoções/Achados (1.1)** — carro-chefe do produto
- **D) Diretório de empresas + assinatura (2.1)** — receita imediata

**Recomendação:** A) — sem cadastro, nada funciona.

**Status:** PENDENTE

---

## Como responder

Deixe um comentário no **PR #81** com:
```
D-001: Opção A
D-002: Não, bloqueado por Z-API
D-003: A
```

Ou responda aqui na sessão do Claude diretamente.

---

## Decisões Resolvidas

*(nenhuma ainda)*

---

*Atualizado em: 2026-09-05 (3ª sessão) | PR #81*
