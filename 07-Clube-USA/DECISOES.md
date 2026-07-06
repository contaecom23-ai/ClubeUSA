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

### [2026-07-03] D-001: Merge order dos PRs de Fase 0 (ação imediata)

**Contexto:** Existem 8 PRs abertos. 4 formam a cadeia completa da Fase 0 (64 testes passando); 3 são implementações redundantes que podem ser fechadas; 1 é sync de docs.

**Ação recomendada:**
1. Fechar PR #1 (supersedido pelo #2, mais antigo)
2. Fechar PR #6 (implementação alternativa da 0.1, supersedida)
3. Fechar PR #7 (implementação mais recente da 0.1, mas isolada — a cadeia #2-5 cobre tudo)
4. Fazer review e merge em ordem: **PR #8 → PR #2 → PR #3 → PR #4 → PR #5**
5. Após merge do #5: PR de polimento de segurança (`claude/fase-0-security-polish`) pode ser mergeado também.

**Risco:** Baixo. Fechar redundantes é reversível. Merge em ordem evita conflito.

**Status:** PENDENTE

---

### [2026-07-03] D-002: Configuração do projeto Supabase (BLOQUEANTE para deploy)

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
   - Redirect URL permitida: `https://seusite.com/confirm.html`

**Custo:** $0 no plano gratuito (até 500MB banco, 50k auth users)

**Status:** PENDENTE

---

### [2026-07-03] D-003: Provedor de email transacional

**Contexto:** Supabase gratuito limita a 3 emails/hora — inaceitável para lançamento. Precisamos de SMTP externo configurado no Supabase.

**Opções:**
- **Resend.com** (recomendado): $0 até 3.000 emails/mês, integra direto no Supabase (Settings > Auth > SMTP). Suficiente para os primeiros 6-12 meses.
- **AWS SES**: $0,10/1.000 emails (baratíssimo em escala), mas tem processo de saída de sandbox. Endgame para 100k+ usuários/mês.

**Recomendação:** Resend agora → migrar para SES quando ultrapassar 3.000 emails/mês.

**Custo:** $0 até 3.000/mês (Resend free)

**Status:** PENDENTE

---

### [2026-07-03] D-004: Hospedagem do backend FastAPI

**Opções:**
- **Railway** (recomendado): ~$5/mês, deploy via GitHub em 5 minutos, zero cold start.
- **Render**: plano grátis tem cold start de 50s (péssimo para UX), pago $7/mês sem cold start.
- **Fly.io**: mais controle, curva de aprendizado maior. Vale quando escalar para 10k+.

**Recomendação:** Railway $5/mês para começar. Reversível quando necessário.

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

**Contexto:** Fase 0.4 implementou `is_valid_registration()` com critério provisório: email confirmado + ZIP preenchido. ZIP é um sinal fraco. Quando a Fase 1.3 (pagamento de influenciadores por cadastro válido) for lançada, precisa de critério mais robusto para evitar fraude.

**Opções:**
- **A — ZIP preenchido (atual, provisório):** Fácil de fraudar. Não recomendado para 1.3.
- **B — Só email confirmado:** Sinal mais forte. Mudança de 1 linha. *Recomendado como próximo passo imediato.*
- **C — Email confirmado + ≥1 interação na plataforma:** Visualizar/salvar ≥1 promoção. Muito mais difícil de fraudar. Requer Fase 1.1 pronta. *Recomendado para quando 1.1 lançar.*
- **D — Email + SMS OTP:** Máximo anti-fraude. Custo ~$0.01/SMS, alta fricção.

**Recomendação:** Migrar para B agora (1 linha de código), depois C quando Fase 1.1 lançar.

**Status:** PENDENTE — decidir antes de lançar Fase 1.3

---

### [2026-07-04] D-007: Valor por cadastro válido e teto orçamentário — Programa de Influenciadores (pré-Fase 1.3)

**Contexto:** A Fase 1.3 paga influenciadores por cadastro válido com teto orçamentário. Precisamos de números reais antes de implementar o sistema de pagamento e os selos (Parceiro 50 / Embaixador 250 / Hall da Fama 1000).

**Opções:**
- $1/cadastro, teto $50/mês: Conservador, baixo risco.
- $2/cadastro, teto $100/mês: Razoável para beta. *Recomendado.*
- $3–5/cadastro, teto $500/mês: Competitivo, alto risco de fraude sem anti-fraude robusto.
- Sem teto: Não. Risco financeiro aberto sem validação prévia.

**Recomendação:** $2/cadastro válido, teto $100/mês por influenciador na fase beta.

**Status:** PENDENTE — aprovação do dono + orçamento definido antes da Fase 1.3

---

### [2026-07-06] D-008: Perguntas de produto para iniciar Fase 1.1 — PROMOÇÕES/ACHADOS

**Contexto:** Fase 1.1 é o carro-chefe da plataforma. Código pode começar quando infra estiver pronta (D-002 a D-005 resolvidos), mas antes precisamos dessas decisões de produto para implementar certo da primeira vez.

**Perguntas (responda todas antes do Claude iniciar a Fase 1.1):**

**1. Quem cria as promoções?**
- Só admins (curadoria total) — mais controle, menos escala
- Empresas com conta premium (self-service) — mais escala, risco de spam
- Ambos (admin cura, empresas submetem para aprovação) — *recomendado*

**2. Quais campos uma promoção tem?**
- Título, descrição, preço original, preço com desconto, prazo de validade, link externo, ZIP alvo, categoria — é isso ou falta algo?
- Há upload de imagem? (adiciona complexidade — storage no Supabase ou S3)
- Há cupom/código de desconto?

**3. Como funciona a "urgência"?**
- Badge automático quando falta < X horas para expirar
- Campo manual "destaque/urgente" marcado pelo admin
- Quantidade limitada ("só 50 disponíveis") — requer controle de estoque

**4. Modelo de dados geográfico:**
- Promoção com ZIP único vs. lista de ZIPs vs. raio em milhas de um ponto central
- Promoção nacional (sem filtro geográfico) é caso válido?

**5. Descoberta inicial (pré-Fase 1.2):**
- Feed cronológico simples (mais novo primeiro)
- Feed curado pelo admin (posição manual)
- Ambos com aba separada

**Recomendação do builder:**
- MVP mínimo: admin cria promoções via painel, campos simples (sem imagem por enquanto), badge de urgência automático por prazo, ZIP único, feed cronológico. Imagem e self-service de empresas entram na Fase 2.1.
- Não implementar filtro geográfico avançado agora (isso é Fase 1.2).

**Status:** PENDENTE — responder antes que o builder inicie a Fase 1.1

---

*Atualizado em: 2026-07-06 — polimento de segurança (D-008 adicionado; password + security headers no branch claude/fase-0-security-polish)*
