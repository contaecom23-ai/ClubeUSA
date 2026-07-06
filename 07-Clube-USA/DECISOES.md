# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação.
> O builder NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o builder travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚡ AÇÃO IMEDIATA NECESSÁRIA (bloqueante para avançar)

A Fase 0 está **codificada e testada** (64 testes passando), mas não pode ser deployada sem as decisões abaixo. Enquanto isso não for resolvido, o builder não tem como avançar para Fase 1 de forma útil.

**Resumo do que precisa acontecer (na ordem):**
1. Você resolve as decisões de infra abaixo (Supabase + email + hosting + domínio)
2. Faz o merge dos PRs em ordem: #2 → #3 → #4 → #5
3. Builder implementa Fase 1.1 (Promoções/Achados) sobre base deployada

---

## Decisões Pendentes

---

### [2026-07-03] D-001: Merge order dos PRs de Fase 0

**Contexto:** Existem 7 PRs abertos. 4 formam a cadeia completa da Fase 0; 3 são implementações redundantes que podem ser fechadas.

**Pergunta:** Você quer fazer o merge da cadeia principal (PRs #2→#3→#4→#5) e fechar os redundantes (#1, #6, #7)?

**Ação recomendada:**
1. Fechar PR #1 (supersedido pelo #2, mais antigo)
2. Fechar PR #6 (implementação alternativa da 0.1, supersedida)
3. Fechar PR #7 (implementação mais recente da 0.1, mas isolada — a cadeia #2-5 cobre tudo e tem mais funcionalidade)
4. Fazer review e merge na ordem: **PR #2 → PR #3 → PR #4 → PR #5**

**Risco:** Baixo. Os PRs redundantes não tem nada que a cadeia #2-5 não tenha. Fechar é reversível (pode reabrir).

**Status:** PENDENTE

---

### [2026-07-03] D-002: Configuração do projeto Supabase (BLOQUEANTE)

**Contexto:** A Fase 0 (auth, referral, analytics, validação) usa Supabase como banco. Código pronto, mas não tem banco para rodar.

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA?

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

**Pergunta:** Qual provedor de email usar para confirmação de cadastro?

**Opções:**
- **Resend.com** (recomendado): $0 até 3.000 emails/mês, API simples, integra direto no Supabase (Settings > Auth > SMTP). Para os primeiros 6-12 meses é suficiente.
- **SendGrid**: free tier menor, mais complexo. Não recomendado para começar.
- **AWS SES**: $0,10/1.000 emails (baratíssimo em escala), mas tem processo de saída de sandbox e setup mais trabalhoso. Endgame para 100k+ usuários/mês.

**Recomendação:** Resend agora → migrar para SES quando ultrapassar 3.000 emails/mês.

**Custo:** $0 até 3.000/mês (Resend free)

**Status:** PENDENTE

---

### [2026-07-03] D-004: Hospedagem do backend FastAPI

**Contexto:** O backend é uma API FastAPI (Python). Precisa de deploy em alguma plataforma cloud.

**Pergunta:** Onde hospedar o backend?

**Opções:**
- **Railway** (recomendado): ~$5/mês, deploy via GitHub em 5 minutos, zero cold start, simples. Certo para os primeiros 1.000–10.000 usuários.
- **Render**: plano grátis tem cold start de 50s (péssimo para UX), pago $7/mês sem cold start.
- **Fly.io**: mais controle, curva de aprendizado maior. Vale quando escalar para 10k+.
- **VPS (DigitalOcean/Hetzner)**: mais barato em escala, mas você gerencia o servidor. Não recomendado para começar.

**Recomendação:** Railway $5/mês para começar. Reversível quando necessário.

**Custo:** ~$5/mês

**Status:** PENDENTE

---

### [2026-07-03] D-005: Domínio do Clube USA

**Contexto:** CORS, links de email de confirmação e credibilidade da marca dependem de um domínio real.

**Pergunta:** Você já tem um domínio para o Clube USA? (ex: clubeusa.com, clube.us, etc.)

**Opções:**
- Registrar `clubeusa.com` (~$12/ano no Cloudflare Registrar) — recomendado
- Usar subdomínio temporário do Railway/Vercel enquanto decide (gratuito, mas links de email ficam feios)

**Recomendação:** Registrar domínio antes do lançamento. Cloudflare Registrar tem os menores preços e inclui proteção DDoS/CDN grátis. Credibilidade essencial para os primeiros 1.000 usuários.

**Custo:** ~$12/ano

**Status:** PENDENTE

---

### [2026-07-04] D-006: Definição final de "ação real" para cadastro válido (pré-Fase 1.3)

**Contexto:** Fase 0.4 implementou `is_valid_registration()` com critério provisório: email confirmado + ZIP preenchido. ZIP é um sinal fraco — qualquer um pode inventar um ZIP. Quando a Fase 1.3 (pagamento de influenciadores por cadastro válido) for lançada, precisa de critério mais robusto para evitar fraude.

**Pergunta:** O que deve contar como "ação real" para fins de pagamento de influenciadores?

**Opções:**
- **A — ZIP preenchido (atual, provisório):** Fácil de fraudar. Zero fricção. Não recomendado para 1.3.
- **B — Só email confirmado:** Sinal mais forte (exige caixa de email real). Mudança de 1 linha. *Recomendado como próximo passo imediato.*
- **C — Email confirmado + ≥1 interação na plataforma:** Visualizar/salvar ≥1 promoção. Muito mais difícil de fraudar. Requer Fase 1.1 pronta. *Recomendado para quando 1.1 lançar.*
- **D — Email + SMS OTP:** Máximo anti-fraude. Custo ~$0.01/SMS, alta fricção, exclui usuários sem telefone americano. Só se fraude em escala for detectada.

**Recomendação:** Migrar para B agora (1 linha de código), depois C quando Fase 1.1 lançar.

**Status:** PENDENTE — decidir antes de lançar Fase 1.3

---

### [2026-07-04] D-007: Valor por cadastro válido e teto orçamentário — Programa de Influenciadores (pré-Fase 1.3)

**Contexto:** A Fase 1.3 paga influenciadores por cadastro válido com teto orçamentário. Precisamos de números reais antes de implementar o sistema de pagamento e os selos (Parceiro 50 / Embaixador 250 / Hall da Fama 1000).

**Pergunta:** Qual o valor por cadastro válido e qual o teto mensal por influenciador?

**Opções:**
- $1/cadastro, teto $50/mês: Conservador, baixo risco, testa o canal.
- $2/cadastro, teto $100/mês: Razoável para beta. Incentiva sem expor muito. *Recomendado.*
- $3–5/cadastro, teto $500/mês: Competitivo, atrai influenciadores maiores. Alto risco de fraude sem anti-fraude robusto.
- Sem teto: Não. Risco financeiro aberto sem validação prévia.

**Recomendação:** $2/cadastro válido, teto $100/mês por influenciador na fase beta. Subir quando validar ROI.

**Status:** PENDENTE — aprovação do dono + orçamento definido antes da Fase 1.3

---

*Atualizado em: 2026-07-06 — consolidando todas as decisões pendentes dos PRs abertos no main*
