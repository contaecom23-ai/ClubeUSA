# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-08-12] Criar projeto Supabase e fornecer credenciais

**Contexto:** O backend (Fase 0.1) está implementado e testado. Ele usa Supabase para autenticação (email/senha + confirmação de email) e banco de dados. Antes de qualquer deploy ou teste real com usuários, você precisa criar um projeto Supabase e fornecer as credenciais via variáveis de ambiente.

**Pergunta:** Você vai criar um projeto Supabase agora para conectar o backend?

**O que você precisa fazer:**
1. Acesse [supabase.com](https://supabase.com) → "New project"
2. Escolha uma organização (ou crie uma)
3. Defina nome do projeto (ex: `clubeusa-prod`) e senha do banco
4. Aguarde o projeto inicializar (~2 min)
5. Vá em **Project Settings → API** e copie:
   - `Project URL` → `SUPABASE_URL`
   - `service_role` secret key → `SUPABASE_SERVICE_KEY`
   - `JWT Settings > JWT Secret` → `SUPABASE_JWT_SECRET`
   - `anon` public key → para usar nos arquivos HTML do frontend
6. Execute a migration em `07-Clube-USA/db/migrations/001_initial_schema.sql` no SQL Editor do Supabase
7. Configure as variáveis de ambiente no `.env` (backend) e nos arquivos HTML (frontend)
8. Em **Authentication → Settings**, ative "Confirm email" e configure o domínio de redirect para `verify-email.html`

**Custo:** Plano Free do Supabase (até 50k MAU, 500MB banco) é suficiente para os primeiros 1.000 usuários. Sem custo inicial.

**Recomendação:** Criar agora no plano Free. Simples, sem custo, e desbloqueia todos os testes reais de Fase 0.1 e 0.2.

**Status:** PENDENTE

---

### [2026-08-12] Definir domínio e URL de produção do frontend

**Contexto:** Os arquivos HTML têm placeholder `SUBSTITUIR_PELA_URL_DO_PROJETO` e `SUBSTITUIR_PELA_ANON_KEY`. O backend precisa de `ALLOWED_ORIGINS` configurado com o domínio real. O link de verificação de email no Supabase também precisa do domínio correto.

**Pergunta:** Qual será o domínio do Clube USA? (Ex: `clubeusa.com`, `app.clubeusa.com`, etc.)

**Opções:**
- **A) Netlify/Vercel grátis** (ex: `clubeusa.netlify.app`): custo $0, deploy fácil; URL provisória, mas funciona para MVP
- **B) Domínio próprio** (ex: `clubeusa.com`): ~$10-15/ano; profissional desde o início; recomendado se já tem o domínio

**Recomendação:** Se já tem o domínio, use-o. Caso contrário, use Netlify/Vercel grátis para o MVP e troque quando quiser. O código não muda — só o `.env` e as configurações do Supabase.

**Status:** PENDENTE

---

### [2026-08-12] Definir onde hospedar o backend FastAPI

**Contexto:** O backend Python/FastAPI precisa rodar em algum servidor para os primeiros usuários.

**Pergunta:** Qual plataforma de hosting para o backend?

**Opções:**
- **A) Railway.app**: Free tier com 512MB RAM, deploy via GitHub. Fácil, sem config. Recomendado para 0–1k usuários. ~$5/mês quando sair do free.
- **B) Render.com**: Similar ao Railway, free tier "spins down" (cold start ~30s na primeira request do dia). Aceitável para MVP.
- **C) Fly.io**: Mais controle, free tier generoso, sem cold start. Levemente mais complexo de configurar.
- **D) VPS própria** (DigitalOcean/Hetzner): ~$5-6/mês, controle total, mas precisa gerenciar servidor.

**Recomendação:** Railway.app para começar — é o mais fácil de conectar ao GitHub repo e fazer deploy automático. Quando chegar a 1k usuários, avaliar custo.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-12*
