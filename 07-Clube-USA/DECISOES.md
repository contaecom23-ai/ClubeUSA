# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-07-05] Supabase: criar o projeto e fornecer credenciais

**Contexto:** A Fase 0.1 (cadastro + email confirmado) está implementada. O backend conecta ao Supabase Postgres via variável de ambiente `DATABASE_URL`. Sem o projeto criado, o sistema não pode rodar em produção.

**Pergunta:** Você vai criar o projeto Supabase e configurar as variáveis de ambiente?

**O que fazer:**
1. Acesse https://supabase.com e crie um projeto novo (nome sugerido: `clubeusa-prod`)
2. Vá em **Settings > Database > Connection string > URI** e copie a connection string
3. Adicione ao seu servidor/plataforma de deploy como variável `DATABASE_URL`
4. Execute o arquivo `07-Clube-USA/migrations/001_initial_schema.sql` no **SQL Editor** do Supabase
5. Gere um `SECRET_KEY` com: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

**Custo:** Supabase free tier é suficiente para os primeiros 1.000 usuários (500 MB banco, 50k MAU auth). Upgrade necessário ~$25/mês ao passar de 50k MAU.

**Recomendação:** Crie agora — é grátis e necessário para qualquer teste real. O código já está pronto e esperando só as credenciais.

**Status:** PENDENTE

---

### [2026-07-05] Provedor de email (SMTP) para confirmação de cadastro

**Contexto:** O sistema envia email de confirmação via SMTP. Sem SMTP configurado, o link é apenas logado no servidor (funciona em dev, não em produção).

**Pergunta:** Qual provedor de email você quer usar?

**Opções:**
- **Resend** (resend.com): Prós: 3.000 emails/mês grátis, API simples, boa reputação de entrega. Contras: serviço novo (fundado 2022). *Recomendado para iniciar.*
- **SendGrid** (sendgrid.com): Prós: 100 emails/dia grátis, muito usado, confiável. Contras: free tier limitado, configuração mais burocrática.
- **Mailgun**: Prós: 5.000 emails/mês por 3 meses grátis. Contras: depois cobra por envio.
- **SMTP do Google/Gmail**: Prós: grátis. Contras: limite de 500 emails/dia, não recomendado para produção.

**O que fazer após escolher:** Crie conta, obtenha credenciais SMTP e preencha as variáveis `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` no servidor.

**Recomendação:** Resend — melhor UX de configuração e free tier generoso para os primeiros 1.000 usuários.

**Status:** PENDENTE

---

### [2026-07-05] Plataforma de deploy do backend (FastAPI)

**Contexto:** A API Python/FastAPI precisa de um servidor para rodar. Há um Dockerfile pronto.

**Pergunta:** Onde você quer hospedar a API?

**Opções:**
- **Render** (render.com): Prós: deploy via GitHub, free tier (dorme após inatividade), $7/mês pro. Contras: cold start no free. *Recomendado para começar.*
- **Railway** (railway.app): Prós: simples, $5/mês com créditos mensais. Contras: free tier limitado.
- **Fly.io**: Prós: $0-5/mês, sem sleep, edge deployment. Contras: CLI necessário, um pouco mais técnico.
- **DigitalOcean App Platform**: Prós: confiável, $12/mês. Contras: mais caro para começar.
- **Servidor próprio (VPS)**: Prós: controle total. Contras: gestão de infra, segurança, uptime.

**Recomendação:** Render com plano $7/mês — sem cold start, deploy automático via GitHub, fácil de configurar. Para testar, o free tier funciona (aceita cold start de ~30s).

**Status:** PENDENTE

---

### [2026-07-05] Domínio da plataforma

**Contexto:** As variáveis `BASE_URL` e `FRONTEND_URL` no backend precisam do domínio definitivo para que os links de confirmação de email funcionem corretamente.

**Pergunta:** Qual é o domínio da plataforma? (ex: clubeusa.com, clubebrasil.us, etc.)

**O que fazer:** Assim que decidido, atualizar as variáveis de ambiente no servidor de deploy.

**Status:** PENDENTE

---

### [2026-07-05] BUG INFORMATIVO: Workflow do GitHub Actions tinha YAML inválido

**Contexto:** O arquivo `.github/workflows/clubeusa-builder.yml` tinha indentação completamente quebrada (todos os campos aninhados em cascata incorreta), o que impedia o GitHub Actions de parsear e executar o workflow.

**Ação tomada:** Corrigido na Fase 0.1 PR — o YAML agora tem indentação correta. Não requer decisão do dono.

**Status:** RESOLVIDO (pelo Claude, decisão técnica não-destrutiva)

---

*Atualizado em: 2026-07-05*
