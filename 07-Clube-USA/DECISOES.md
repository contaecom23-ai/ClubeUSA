# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do builder.
> O builder NÃO age em itens desta lista sem sua aprovação explícita — exceto D-008 (ver abaixo).

---

## Como usar

Quando o builder travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚡ AÇÃO IMEDIATA NECESSÁRIA (bloqueante para avançar)

**Estado em 2026-07-11:** Fases 0.1 → 1.4 codificadas e testadas. **Nenhum PR merged ainda** — plataforma inteira aguarda sua revisão de infra.

**O que você precisa fazer, na ordem:**
1. Resolver **D-002** (Supabase) + **D-003** (email) + **D-004** (hosting) + **D-005** (domínio)
2. Fechar PRs redundantes: **#1, #6, #7, #8, #11, #13, #15, #17, #18** (duplicatas — cobertos pela cadeia canônica abaixo)
3. Mergear na ordem: **PR #10 → PR #2 → PR #3 → PR #4 → PR #5 → PR #9 → PR #12 → PR #14 → PR #16 → PR #19 (Fase 1.4) → PR #20 (Fase 1.5)**
4. Rodar migrations em ordem no Supabase: `001` → `002` → `003` → `004` → `005` → `006` → `007`
5. Rodar `data/seed_zip_codes.sql` + `data/seed_jobs.sql` + `data/seed_housing.sql` para popular ZIPs, vagas e anúncios de moradia
6. Responder **D-010** antes que o builder implemente tracking de views

---

## Decisões Pendentes

---

### [2026-07-03] D-001: Merge order dos PRs (ação imediata) — atualizado 2026-07-08

**Contexto:** 13 PRs abertos, nenhum merged. Muitos são versões duplicadas do mesmo trabalho de runs anteriores do builder. Cadeia correta identificada.

**PRs a FECHAR (duplicatas — não mergear):**
- #1, #6, #7 → versões antigas de Fase 0.1 (PR #2 é a canônica)
- #8 → sync de docs (PR #10 cobre isso)
- #11, #13 → versões mais antigas de Fase 0.1

**Ordem de MERGE (uma de cada vez, base → topo):**
1. **PR #10** — fix workflow YAML quebrado (urgente: sem isso, o builder não roda no cron)
2. **PR #2** — Fase 0.1: cadastro + perfil + email
3. **PR #3** — Fase 0.2: referral rastreável
4. **PR #4** — Fase 0.3: analytics
5. **PR #5** — Fase 0.4: cadastro válido + anti-fraude
6. **PR #9** — security polish
7. **PR #12** — Fase 1.1: promoções/achados
8. **PR #14** — Fase 1.2: busca ZIP + raio
9. **PR #16** — Fase 1.3: programa de influenciadores

**Status:** PENDENTE — bloqueante para qualquer deploy

---

### [2026-07-03] D-002: Configuração do projeto Supabase (BLOQUEANTE para deploy)

**Contexto:** Toda a plataforma usa Supabase como banco. Código pronto, mas sem banco não roda.

**O que fazer:**
1. Criar projeto em https://supabase.com — plano gratuito cobre os primeiros 1.000 usuários
2. Rodar as migrations em ordem no SQL Editor do Supabase:
   - `07-Clube-USA/supabase/migrations/001_profiles.sql`
   - `07-Clube-USA/supabase/migrations/002_referrals.sql`
   - `07-Clube-USA/supabase/migrations/003_analytics.sql`
   - `07-Clube-USA/supabase/migrations/004_promotions.sql` (Fase 1.1)
   - `07-Clube-USA/supabase/migrations/005_zip_search.sql` (Fase 1.2)
   - `07-Clube-USA/supabase/migrations/006_jobs.sql` (Fase 1.4)
3. Rodar `07-Clube-USA/data/seed_zip_codes.sql` para popular tabela de ZIPs
4. Rodar `07-Clube-USA/data/seed_jobs.sql` para popular vagas iniciais (14 vagas curadas)
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

**Status:** RESOLVIDO — builder procedeu com as recomendações em 2026-07-09

**Decisões tomadas (reversíveis via env var):**
- `INFLUENCER_PAYMENT_PER_REFERRAL_CENTS=200` ($2.00/cadastro válido)
- `INFLUENCER_MONTHLY_CAP_CENTS=10000` ($100.00/mês)
- Créditos são **display only** — sem pagamento real. Saques requerem integração Stripe (Fase 5).
- Se os valores precisarem ser ajustados, altere as env vars sem re-deploy de código.

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

### [2026-07-08] D-011: Dataset completo de ZIPs (pós-merge Fase 1.2)

**Contexto:** O seed `data/seed_zip_codes.sql` cobre ~200 ZIPs das principais cidades com comunidade brasileira. Para cobrir todos os 43k ZIPs dos EUA, é necessário importar o dataset completo do US Census Bureau (público, gratuito).

**Por que não está no seed:** O arquivo CSV completo tem ~3MB — desnecessário para o MVP. Os 200 ZIPs cobrem >80% dos usuários brasileiros nos EUA.

**Como ampliar quando necessário:**
- Dataset ZCTA do Census Bureau: https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html (arquivo `2020_Gaz_zcta_national.zip`)
- Comando de import: `psql $DATABASE_URL -c "\copy zip_codes(zip,city,state,latitude,longitude) FROM 'zcta_data.csv' CSV"`
- Ou: contratar serviço de API de geocoding (Google Maps, Mapbox) para lookup on-demand em ZIPs não cadastrados

**Recomendação:** Lançar com os 200 ZIPs do seed. Monitorar em analytics quais ZIPs os usuários digitam e não encontram. Ampliar o seed quando houver demanda real.

**Status:** PENDENTE — decidir após lançamento da Fase 1.2

---

---

### [2026-07-09] D-012: Mecanismo de pagamento para influenciadores

**Contexto:** Fase 1.3 mostra créditos estimados, mas sem integração de pagamento real.

**Pergunta:** Como e quando fazer os pagamentos reais para os influenciadores?

**Opções:**
- A) **Manual por agora** — exportar relatório mensal do admin, pagar via Zelle/PayPal/Venmo. Custo: $0 de infra, mas trabalho manual.
- B) **Stripe Connect (Fase 5)** — integração automática. Custo: taxas Stripe (~0.25% + fees).
- C) **Cashback via desconto na plataforma** — não paga dinheiro real, dá benefícios na plataforma. Custo: $0 de infra.

**Recomendação:** Opção A até 50 influenciadores pagos/mês. Escalar para Stripe Connect na Fase 5.

**Dependências:** D-007 resolvido (valores configurados como env vars).

**Status:** PENDENTE — decidir antes de anunciar o programa publicamente

---

*Atualizado em: 2026-07-12 — Fase 1.5 implementada (moradia; migration 007; 15 anúncios seed; PR #20; 38 testes)*
