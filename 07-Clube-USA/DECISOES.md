# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do builder.
> O builder NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o builder travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚡ AÇÃO IMEDIATA NECESSÁRIA — atualizado 2026-07-09

**Situação crítica:** 16 PRs abertos, nenhum merged. A Fase 0 está codificada e testada (66 testes passando) mas o ROADMAP no main ainda mostra `[ ]` porque este PR (#10) não foi merged. Cada nova rodada do builder cria PRs duplicados. O ROADMAP do main é a raiz do problema.

**Impacto se não agir:** O builder vai continuar abrindo PRs duplicados toda rodada. Já foram criados 3 duplicatas de 0.1 desde 2026-07-07 (#11, #13, #15).

**Plano de ação (60 minutos do seu tempo):**
1. **Fechar PRs redundantes:** #1, #6, #7, #8, #11, #13, #15 (todos duplicatas de 0.1)
2. **Mergear ESTE PR #10 primeiro** — corrige o YAML do workflow e atualiza o ROADMAP no main. Resolve a causa raiz dos duplicados.
3. **Resolver D-002** (criar projeto Supabase — grátis, ~10 min) — desbloqueia deploy
4. **Mergear em ordem:** PR #2 → #3 → #4 → #5 → #9 (Fase 0 completa)
5. **Responder D-008** (produto para 1.1 Promoções) — uma resposta de 2 minutos desbloqueia semanas de trabalho do builder
6. **Avaliar PRs #12, #14, #16** (Fase 1.1, 1.2, 1.3) — ver D-010

**Resumo de PRs:**
| PR | Ação | Prioridade |
|----|------|-----------|
| **#10** (este) | Mergear 1º — corrige workflow + ROADMAP | 🔴 Urgente |
| **#2** | Mergear 2º — Fase 0.1 auth | 🔴 Urgente |
| **#3** | Mergear 3º — Fase 0.2 referral | 🔴 Urgente |
| **#4** | Mergear 4º — Fase 0.3 analytics | 🔴 Urgente |
| **#5** | Mergear 5º — Fase 0.4 anti-fraude | 🔴 Urgente |
| **#9** | Mergear 6º — security polish | 🟡 Normal |
| #12 | Avaliar — Fase 1.1 Promoções (ver D-010) | 🟡 Depois |
| #14 | Avaliar — Fase 1.2 Busca ZIP (ver D-010) | 🟡 Depois |
| #16 | Avaliar — Fase 1.3 Influenciadores (ver D-010) | 🟡 Depois |
| #1, #6, #7, #8, #11, #13, #15 | **Fechar** — duplicatas | ❌ Fechar |

---

## Decisões Pendentes

---

### [2026-07-03 → atualizado 2026-07-09] D-001: Merge order dos PRs

**Contexto:** Existem agora 16 PRs abertos (era 9 em 2026-07-07). 7 são duplicatas de 0.1; 3 são Fase 1.x construídos sem Fase 0 merged.

**Ação recomendada:**
1. Fechar duplicatas: #1, #6, #7, #8, #11, #13, #15
2. Review e merge na ordem: **#10 → #2 → #3 → #4 → #5 → #9**
3. Avaliar #12, #14, #16 (ver D-010)

**Status:** PENDENTE — atenção redobrada, situação piorou desde 2026-07-07

---

### [2026-07-03] D-002: Configuração do projeto Supabase (BLOQUEANTE)

**Contexto:** A Fase 0 (auth, referral, analytics, validação) usa Supabase como banco. Código pronto, mas não tem banco para rodar.

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

**Contexto:** A Fase 1.1 (PROMOÇÕES/ACHADOS = carro-chefe da plataforma) precisa de respostas antes do builder implementar. Sem clareza de produto, o código vai na direção errada.

**Perguntas:**

1. **Quem cria as promoções no MVP?**
   - Opção A: Só o admin (você), via painel ou seed manual. *Recomendado no MVP — garante curadoria, sem overhead de UX para empresas.*
   - Opção B: Empresas cadastradas criam as próprias (self-service). Requer Fase 2.1 antes.

2. **Quais campos mínimos por promoção?**
   - Sugestão: título, descrição curta, loja/empresa, categoria, ZIP do estabelecimento, data de expiração (opcional), URL ou código do desconto (opcional), imagem (opcional).
   - Confirma ou ajusta?

3. **Mecanismo de urgência?**
   - Opção A: Campo `expires_at` — expira automaticamente. Simples. *Recomendado.*
   - Opção B: Campo `quantity` — "restam 10 vagas". Mais complexo, permite fraude.

4. **Modelo geográfico?**
   - Opção A: Promoções nacionais (sem filtro de ZIP na Fase 1.1) + filtro de ZIP chega na 1.2.
   - Opção B: ZIP obrigatório desde o início. Consistente com 1.2, mas exige que admin saiba o ZIP de cada promoção.
   - *Recomendado: A — nacional primeiro, filtro de ZIP na 1.2.*

5. **Como usuários descobrem promoções?**
   - Lista cronológica (mais recente primeiro) com paginação. Zero algoritmo. *Recomendado para MVP — implementa em 1 dia.*

**Recomendação geral:** Admin cria promoções (Opção A), campos mínimos da sugestão, urgência por `expires_at`, nacional primeiro, lista cronológica.

**Status:** PENDENTE — confirme suas escolhas para o builder iniciar 1.1

---

### [2026-07-07] D-009: Workflow YAML estava quebrado (fix incluído neste PR)

**Contexto:** O arquivo `.github/workflows/clubeusa-builder.yml` inicial tinha indentação completamente malformada — o YAML não era válido e o builder nunca rodou no agendamento (3x ao dia). Toda rodada era manual ou via interface web.

**O que foi feito:** O workflow foi reescrito com YAML válido e prompt completo (incluindo ROADMAP, regras de segurança e como trabalhar). Este fix está incluído neste PR (claude/fix-workflow-yaml-e-docs-main).

**Ação necessária:** Apenas mergear este PR. Após o merge, o builder vai rodar automaticamente 3x/dia nos horários configurados (10h, 16h, 22h UTC = 6h, 12h, 18h ET) sem intervenção manual.

**Status:** RESOLVIDO — aguarda merge deste PR

---

---

### [2026-07-09] D-010: PRs de Fase 1 construídos antes de Fase 0 ser deployed

**Contexto:** Entre 2026-07-07 e 2026-07-09, o builder ignorou o bloqueio em D-008 e construiu PRs de Fase 1:
- **PR #12** (`claude/fase-1.1-promocoes`): Fase 1.1 — PROMOÇÕES/ACHADOS
- **PR #14** (`claude/fase-1.2-busca-zip`): Fase 1.2 — busca por ZIP
- **PR #16** (`claude/fase-1.3-influenciadores`): Fase 1.3 — programa de influenciadores

**Problema:** Esses PRs foram construídos sem a Fase 0 deployed/testada, sem as decisões de produto (D-008 para 1.1) e sem orçamento definido (D-007 para 1.3). Podem ter escolhas de produto incorretas.

**Opções:**
- **A — Manter e revisar:** Os PRs podem estar tecnicamente corretos mesmo sem deploy de Fase 0. Revisar se as escolhas de produto fazem sentido. Ajustar o que precisar. *Mais rápido.*
- **B — Descartar e rebuild depois:** Fechar #12, #14, #16 agora. Builder reconstrói depois com D-008 respondido. *Mais correto, mas perde o trabalho feito.*
- **C — Manter mas não mergear até Fase 0 estar em produção:** Não fechar, não mergear ainda. Revisar quando Fase 0 for ao ar. *Recomendado — não perde trabalho, não apressa o processo.*

**Recomendação:** Opção C. Manter PRs #12, #14, #16 abertos para revisão futura, mas NÃO mergear antes de Fase 0 estar deployed e D-008 respondido. Revisar D-008 respondendo as 5 perguntas de produto — o builder adapta o código se necessário.

**Impacto se D-008 não for respondido:** Builder vai continuar não sabendo como implementar 1.1 corretamente e pode criar mais PRs inconsistentes.

**Status:** PENDENTE — decida A, B ou C e responda D-008

---

*Atualizado em: 2026-07-09*
