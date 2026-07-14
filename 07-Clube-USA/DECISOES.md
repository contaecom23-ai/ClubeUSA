# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-07-14] Configuração do projeto Supabase (BLOQUEADOR para Fase 0.1 entrar em produção)

**Contexto:**
A Fase 0.1 está codificada e pronta para rodar, mas exige um projeto Supabase real com as chaves de API. Sem isso, o backend não inicia.

**Pergunta:**
Você tem um projeto Supabase criado para o Clube USA? Se não, precisa criar um.

**O que você precisa fazer (não requer aprovação do Claude, só sua ação):**

1. **Criar projeto Supabase** (gratuito até ~500 MB):
   - Acesse https://supabase.com → New Project
   - Nome sugerido: `clube-usa`
   - Escolha região: `US East (N. Virginia)` — mais próxima do público-alvo

2. **Aplicar a migration SQL:**
   - No dashboard → SQL Editor → cole e execute o arquivo `07-Clube-USA/backend/migrations/001_initial_schema.sql`

3. **Configurar email de verificação:**
   - Dashboard → Authentication → URL Configuration
   - Site URL: `https://SEU_DOMINIO.com` (ou `http://localhost:3000` para testar)
   - Redirect URLs: adicione `https://SEU_DOMINIO.com/verify-email.html`
   - Email Templates → Confirm signup → verifique que o link aponta para a URL correta

4. **Copiar as chaves:**
   - Dashboard → Settings → API
   - Copie: `URL`, `anon key`, `service_role key`, `JWT Secret`
   - Crie `07-Clube-USA/backend/.env` baseado em `.env.example` e preencha com as chaves reais
   - **NUNCA commite o `.env` com chaves reais** (está no `.gitignore`)

5. **Hospedar o backend:**
   - Opção grátis/fácil: [Railway](https://railway.app) ou [Render](https://render.com)
   - Configure as env vars no painel do host (não no código)
   - Comando de start: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

6. **Hospedar o frontend:**
   - Opção grátis: [Netlify](https://netlify.com) ou [GitHub Pages](https://pages.github.com)
   - Antes do deploy, edite `frontend/assets/api.js` linha 1: troque `http://localhost:8000` pela URL real do backend

**Recomendação do Claude:**
Comece com Railway (backend) + Netlify (frontend) — ambos gratuitos, deploy simples via GitHub, suportam env vars. Isso cobre os primeiros 1.000 usuários sem custo.

**Status:** PENDENTE — aguardando ação do dono

---

### [2026-07-14] Provedor de e-mail transacional (para verificação de conta)

**Contexto:**
O Supabase usa seu próprio SMTP para enviar e-mails de verificação. O limite gratuito é 3 e-mails/hora — **insuficiente para lançamento**. Acima disso é necessário configurar SMTP externo.

**Pergunta:**
Qual provedor de e-mail transacional deseja usar?

**Opções:**
| Provedor | Custo | Limite grátis | Notas |
|---|---|---|---|
| **Resend** | $0–20/mês | 3.000/mês | API moderna, fácil integrar com Supabase |
| **SendGrid** | $0–19.95/mês | 100/dia | Consolidado, mais configuração |
| **Mailgun** | $0–35/mês | 100/dia (3 meses) | Bom deliverability |
| Supabase built-in | $0 | 3/hora | Só para dev/teste |

**Recomendação do Claude:**
**Resend** — mais simples, integração nativa com Supabase Auth, 3.000 e-mails/mês grátis são suficientes para os primeiros 1.000 usuários. Setup em 10 minutos.

**Como fazer:** Resend.com → criar conta → gerar API Key → no Supabase: Auth → SMTP Settings → ativar custom SMTP com as credenciais do Resend.

**Status:** PENDENTE — aguardando decisão e ação do dono

---

*Atualizado em: 2026-07-14*
