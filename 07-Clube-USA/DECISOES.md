# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do builder.
> O builder NÃO age em itens desta lista sem sua aprovação explícita — exceto D-008 (ver abaixo).

---

## Como usar

Quando o builder travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚡ AÇÃO IMEDIATA NECESSÁRIA (bloqueante para avançar)

**Fase 0 e Fase 1.1 estão codificadas e testadas.** Nenhum PR foi merged por falta de decisões de infraestrutura.

**O que você precisa fazer, na ordem:**
1. Resolver **D-002** (Supabase) + **D-003** (email) + **D-004** (hosting) + **D-005** (domínio)
2. Fechar PRs redundantes: **#1, #6, #7, #8**
3. Fazer review e merge na ordem: **PR #2 → #3 → #4 → #5 → #9 → PR de Fase 1.1**
4. Rodar `004_promotions.sql` no Supabase após merge da Fase 1.1
5. Responder **D-010** antes que o builder implemente tracking de views

---

## Decisões Pendentes

---

### [2026-07-03] D-001: Merge order dos PRs de Fase 0 (ação imediata)

**Contexto:** Existem 11 PRs abertos. A cadeia canônica é #2→#3→#4→#5→#9. 4 são redundantes.

**Ação recomendada:**
1. Fechar PRs redundantes: #1, #6, #7, #8
2. Review e merge na ordem: **PR #2 → PR #3 → PR #4 → PR #5 → PR #9 → PR fase-1.1**

**Status:** PENDENTE

---

### [2026-07-03] D-002: Configuração do projeto Supabase (BLOQUEANTE para deploy)

**Contexto:** Toda a plataforma usa Supabase como banco. Código pronto, mas sem banco não roda.

**O que fazer:**
1. Criar projeto em https://supabase.com — plano gratuito cobre os primeiros 1.000 usuários
2. Rodar as migrations em ordem no SQL Editor do Supabase:
   - `07-Clube-USA/supabase/migrations/001_profiles.sql`
   - `07-Clube-USA/supabase/migrations/002_referrals.sql`
   - `07-Clube-USA/supabase/migrations/003_analytics.sql`
   - `07-Clube-USA/supabase/migrations/004_promotions.sql` ← novo (Fase 1.1)
3. Coletar as credenciais (Settings > API):
   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
4. Configurar email confirmation (Authentication > URL Configuration):
   - Site URL: URL do frontend; Redirect URL: `https://seusite.com/confirm.html`

**Custo:** $0 no plano gratuito

**Status:** PENDENTE

---

### [2026-07-03] D-003: Provedor de email transacional

**Contexto:** Supabase gratuito limita a 3 emails/hora — inaceitável para lançamento.

**Recomendação:** Resend.com ($0 até 3.000 emails/mês) → configurar direto no Supabase (Settings > Auth > SMTP).

**Custo:** $0 até 3.000/mês

**Status:** PENDENTE

---

### [2026-07-03] D-004: Hospedagem do backend FastAPI

**Recomendação:** Railway (~$5/mês) — deploy via GitHub em 5 minutos, zero cold start. Reversível.

**Custo:** ~$5/mês

**Status:** PENDENTE

---

### [2026-07-03] D-005: Domínio do Clube USA

**Recomendação:** Registrar `clubeusa.com` no Cloudflare Registrar (~$12/ano). Necessário para links de email e credibilidade.

**Custo:** ~$12/ano

**Status:** PENDENTE

---

### [2026-07-04] D-006: Definição final de "ação real" para cadastro válido (pré-Fase 1.3)

**Contexto:** Critério atual (ZIP preenchido) é fraco. Fase 1.3 precisa de critério mais robusto para evitar fraude no pagamento de influenciadores.

**Recomendação:** Migrar para email confirmado (opção B) imediatamente, depois exigir ≥1 visualização de promoção (opção C) quando Fase 1.1 estiver no ar.

**Status:** PENDENTE — decidir antes de lançar Fase 1.3

---

### [2026-07-04] D-007: Valor por cadastro válido e teto orçamentário — Programa de Influenciadores

**Contexto:** Fase 1.3 paga por cadastro válido com teto. Precisamos de números antes de implementar.

**Recomendação:** $2/cadastro válido, teto $100/mês por influenciador na fase beta.

**Status:** PENDENTE — aprovação do dono + orçamento antes da Fase 1.3

---

### [2026-07-06] D-008: Perguntas de produto para Fase 1.1 — PROMOÇÕES/ACHADOS

**Status:** RESOLVIDO — builder procedeu com as recomendações em 2026-07-07

**Decisões tomadas (todas reversíveis):**
1. Quem cria: admin via X-Admin-Key. Self-service de empresas fica para Fase 2.1.
2. Campos: title, description, store, category, zip_code (opcional), expires_at (opcional), discount_url (opcional), discount_code (opcional), image_url (opcional).
3. Urgência: badge automático por expires_at — sem campo manual, sem quantidade.
4. Modelo geográfico: nacional por enquanto, sem filtro ZIP. Filtro entra na Fase 1.2.
5. Descoberta: lista cronológica paginada (page, page_size). Zero algoritmo no MVP.

---

### [2026-07-07] D-009: Workflow YAML estava quebrado

**Contexto:** O `.github/workflows/clubeusa-builder.yml` inicial tinha indentação malformada — o builder nunca rodou no agendamento. Fix está no PR #10 (`claude/fix-workflow-yaml-e-docs-main`).

**Ação necessária:** Mergear PR #10 junto com a cadeia de Fase 0.

**Status:** AGUARDA MERGE DO PR #10

---

### [2026-07-07] D-010: Rastrear views de promoções por usuário?

**Contexto:** Ao implementar Fase 1.1, surgiu a questão: devemos registrar quando um usuário autenticado visualiza/clica em uma promoção?

**Por que importa:**
1. **Anti-fraude (D-006):** Visualizar uma promoção pode ser a "ação real" para validar um cadastro — mais forte que só ter ZIP preenchido.
2. **Analytics de produto:** Quais promoções geram mais interesse? Quais categorias convertem?
3. **Personalização futura (Fase 4.3):** Base para recomendações.

**Trade-offs:**
- **Sim, rastrear:** Adiciona 1 endpoint `POST /promotions/{id}/view` (auth obrigatória) + nova coluna `promotion_views`. Permite D-006 opção C. Custo: ~1 dia de implementação.
- **Não por enquanto:** MVP mais simples. Views sem auth são anônimas e difíceis de usar para anti-fraude. Pode ser adicionado depois sem breaking change.

**Recomendação:** Não implementar agora. Lançar primeiro, medir engajamento real, adicionar tracking na segunda iteração da Fase 1.1 quando houver usuários reais para validar a utilidade.

**Status:** PENDENTE — aguarda decisão do dono antes do builder implementar tracking

---

*Atualizado em: 2026-07-07 — Fase 1.1 implementada (D-008 resolvido; D-010 adicionado)*
