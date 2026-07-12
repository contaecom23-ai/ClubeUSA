# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do builder.
> O builder NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o builder travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 ATENÇÃO IMEDIATA NECESSÁRIA — atualizado 2026-07-12

**Situação crítica:** 20 PRs abertos, nenhum merged. A cada rodada (3x/dia) que passa sem o PR #10 ser merged, o builder cria 2 novos PRs duplicados de Fase 0.1. Desde a última atualização (2026-07-09), foram criados PRs #17, #18 (mais duplicatas de 0.1), #19 (Fase 1.4 empregos) e #20 (Fase 1.5 moradia).

**Por que isso acontece:** O ROADMAP no main mostra tudo como `[ ]`. O builder lê isso, acha que nada foi feito e recomeça do zero. A única correção é mergear PR #10.

**Custo real de não agir:** 2 novos PRs por rodada × 3 rodadas/dia = ~6 PRs/dia acumulando lixo no repositório.

**Plano de ação (~60 minutos do seu tempo):**

**Passo 1 — Limpar duplicatas (5 min):** Fechar PRs #1, #6, #7, #8, #11, #13, #15, #17, #18 (todos duplicatas de Fase 0.1).

**Passo 2 — Mergear PR #10 (5 min):** Este PR corrige o ROADMAP e o workflow. É a ação mais impactante — para o ciclo de duplicatas imediatamente.

**Passo 3 — Configurar Supabase (10 min):** Ver D-002 abaixo. Grátis. Desbloqueia deploy da Fase 0.

**Passo 4 — Mergear Fase 0 em ordem (20 min revisão):** PR #2 → #3 → #4 → #5 → #9.

**Passo 5 — Responder D-008 (5 min):** 5 perguntas rápidas de produto para Fase 1.1. Uma resposta sua desbloqueia semanas de trabalho.

**Passo 6 — Avaliar PRs de Fase 1 (15 min):** Ver D-010 e D-011.

---

## Tabela de PRs (estado atual 2026-07-12)

| PR | Ação | Prioridade |
|----|------|------------|
| **#10** (este) | Mergear 1º — corrige ROADMAP + workflow | 🔴 Urgente |
| **#2** | Mergear 2º — Fase 0.1 auth | 🔴 Urgente |
| **#3** | Mergear 3º — Fase 0.2 referral | 🔴 Urgente |
| **#4** | Mergear 4º — Fase 0.3 analytics | 🔴 Urgente |
| **#5** | Mergear 5º — Fase 0.4 anti-fraude | 🔴 Urgente |
| **#9** | Mergear 6º — security polish | 🟡 Normal |
| #12 | Avaliar — Fase 1.1 Promoções (ver D-008, D-010) | 🟡 Depois |
| #14 | Avaliar — Fase 1.2 Busca ZIP (ver D-010) | 🟡 Depois |
| #16 | Avaliar — Fase 1.3 Influenciadores (ver D-007, D-010) | 🟡 Depois |
| #19 | Avaliar — Fase 1.4 Empregos (ver D-011) | 🟡 Depois |
| #20 | Avaliar — Fase 1.5 Moradia (ver D-011) | 🟡 Depois |
| #1, #6, #7, #8, #11, #13, #15, #17, #18 | **Fechar** — duplicatas de Fase 0.1 | ❌ Fechar |

---

## Decisões Pendentes

---

### [2026-07-03 → atualizado 2026-07-12] D-001: Merge order dos PRs

**Contexto:** 20 PRs abertos. 9 são duplicatas de 0.1 (criadas porque o ROADMAP do main ainda mostra `[ ]`). 5 são Fase 1.x construídas sem Fase 0 merged. Situação piora a cada rodada.

**Ação recomendada (em ordem):**
1. Fechar duplicatas: #1, #6, #7, #8, #11, #13, #15, #17, #18
2. Mergear: **#10 → #2 → #3 → #4 → #5 → #9**
3. Avaliar: #12, #14, #16, #19, #20 (ver D-008, D-010, D-011)

**Status:** PENDENTE — situação piorou desde 2026-07-09 (eram 16 PRs, agora são 20)

---

### [2026-07-03] D-002: Configuração do projeto Supabase (BLOQUEANTE)

**Contexto:** A Fase 0 (auth, referral, analytics, validação) usa Supabase como banco. Código pronto e testado, mas sem banco configurado não tem como deployar.

**O que fazer:**
1. Criar projeto em https://supabase.com — plano gratuito cobre os primeiros 1.000 usuários
2. Rodar as migrations em ordem no SQL Editor do Supabase:
   - `07-Clube-USA/supabase/migrations/001_profiles.sql`
   - `07-Clube-USA/supabase/migrations/002_referrals.sql`
   - `07-Clube-USA/supabase/migrations/003_analytics.sql`
3. Coletar as credenciais (Settings > API):
   - `SUPABASE_URL` (ex: `https://abcxyz.supabase.co`)
   - `SUPABASE_SERVICE_ROLE_KEY` (key secreta — não a anon key)
   - `SUPABASE_JWT_SECRET` (Settings > API > JWT Secret)
4. Configurar email confirmation (Authentication > URL Configuration):
   - Site URL: URL do frontend
   - Redirect URL: `https://seusite.com/confirm.html`

**Custo:** $0 no plano gratuito (até 500MB banco, 50k auth users)

**Status:** PENDENTE

---

### [2026-07-03] D-003: Provedor de email transacional

**Contexto:** Supabase gratuito limita a 3 emails/hora — inaceitável para lançamento. Precisamos de SMTP externo.

**Opções:**
- **Resend.com** (recomendado): $0 até 3.000 emails/mês, integra direto no Supabase (Settings > Auth > SMTP). Suficiente para os primeiros 6–12 meses.
- **SendGrid**: free tier menor, mais complexo.
- **AWS SES**: $0,10/1.000 emails, exige aprovação de saída de sandbox. Endgame para 100k+ usuários.

**Recomendação:** Resend agora → migrar para SES quando ultrapassar 3.000 emails/mês.

**Custo:** $0 até 3.000/mês (Resend free)

**Status:** PENDENTE

---

### [2026-07-03] D-004: Hospedagem do backend FastAPI

**Contexto:** O backend é uma API FastAPI (Python). Precisa de deploy em alguma plataforma cloud.

**Opções:**
- **Railway** (recomendado): ~$5/mês, deploy via GitHub em 5 minutos, zero cold start. Certo para os primeiros 1.000–10.000 usuários.
- **Render**: plano grátis tem cold start de 50s (péssimo para UX), pago $7/mês sem cold start.
- **Fly.io**: mais controle, curva de aprendizado maior. Vale quando escalar para 10k+.
- **VPS (DigitalOcean/Hetzner)**: mais barato em escala, mas você gerencia o servidor.

**Recomendação:** Railway $5/mês para começar. Reversível.

**Custo:** ~$5/mês

**Status:** PENDENTE

---

### [2026-07-03] D-005: Domínio do Clube USA

**Contexto:** CORS, links de email de confirmação e credibilidade da marca dependem de um domínio real.

**Opções:**
- Registrar `clubeusa.com` (~$12/ano no Cloudflare Registrar) — recomendado
- Usar subdomínio temporário do Railway/Vercel enquanto decide (gratuito, mas links de email ficam feios)

**Recomendação:** Registrar domínio antes do lançamento. Cloudflare Registrar tem os menores preços e inclui proteção DDoS/CDN grátis.

**Custo:** ~$12/ano

**Status:** PENDENTE

---

### [2026-07-04] D-006: Definição final de "ação real" para cadastro válido (pré-Fase 1.3)

**Contexto:** Fase 0.4 implementou critério provisório: email confirmado + ZIP preenchido. ZIP é fraco — qualquer um pode inventar. Quando Fase 1.3 (pagamento de influenciadores) lançar, precisa de critério mais robusto para evitar fraude.

**Opções:**
- **A — ZIP preenchido (atual, provisório):** Fácil de fraudar. Não recomendado para 1.3.
- **B — Só email confirmado:** Sinal mais forte. Mudança de 1 linha. *Recomendado como próximo passo imediato.*
- **C — Email confirmado + ≥1 interação na plataforma:** Visualizar/salvar ≥1 promoção. Muito mais difícil de fraudar. Requer Fase 1.1 pronta. *Recomendado para quando 1.1 lançar.*
- **D — Email + SMS OTP:** Máximo anti-fraude. Custo ~$0.01/SMS, alta fricção.

**Recomendação:** Migrar para B agora, depois C quando Fase 1.1 lançar.

**Status:** PENDENTE — decidir antes de lançar Fase 1.3

---

### [2026-07-04] D-007: Valor por cadastro válido e teto orçamentário — Programa de Influenciadores (pré-Fase 1.3)

**Contexto:** A Fase 1.3 paga influenciadores por cadastro válido com teto orçamentário. Precisamos de números reais antes de implementar o sistema de pagamento.

**Opções:**
- $1/cadastro, teto $50/mês: Conservador, baixo risco, testa o canal.
- $2/cadastro, teto $100/mês: Razoável para beta. *Recomendado.*
- $3–5/cadastro, teto $500/mês: Competitivo, alto risco de fraude sem anti-fraude robusto.
- Sem teto: Não. Risco financeiro aberto sem validação.

**Recomendação:** $2/cadastro válido, teto $100/mês por influenciador na fase beta.

**Status:** PENDENTE — aprovação do dono + orçamento antes da Fase 1.3

---

### [2026-07-06] D-008: Decisões de produto para iniciar Fase 1.1 (Promoções/Achados)

**Contexto:** A Fase 1.1 (PROMOÇÕES/ACHADOS = carro-chefe da plataforma) precisa de respostas de produto. Sem clareza, o código vai na direção errada. O PR #12 já existe mas pode precisar de ajuste dependendo das respostas.

**Perguntas (responda as 5, leva ~5 min):**

1. **Quem cria as promoções no MVP?**
   - Opção A: Só o admin (você), via painel ou seed manual. *Recomendado — curadoria garantida, sem overhead.*
   - Opção B: Empresas cadastradas criam as próprias (self-service). Requer Fase 2.1 antes.

2. **Quais campos mínimos por promoção?**
   - Sugestão: título, descrição curta, loja/empresa, categoria, ZIP do estabelecimento, data de expiração (opcional), URL ou código do desconto (opcional), imagem (opcional).
   - Confirma ou ajusta?

3. **Mecanismo de urgência?**
   - Opção A: Campo `expires_at` — expira automaticamente. Simples. *Recomendado.*
   - Opção B: Campo `quantity` — "restam 10 vagas". Mais complexo, permite fraude.

4. **Modelo geográfico?**
   - Opção A: Promoções nacionais (sem filtro de ZIP na Fase 1.1) + filtro de ZIP chega na 1.2. *Recomendado.*
   - Opção B: ZIP obrigatório desde o início.

5. **Como usuários descobrem promoções?**
   - Lista cronológica (mais recente primeiro) com paginação. Zero algoritmo. *Recomendado para MVP.*

**Status:** PENDENTE — responda para o builder ajustar PR #12 se necessário e iniciar o deploy

---

### [2026-07-07] D-009: Workflow YAML estava quebrado (fix incluído neste PR)

**Contexto:** O arquivo `.github/workflows/clubeusa-builder.yml` inicial tinha YAML malformado — o builder nunca rodou no agendamento. Toda rodada era manual.

**O que foi feito:** O workflow foi reescrito com YAML válido. Fix incluído neste PR.

**Ação necessária:** Apenas mergear este PR. Após merge, o builder roda automaticamente 3x/dia.

**Status:** RESOLVIDO — aguarda merge deste PR

---

### [2026-07-09] D-010: PRs de Fase 1.1, 1.2, 1.3 construídos antes de Fase 0 deployed

**Contexto:** PRs #12 (Fase 1.1), #14 (Fase 1.2) e #16 (Fase 1.3) foram construídos sem Fase 0 deployed e sem D-008 respondido.

**Opções:**
- **A — Manter e revisar:** Código pode estar tecnicamente correto. Ajustar se D-008 mostrar escolhas diferentes. *Mais rápido.*
- **B — Descartar:** Fechar agora, reconstruir depois com D-008 respondido. *Mais correto, perde trabalho.*
- **C — Manter mas não mergear:** Não fechar, não mergear ainda. Revisar quando Fase 0 for ao ar. *Recomendado.*

**Recomendação:** Opção C. Responda D-008 para o builder ajustar o código se necessário.

**Status:** PENDENTE

---

### [2026-07-12] D-011: PRs de Fase 1.4 e 1.5 construídos fora de ordem

**Contexto:** Entre 2026-07-09 e 2026-07-12, o builder construiu:
- **PR #19** (`claude/fase-1.4-empregos`): board de empregos com seed manual + filtro ZIP
- **PR #20** (`claude/fase-1.5-moradia`): moradia/quartos/roommates com filtro ZIP

Fases 1.4 e 1.5 foram implementadas sem: Fase 0 deployed, Fase 1.1 respondida (D-008), Fase 1.2 deployada. O código provavelmente tem qualidade razoável (o padrão dos outros PRs é bom), mas as escolhas de produto podem não refletir sua visão.

**Perguntas de produto para Fase 1.4 (Empregos):**
1. Quem posta vagas no MVP? Admin (seed manual) ou empregadores self-service?
2. Campos mínimos: título, empresa, descrição, ZIP, tipo (CLT/PJ/freelance), salário (opcional)? Confirma?
3. Vagas expiram? Por data ou por remoção manual?

**Perguntas de produto para Fase 1.5 (Moradia):**
1. Quem posta quartos/casas? Admin (seed) ou usuários self-service?
2. Campos: tipo (quarto/apartamento/casa), preço/mês, ZIP, descrição, contato. Confirma?
3. Listings expiram? Por data ou por remoção manual?

**Opções (mesmas do D-010):**
- **A — Manter e revisar:** Verificar se as escolhas batem com sua visão. Ajustar o que não bater.
- **B — Descartar:** Fechar #19 e #20, reconstruir depois com respostas.
- **C — Manter mas não mergear:** Aguardar Fase 0 deployed, responder as perguntas acima, revisar código então. *Recomendado.*

**Recomendação:** Opção C. Responda as perguntas acima quando chegar a hora. O builder não tocará nesses PRs até então.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-12*
