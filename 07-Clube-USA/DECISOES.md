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

### [2026-07-15] Qual serviço de email usar para confirmação de cadastro?

**Contexto:** A Fase 0.1 tem o serviço de email construído e plugável (via SMTP). Sem configuração, o link de confirmação é apenas logado no terminal — útil em dev, inútil em produção. Para o lançamento, precisamos de um provedor real.

**Pergunta:** Qual provedor de email configurar para os emails transacionais (confirmação de cadastro, futuramente reset de senha etc.)?

**Opções:**

- **A) Resend** (resend.com): Prós — grátis até 3k emails/mês, API moderna, domínio próprio, excelente DX. Contras — serviço externo, vendor lock-in moderado. **Recomendado para começar.**
- **B) SendGrid**: Prós — battle-tested, 100 emails/dia grátis. Contras — UI mais complexa, limite grátis menor que Resend.
- **C) Amazon SES**: Prós — muito barato em escala ($0,10/1k), ideal para 10k+ usuários. Contras — precisa de conta AWS, setup de domínio mais trabalhoso. Bom para escala, não para agora.
- **D) Mailgun**: Prós — grátis 100 emails/dia. Contras — UX inferior, sem tier gratuito permanente agora.

**Recomendação do Claude:** Opção A (Resend). Tier gratuito cobre os primeiros 1.000 usuários com folga. Setup em 10 minutos. Quando passar de 3k emails/mês (∼1k usuários ativos), custa $20/mês — ponto em que já haverá receita.

**Ação após decisão:** Criar conta no provedor escolhido, obter credenciais SMTP, configurar `SMTP_HOST/PORT/USER/PASSWORD` no `.env` de produção.

**Status:** PENDENTE

---

### [2026-07-15] Credenciais do Supabase para produção

**Contexto:** O backend precisa de `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` para funcionar. A migration SQL (`migrations/001_initial_schema.sql`) precisa ser executada no SQL Editor do Supabase.

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA?

**Ação necessária:**
1. Criar projeto em supabase.com (grátis até 500MB/2 projetos)
2. Executar `migrations/001_initial_schema.sql` no SQL Editor
3. Copiar `Project URL` e `service_role` key em Settings → API
4. Configurar como variáveis de ambiente no servidor

**Status:** PENDENTE

---

### [2026-07-15] Onde hospedar o backend e o frontend?

**Contexto:** Para o lançamento precisamos de URLs públicas. Nada foi decidido ainda.

**Opções para o backend (FastAPI):**
- **A) Railway** — $5/mês, deploy via GitHub, simples. Recomendado para 1k usuários.
- **B) Fly.io** — tier grátis limitado, mais controle. Boa opção de custo zero no início.
- **C) VPS (DigitalOcean/Hetzner)** — mais controle, mais trabalho de setup.

**Opções para o frontend (HTML estático):**
- **A) Netlify/Vercel** — grátis, deploy automático via GitHub. Recomendado.
- **B) Cloudflare Pages** — grátis, excelente CDN.

**Recomendação do Claude:** Railway (backend) + Netlify (frontend). Setup de 30 minutos, custo ~$5/mês no início. Escala sem friction até milhares de usuários.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-15*
