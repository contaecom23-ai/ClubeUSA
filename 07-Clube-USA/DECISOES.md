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

### [2026-08-13] Criar projeto Supabase e fornecer credenciais

**Contexto:** A Fase 0.1 (cadastro + auth) está implementada e depende de um projeto Supabase para funcionar. O backend usa 4 variáveis de ambiente que só você pode obter.

**Pergunta:** Você tem ou vai criar um projeto Supabase para o Clube USA?

**O que precisa ser feito:**
1. Criar conta e projeto em [supabase.com](https://supabase.com) (plano gratuito suporta ~500 usuários ativos/mês — ok para 0.1)
2. No painel Supabase → Settings → API, copiar:
   - `SUPABASE_URL` (ex: `https://xyzxyz.supabase.co`)
   - `SUPABASE_ANON_KEY` (chave pública, usada só no backend)
   - `SUPABASE_SERVICE_ROLE_KEY` (chave privada, só no servidor)
   - `SUPABASE_JWT_SECRET` (Settings → API → JWT Settings)
3. Executar o arquivo `07-Clube-USA/sql/001_initial_schema.sql` no SQL Editor do Supabase
4. No Supabase → Authentication → URL Configuration: definir `Site URL` = URL do seu servidor
5. Criar o arquivo `07-Clube-USA/backend/.env` com esses valores (não comitar)

**Custo:** Plano Free do Supabase é gratuito. Suficiente para os primeiros 1.000 usuários.

**Recomendação:** Criar no plano Free agora. Migrate para Pro ($25/mês) só quando tiver usuários reais pagantes ou precisar de mais de 500 MAU.

**Status:** PENDENTE

---

### [2026-08-13] Definir domínio / hospedagem do backend

**Contexto:** O backend FastAPI precisa de um servidor para rodar. Atualmente só existe localmente. Sem servidor, não há como usuários reais acessarem.

**Pergunta:** Onde hospedar o backend para as primeiras centenas de usuários?

**Opções:**
- **Railway.app** — deploy do Docker com 1 clique, plano Hobby $5/mês. Prós: simples, suporte a FastAPI. Contras: custo mínimo.
- **Render.com** — plano Free (limitado: dorme após inatividade) ou $7/mês (sempre ativo). Prós: grátis para testar. Contras: plano free dorme.
- **Fly.io** — plano gratuito (256 MB RAM). Prós: gratuito para 1k usuários. Contras: configuração um pouco mais técnica.
- **VPS (DigitalOcean/Linode)** — $4-6/mês. Prós: controle total. Contras: mais manutenção.

**Recomendação:** Railway ou Render para começar — menor fricção. Fly.io se quiser gratuito. VPS só se tiver alguém técnico gerenciando.

**Status:** PENDENTE

---

### [2026-08-13] Configurar envio de emails de confirmação no Supabase

**Contexto:** O Supabase, por padrão, envia emails de confirmação via seu próprio SMTP, mas com limite de 3 emails/hora no plano Free. Para produção real, é necessário SMTP próprio.

**Pergunta:** Qual provedor de email usar para os emails de confirmação de conta?

**Opções:**
- **Supabase built-in** — funciona para testes/desenvolvimento. Limite: 3/hora. Prós: zero configuração. Contras: inviável para produção.
- **Resend.com** — 100 emails/dia grátis, $20/mês para mais. Prós: moderno, API simples. Contras: pequeno custo em volume.
- **SendGrid** — 100 emails/dia grátis. Prós: conhecido, confiável. Contras: setup mais burocrático.
- **Amazon SES** — $0.10 por 1.000 emails. Prós: mais barato em volume. Contras: requer conta AWS + verificação de domínio.

**Recomendação:** Começar com Supabase built-in para os primeiros testes. Migrar para Resend quando tiver volume real (fácil de configurar no painel Supabase).

**Status:** PENDENTE

---

*Atualizado em: 2026-08-13*
