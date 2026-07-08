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

### [2026-07-08] Configuração do Supabase para Phase 0.1

**Contexto:** O backend FastAPI e o frontend estão implementados e prontos. Para rodar, precisam de um projeto Supabase ativo com Auth habilitado (email/senha).

**Pergunta:** Você tem um projeto Supabase já criado para o Clube USA? Se sim, me forneça as credenciais via `.env`.

**O que preciso de você:**

1. Criar um projeto em [supabase.com](https://supabase.com) (gratuito até 500MB + 50k MAU)
2. Adicionar as credenciais no arquivo `07-Clube-USA/backend/.env` (copie de `.env.example`):
   - `SUPABASE_URL` — em Settings → API → Project URL
   - `SUPABASE_SERVICE_ROLE_KEY` — em Settings → API → service_role (secret)
   - `SUPABASE_JWT_SECRET` — em Settings → API → JWT Secret
3. Rodar a migration SQL `migrations/001_initial_schema.sql` no SQL Editor do Supabase
4. Em Authentication → URL Configuration:
   - Site URL: `https://clubeusa.com` (ou `http://localhost:8000` para dev)
   - Redirect URLs: adicione `https://clubeusa.com/confirm.html` e `http://localhost:8000/confirm.html`

**Ação após configurar:** Me avise e o sistema estará funcional imediatamente.

**Status:** PENDENTE

---

### [2026-07-08] Domínio e hospedagem

**Contexto:** O frontend é HTML puro (sem build step) e o backend é FastAPI/Python. Precisamos decidir onde hospedar antes de ir ao ar.

**Pergunta:** Você já tem domínio (clubeusa.com?) e preferência de hospedagem?

**Opções:**

- **Opção A — Railway (recomendado para MVP):**
  - Pros: deploy com um comando, auto-SSL, suporta Python, free tier generoso, fácil de migrar depois
  - Contras: não é o mais barato em escala (mas para 1k usuários é irrelevante)

- **Opção B — Vercel (frontend) + Railway (backend):**
  - Pros: frontend em CDN global, backend separado
  - Contras: CORS entre domínios, mais complexidade de configuração inicial

- **Opção C — VPS (DigitalOcean/Linode):**
  - Pros: controle total, mais barato em escala
  - Contras: responsabilidade de manutenção (SSL, nginx, updates)

**Recomendação:** Railway para ambos frontend+backend no MVP. Simples, rápido, sem fricção. Migramos quando fizer sentido econômico.

**Status:** PENDENTE

---

### [2026-07-08] Variável `ALLOWED_ORIGINS` para CORS

**Contexto:** O backend restringe chamadas a origens explicitamente permitidas (segurança). Preciso saber o domínio final.

**Pergunta:** Qual o domínio de produção do Clube USA?

**Ação necessária:** Me informe o domínio para adicionar à configuração.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-08*
