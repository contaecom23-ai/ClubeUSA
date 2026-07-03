# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-07-03] Infraestrutura para deploy (3 serviços externos necessários)

**Contexto:** A Fase 0.1 (cadastro + email confirmado) está implementada e testada localmente. Para fazer o deploy e ter a plataforma no ar, são necessários 3 serviços externos. Todos têm plano gratuito adequado para os primeiros 1.000 usuários.

---

#### Decisão 1 de 3 — Banco de dados PostgreSQL

**Pergunta:** Onde hospedar o banco de dados PostgreSQL da plataforma?

**Opções:**
- **A) Supabase** (recomendado): Free tier = 500MB, 2 projetos, 50.000 linhas. Painel amigável, backups automáticos, RLS nativo. Cria em 2 minutos em supabase.com. **Prós:** grátis, fácil, produção pronta para 1-10k usuários. **Contras:** dependência de vendor (migrável depois com dump SQL).
- **B) Neon.tech**: Serverless PostgreSQL, free tier generoso, boa performance. Menos recursos de painel. **Prós:** sem cold starts em paid tier. **Contras:** menos recursos que Supabase para nosso stack.
- **C) Railway**: $5/mês mínimo, PostgreSQL gerenciado. **Prós:** flexível. **Contras:** tem custo desde o início.

**Recomendação:** **Opção A — Supabase.** Free tier cobre perfeitamente os 1.000 primeiros usuários, setup em 5 minutos, e o banco é PostgreSQL padrão (export/migrate fácil se precisar trocar). Depois de criar o projeto, execute `supabase/migrations/001_initial_schema.sql` no SQL Editor.

**O que você precisa fazer:** Criar conta em supabase.com → New Project → copiar a *Connection String (URI)* e colocar no `.env` como `DATABASE_URL`.

**Status:** PENDENTE

---

#### Decisão 2 de 3 — Serviço de email transacional

**Pergunta:** Qual serviço usar para enviar emails de confirmação de cadastro?

**Opções:**
- **A) Resend.com** (recomendado): Free tier = 3.000 emails/mês, API simples, excelente deliverability. Setup: criar conta, verificar domínio, gerar API key. **Prós:** o melhor custo-benefício para transacional, SDK moderno. **Contras:** precisa verificar domínio.
- **B) SendGrid**: Free = 100 emails/dia. Mais complexo de configurar. **Prós:** marca conhecida. **Contras:** limite baixo no free.
- **C) Mailgun**: Free = 5.000 emails/mês por 3 meses, depois pago. **Prós:** generoso. **Contras:** muda após trial.
- **D) SMTP do Gmail**: Fácil de configurar mas não recomendado para produção (deliverability ruim, limite diário baixo).

**Recomendação:** **Opção A — Resend.com.** 3k emails/mês grátis é suficiente para centenas de cadastros por mês. Use o SMTP deles: host=`smtp.resend.com`, port=587, user=`resend`, password=API key.

**O que você precisa fazer:** Criar conta em resend.com → Domains → verificar seu domínio → API Keys → criar key → configurar no `.env` como `SMTP_PASSWORD`.

**Status:** PENDENTE

---

#### Decisão 3 de 3 — Hospedagem do backend FastAPI

**Pergunta:** Onde rodar o servidor Python/FastAPI?

**Opções:**
- **A) Railway.app** (recomendado): $5/mês (crédito grátis de $5/mês no plano Hobby). Deploy via GitHub, auto-scaling, SSL automático, logs em tempo real. **Prós:** deploy em 2 cliques, escala fácil. **Contras:** pequeno custo mensal.
- **B) Fly.io**: Free tier com hibernação (cold starts). **Prós:** grátis. **Contras:** hibernação torna o primeiro request lento; reinicia containers.
- **C) Render.com**: Free tier com hibernação após 15min inatividade. Similar ao Fly. **Prós:** grátis. **Contras:** hibernação + cold starts lentos.
- **D) DigitalOcean App Platform**: $5/mês, sem hibernação. Boa opção.

**Recomendação:** **Opção A — Railway.** $5/mês mas sem hibernação (UX melhor), deploy simples via GitHub, cobre tranquilamente 1k-10k usuários. Se quiser começar sem custo algum, use **Opção C (Render)** aceitando cold starts de ~30s.

**O que você precisa fazer:** Criar conta em railway.app → New Project → Deploy from GitHub → apontar para `07-Clube-USA/backend/` → adicionar variáveis de ambiente do `.env`.

**Status:** PENDENTE

---

### [2026-07-03] Domínio e URL da plataforma

**Contexto:** O app precisa saber sua URL pública para montar os links de confirmação de email e configurar CORS.

**Pergunta:** Qual será o domínio do Clube USA? (ex: clubeusa.com, clubeusa.app, clubeusa.us, etc.)

**Opções:**
- **A) clubeusa.com**: .com é o mais credível para um negócio. Disponibilidade a verificar. ~$12/ano.
- **B) clubeusa.app**: Moderno, seguro (HTTPS obrigatório). ~$14/ano.
- **C) clubeusa.us**: Temático (USA). ~$8/ano.

**Recomendação:** **Opção A — clubeusa.com** se disponível. A credibilidade do .com vale os $2/ano a mais. Se não estiver disponível, .app é boa alternativa.

**O que você precisa fazer:** Verificar disponibilidade (namecheap.com ou godaddy.com) → registrar → configurar DNS apontando para o servidor do backend → atualizar `APP_BASE_URL` e `CORS_ORIGINS` no `.env`.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-03*
