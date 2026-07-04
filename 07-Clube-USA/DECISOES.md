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

### [2026-07-03] Configuração do projeto Supabase (BLOQUEANTE para deploy do 0.1)

**Contexto:** A Fase 0.1 está com o código completo (backend FastAPI + frontend HTML + migration SQL). Para rodar o sistema, o projeto precisa de um projeto Supabase real com as credenciais configuradas.

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA? Se não, qual é o plano para criá-lo?

**O que é preciso fazer (ação do dono):**

1. **Criar projeto no Supabase** (https://supabase.com) — plano gratuito serve para os primeiros 1.000 usuários.

2. **Rodar a migration** no SQL Editor do Supabase:
   - Copiar e executar o conteúdo de `07-Clube-USA/supabase/migrations/001_profiles.sql`

3. **Coletar as credenciais** do painel (Settings > API):
   - `SUPABASE_URL` (ex: `https://abcxyz.supabase.co`)
   - `SUPABASE_SERVICE_ROLE_KEY` (key secreta, não a anon key)
   - `SUPABASE_JWT_SECRET` (Settings > API > JWT Secret)

4. **Configurar email confirmation** (Authentication > URL Configuration):
   - Site URL: URL onde o frontend ficará hospedado
   - Redirect URL permitida: `https://seusite.com/confirm.html`

5. **Criar o `.env`** na pasta `07-Clube-USA/backend/` baseado no `.env.example`

**Opções de hospedagem do backend (para você decidir depois):**
- **Railway** (recomendado para começar): ~$5/mês, deploy via GitHub, simples
- **Render**: plano grátis com cold start de 50s (ruim para UX), pago ~$7/mês sem cold start
- **Fly.io**: mais controle, curva maior

**Opções de hospedagem do frontend (HTML estático):**
- **GitHub Pages**: grátis, integrado ao repo — recomendado para começar
- **Vercel/Netlify**: grátis, mais recursos (redirects, edge)

**Recomendação:** Supabase gratuito + Railway $5/mês + GitHub Pages grátis = ~$5/mês total para os primeiros 1.000 usuários. Baixo risco, reversível, sem lock-in pesado.

**Status:** PENDENTE

---

### [2026-07-03] Provedor de email para confirmação de cadastro

**Contexto:** Supabase inclui envio de email nativo (via Inbucket em dev, via SMTP externo em prod). O plano gratuito do Supabase tem limite de 3 emails/hora. Para produção com volume real isso é insuficiente.

**Pergunta:** Qual provedor de email transacional usar para envio de confirmação de cadastro?

**Opções:**
- **Supabase built-in (Resend)**: Supabase integra nativamente com Resend; plano gratuito do Resend = 3.000 emails/mês. Pros: zero config extra. Contras: limitado.
- **Resend.com direto**: $0 até 3.000/mês, depois $20/mês para 50.000. API simples. Pros: escala, boa reputação. Recomendado.
- **SendGrid**: mais complexo, free tier menor hoje. Não recomendado para começar.
- **AWS SES**: baratíssimo em escala ($0,10/1.000 emails), mas precisa verificar domínio e tem processo de saída de sandbox. Endgame para 100k+ usuários.

**Recomendação:** Começar com Resend integrado via Supabase (Settings > Auth > SMTP). Grátis até 3.000/mês, suficiente para os primeiros meses. Migrar para SES quando ultrapassar 10k usuários/mês.

**Status:** PENDENTE

---

### [2026-07-03] Domínio do Clube USA

**Contexto:** Para configurar CORS, email de confirmação e identidade da marca, precisamos de um domínio.

**Pergunta:** Você já tem um domínio para o Clube USA? (ex: clubeusa.com, clube.us, etc.)

**Opções:**
- Registrar `clubeusa.com` (~$12/ano no Namecheap/Cloudflare Registrar) — recomendado
- Usar subdomínio temporário do Railway/Vercel enquanto decide

**Recomendação:** Registrar o domínio antes do lançamento. Cloudflare Registrar tem os menores preços e já inclui proteção DDoS/CDN grátis. Importante para credibilidade com os primeiros usuários.

**Status:** PENDENTE

---

---

### [2026-07-04] Definição final de "ação real" para cadastro válido (Fase 1.3)

**Contexto:** A Fase 0.4 implementou `is_valid_registration()` com critério provisório: email confirmado + ZIP preenchido. ZIP é coletado no cadastro e é um sinal fraco — qualquer um pode inventar um ZIP. Quando a Fase 1.3 (pagamento de influenciadores por cadastro válido) for lançada, precisamos de critério mais robusto.

**Pergunta:** O que deve contar como "ação real" para validar um cadastro para fins de pagamento de influenciadores?

**Opções:**

- **Opção A — ZIP preenchido (critério atual, provisório):** Manter. Fácil de fraudar. Zero fricção.
  - *Pros:* Simples, zero fricção.
  - *Contras:* Influenciadores podem criar contas em massa com ZIPs fictícios e custo pode disparar.

- **Opção B — Só email confirmado:** Exigir apenas que o email seja confirmado. Mais robusto que ZIP.
  - *Pros:* Sinal mais forte (exige caixa de email real). Já verificado pelo Supabase Auth. Zero custo.
  - *Contras:* Ainda possível criar contas bulk com emails comprados.

- **Opção C — Email confirmado + >=1 interação na plataforma (após Phase 1.1):** Visualizar/salvar >=1 promoção.
  - *Pros:* Sinal de engajamento genuíno. Muito mais difícil de fraudar em massa.
  - *Contras:* Requer Phase 1.1 pronto. Mais fricção para usuários reais.

- **Opção D — Email confirmado + telefone verificado (SMS OTP):** Máximo anti-fraude.
  - *Pros:* Padrão da indústria, muito difícil fraudar em escala.
  - *Contras:* Custo (~$0.01/SMS via Twilio). Exclui usuários sem telefone americano. Alta fricção.

**Recomendação:** Migrar para **Opção B** agora (só email confirmado é mais defensável que ZIP), depois **Opção C** quando Phase 1.1 lançar. Opção D somente se fraude for detectada em escala. A mudança é de 1 linha em `validation/service.py`.

**Status:** PENDENTE — decidir antes de lançar Fase 1.3

---

### [2026-07-04] Valor por cadastro válido e teto orçamentário — Programa de Influenciadores (Fase 1.3)

**Contexto:** A Fase 1.3 paga influenciadores por cadastro válido com teto orçamentário. Precisamos definir o valor e o teto antes de implementar o sistema de pagamento e os selos (Parceiro 50 / Embaixador 250 / Hall da Fama 1000).

**Pergunta:** Qual o valor por cadastro válido e qual o teto mensal?

**Opções:**

- $1/cadastro, teto $50/mês: Conservador, baixo risco, testa o canal.
- $2/cadastro, teto $100/mês: Razoável para beta. Incentiva, mas controla gasto.
- $3–5/cadastro, teto $500/mês: Competitivo, atrai influenciadores maiores.
- Sem teto: Risco financeiro aberto. Não recomendado sem validação de fraude robusta.

**Recomendação:** Começar com **$2/cadastro válido, teto $100/mês por influenciador** na fase beta. Subir quando validar anti-fraude e ROI. Nunca sem teto.

**Status:** PENDENTE — aprovação do dono + orçamento definido antes da Fase 1.3

---

*Atualizado em: 2026-07-04 (Fase 0 completa; decisões pendentes para Fase 1.3)*
