# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-07-13] Configurar projeto Supabase e fornecer credenciais

**Contexto:** O backend está pronto e usa Supabase para auth e banco. Sem as credenciais, nada sobe.

**O que o dono precisa fazer:**

1. Criar projeto em https://supabase.com (gratuito para MVP)
2. Em Settings > API, copiar:
   - `Project URL` → `SUPABASE_URL`
   - `service_role` secret → `SUPABASE_SERVICE_ROLE_KEY`
3. Criar o arquivo `07-Clube-USA/.env` a partir do `.env.example` e preencher os valores
4. Rodar a migration: abrir o Supabase Dashboard > SQL Editor e executar o conteúdo de `07-Clube-USA/database/001_profiles_schema.sql`
5. Em Authentication > URL Configuration, configurar:
   - **Site URL:** `http://localhost:8000` (dev) ou seu domínio de produção
   - **Redirect URLs:** adicionar `http://localhost:8000/confirm-email.html` (ou URL de prod)
6. Em Authentication > Email Templates, revisar o template de confirmação (opcional)

**Impacto:** Bloqueante — sem isso o backend não inicializa.

**Status:** PENDENTE

---

### [2026-07-13] Domínio e hospedagem para lançamento

**Contexto:** Para 0.1 ir ao ar precisamos de: (a) domínio, (b) servidor para o backend FastAPI, (c) hosting para o frontend estático.

**Opções:**
- **A (recomendada para MVP):** Backend no Railway ou Render (gratuito, ~5min para subir) + Frontend em Netlify/Vercel (gratuito) + domínio Namecheap/GoDaddy (~$12/ano). Total: ~$12/ano.
- **B:** VPS ($6-20/mês no DigitalOcean/Vultr). Mais controle, mais trabalho de configuração.
- **C:** Tudo no mesmo servidor (backend serve HTML como static files). Mais simples mas mistura frontend e backend.

**Recomendação:** Opção A. Railway tem deploy via GitHub em 5 minutos, funciona perfeitamente para 1k-10k usuários. Quando crescer, migra para VPS sem refazer nada.

**Pergunta:** Qual opção prefere? Tem domínio já? Se sim, qual?

**Status:** PENDENTE

---

### [2026-07-13] Token de sessão: localStorage vs httpOnly cookie

**Contexto:** O frontend MVP usa `sessionStorage` para o JWT (mais seguro que localStorage — limpa ao fechar a aba). httpOnly cookies são mais seguros contra XSS mas exigem configuração de CORS/cookie no backend.

**Decisão técnica minha (reversível):** Para MVP com 1k usuários, sessionStorage é aceitável. Migro para httpOnly cookie antes de escalar.

**Não requer ação do dono agora.** Registrado por transparência.

**Status:** DECIDIDO (Claude) — revisar antes de escalar

---

*Atualizado em: 2026-07-13*
