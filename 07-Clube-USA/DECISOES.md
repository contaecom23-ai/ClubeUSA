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

### [2026-07-08] Provedor de email transacional para produção

**Contexto:** O Supabase Auth envia os emails de verificação de conta. Em desenvolvimento ele usa o serviço compartilhado deles (limitado e sem domínio customizado). Para produção você precisa configurar um SMTP próprio no painel do Supabase (`Authentication > SMTP Settings`) para:
- Enviar pelo seu domínio (@clubeusa.com → credibilidade)
- Limites maiores (o compartilhado é muito restrito)
- Rastreamento de entrega

**Pergunta:** Qual provedor de email transacional usar?

**Opções:**
- **Resend.com** ✅ RECOMENDADO — 3.000 emails/mês grátis, API moderna, fácil configurar, tem suporte a domínio custom. Para 1k usuários, o free tier dura bastante.
- **SendGrid** — 100 emails/dia grátis, mais complexo, mas muito consolidado. Vale se já tiver conta.
- **Postmark** — Pago desde o início (~$15/mo), mas excelente deliverability. Faz sentido pós-tração.
- **Amazon SES** — Muito barato em escala ($0.10/1000), mas configuração trabalhosa. Ótimo para 10k+ usuários.

**Recomendação:** Comece com Resend.com (grátis, simples, profissional). Migre para SES quando passar de 10k usuários ativos.

**O que fazer:** Criar conta em resend.com → verificar domínio clubeusa.com → configurar SMTP no Supabase Dashboard.

**Status:** PENDENTE

---

### [2026-07-08] URL de produção e configuração do Supabase Auth

**Contexto:** O frontend (register.html, login.html, etc.) tem placeholders `YOUR-PROJECT-ID.supabase.co` e `YOUR-SUPABASE-ANON-KEY`. Para o produto funcionar, precisam ser preenchidos com os valores reais do seu projeto Supabase. Além disso, o Supabase precisa saber para qual URL redirecionar após verificação de email.

**O que você precisa configurar (você, no painel do Supabase):**

1. **Credenciais no `frontend/config.js`:**
   - `supabaseUrl` → `https://app.supabase.com > Settings > API > Project URL`
   - `supabaseAnonKey` → `Settings > API > Project API Keys > anon / public`

2. **URL de redirecionamento (Supabase Dashboard):**
   - `Authentication > URL Configuration > Site URL`: `https://clubeusa.com`
   - `Authentication > URL Configuration > Redirect URLs`: `https://clubeusa.com/verify-email.html`

3. **Variáveis do backend (arquivo `.env`, nunca commitar):**
   - Ver `.env.example` para a lista completa
   - `SUPABASE_JWT_SECRET` → `Settings > API > JWT Settings > JWT Secret`
   - `SUPABASE_SERVICE_ROLE_KEY` → `Settings > API > Project API Keys > service_role` (**NUNCA no frontend**)

**Status:** PENDENTE — aguardando você configurar e informar a URL de produção

---

### [2026-07-08] Domínio e hospedagem

**Contexto:** Precisamos de um lugar para hospedar a API FastAPI e as páginas HTML.

**Pergunta:** Onde hospedar?

**Opções:**
- **Railway.app** — Deploy da API FastAPI em minutos, ~$5/mês. Recomendado para começar.
- **Render.com** — Similar ao Railway, free tier disponível (dorme após inatividade — não ideal para produção).
- **VPS (DigitalOcean/Linode/Hetzner)** — $6-12/mês, controle total, mais setup. Faz sentido para 10k+ usuários.
- **Frontend estático no Vercel/Netlify** — Grátis para as páginas HTML. Separar da API.

**Recomendação:** Railway para a API (~$5/mês) + Vercel/Netlify para o frontend (grátis). Simples, escala até ~50k usuários sem dor. Migra para VPS quando valer a pena.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-08*
