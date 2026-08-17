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

### [2026-08-17] D-001 — Autenticação: WhatsApp OTP vs. email confirmado

**Contexto:**
O roadmap original pede "email confirmado" na Fase 0.1. O código que existe em `main` usa WhatsApp OTP como único método de autenticação — email é campo opcional, nunca verificado. Isso foi uma escolha de produto feita em sessões anteriores sem registro explícito.

**Pergunta:**
O sistema de autenticação por WhatsApp OTP (sem email confirmado) é a decisão final de produto?

**Opções:**

- **Opção A — Manter WhatsApp OTP (recomendado):**
  - Prós: mais simples para o público-alvo (imigrantes brasileiros que já usam WhatsApp), sem fricção de email, já implementado e funciona
  - Contras: não tem "email confirmado" como o roadmap dizia; usuários sem WhatsApp são excluídos (minoria do público-alvo)
  - Custo: zero — já existe

- **Opção B — Adicionar email + confirmação em paralelo ao WhatsApp OTP:**
  - Prós: alcança usuários que preferem email; "email confirmado" como anti-fraude
  - Contras: duplica o sistema de auth, aumenta complexidade, email de imigrante pode ter qualidade baixa (muitos usam Gmail temporário), anti-fraude de email descartável é trabalhoso
  - Custo: ~2 semanas de dev

- **Opção C — WhatsApp OTP + email opcional mas verificado (não obrigatório):**
  - Prós: flexibilidade sem forçar, email vira fator de "cadastro válido" se fornecido
  - Contras: complexidade adicional, pouco valor real para o usuário médio

**Recomendação do Claude:** Opção A. WhatsApp OTP é adequado para o público e já funciona. "Email confirmado" no roadmap foi uma redação genérica — o *objetivo* (confirmar identidade real) é atendido pelo OTP WhatsApp. Atualizar o roadmap para refletir isso (já feito neste PR).

**Status:** PENDENTE

---

### [2026-08-17] D-002 — O que fazer com as 12 PRs abertas (nenhuma mergeada)

**Contexto:**
Em 2026-08-17 existem 12 PRs abertas:
- **PRs contra `main`:** #46 (Fase 0.1), #51 (docs), #52 (Fase 0.2) — estas são limpas e mergeáveis
- **Chain antiga (PRs #3–#20):** stacked entre si, cada uma tem como base o branch da PR anterior (não `main`). Isso significa que para mergear #12 (Fase 1.1) seria necessário antes mergear #9, que depende de #5, que depende de #4, que depende de #3. Total: 9 PRs em cascata, feitas sem validação do dono em cada etapa.

O Claude autônomo construiu adiantado demais (até Fase 1.5) sem esperar aprovação das fases anteriores. Cada PR faz sentido individualmente, mas a chain toda representa trabalho não revisado pelo dono.

**Pergunta:**
O que fazer com as PRs #3–#20 (chain antiga)?

**Opções:**

- **Opção A — Fechar as PRs antigas, rebasear o que for útil na hora certa (recomendado):**
  - Prós: limpa o projeto, foca no que importa agora (Fase 0), código das PRs antigas ainda existe nos branches e pode ser aproveitado; quando chegar a hora de Fase 1.1 rebasa o branch contra main atualizado
  - Contras: trabalho de fechar manualmente 9 PRs; código pode precisar de ajuste no rebase
  - Custo: ~30 min do dono para fechar PRs

- **Opção B — Mergear em cascata começando pela #3:**
  - Prós: aproveita o trabalho feito
  - Contras: seria mergear ~9 PRs sem revisar cada uma, pulando a Fase 0 incompleta, criando uma base de código desconhecida e potencialmente inconsistente; viola a regra de "uma fase por vez"
  - Custo: alto risco de bugs cumulativos

- **Opção C — Deixar como está e continuar adicionando PRs:**
  - Prós: não exige ação imediata
  - Contras: aumenta confusão, próximas sessões do Claude podem criar mais PRs duplicadas, GitHub fica ilegível
  - Custo: dívida técnica crescente

**Recomendação do Claude:** Opção A. Mergear em ordem: PR #46 (0.1) → PR #52 (0.2) → PR #51 (docs). Fechar as PRs #3–#20 com uma mensagem como "fechado — código preservado no branch, será rebased quando a fase for revisada". O Claude só cria nova PR de Fase 1 depois que Fase 0 estiver mergeada e validada.

**Status:** PENDENTE

---

### [2026-08-17] D-003 — Ambiente de produção: o app está rodando?

**Contexto:**
O `SETUP_PENDENTE.md` descreve setup no Render que requer chaves do Supabase, JWT_SECRET, ENCRYPTION_KEY, etc. O repositório tem `render.yaml` configurado. Não há evidência de que a API esteja em produção — não há URL de produção registrada no código, apenas `APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")`.

**Pergunta:**
A API do Clube USA já está rodando em produção (Render ou outro host)? Se sim, qual é a URL?

**Por que isso importa:**
- Se está em produção: mudanças no schema do banco são arriscadas (migração destrutiva requer cuidado extra); o Claude precisa saber disso antes de propor mudanças de banco
- Se não está: pode configurar ambiente de staging sem risco e testar as PRs antes de mergear

**Opções:**
- **A — Já está rodando:** informe a URL; Claude marca como contexto em todas as sessões futuras
- **B — Não está rodando ainda:** Claude pode recomendar setup básico e criar ambiente de staging
- **C — Está em desenvolvimento local apenas:** Claude pode ajudar a configurar Render via `render.yaml` existente

**Recomendação do Claude:** Responda aqui com A, B ou C + URL se aplicável. Sem isso, o Claude age conservadoramente em mudanças de banco.

**Status:** PENDENTE

---

## Decisões Resolvidas

*(nenhuma ainda)*

---

*Atualizado em: 2026-08-17*
