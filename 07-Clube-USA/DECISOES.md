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

### [2026-08-05] Provedor de email transacional (SMTP)

**Contexto:** O sistema de cadastro está pronto e envia emails de confirmação. Em desenvolvimento, os links são logados no console. Para produção, precisamos de um provedor SMTP real. O campo `SMTP_HOST` no `.env` controla isso — sem custo de mudança de código.

**Pergunta:** Qual provedor de email transacional usar para os emails de confirmação/notificação?

**Opções:**

| Provedor | Custo inicial | Free tier | Pros | Contras |
|---|---|---|---|---|
| **Resend** | $0 até 3k emails/mês | 3.000/mês | API moderna, fácil, reputação boa, docs excelentes | Novo no mercado |
| **SendGrid** | $0 até 100/dia (~3k/mês) | 100/dia | Padrão do mercado, confiável | Interface pesada, suporte fraco no free |
| **Mailgun** | $0 até 1k/mês por 3 meses | 3 meses grátis | Boa API, bom deliverability | Expira, depois ~$35/mês |
| **Amazon SES** | ~$0.10/1k emails | Sem free tier real | Baratíssimo em escala, confiável | Setup mais complexo (AWS) |

**Recomendação Claude:** **Resend** para começar — free tier generoso para 1k usuários, API limpa, setup em 5 minutos. Migra para Amazon SES quando passar de 50k usuários (custo justificável). Não use SendGrid free — limite de 100/dia é insuficiente rapidamente.

**Ação necessária:** Criar conta no Resend (resend.com), gerar API key, adicionar SMTP settings no `.env` de produção.

**Status:** PENDENTE

---

### [2026-08-05] Configuração do projeto Supabase

**Contexto:** O backend está pronto e usa Supabase (PostgreSQL) para autenticação e dados. A migration `migrations/001_users.sql` precisa ser rodada uma vez no projeto Supabase. As credenciais `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` (service_role) precisam ser geradas.

**Pergunta:** Você tem um projeto Supabase criado? Preciso das credenciais para o deploy funcionar.

**Ação necessária:**
1. Criar projeto em [supabase.com](https://supabase.com) (free tier suficiente para fase 0)
2. Copiar `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` (service_role) do painel → Settings → API
3. Rodar `migrations/001_users.sql` no SQL editor do Supabase
4. Adicionar as credenciais no `.env` do servidor

**Status:** PENDENTE

---

### [2026-08-05] Onde hospedar a API (deploy)

**Contexto:** A API FastAPI está pronta para rodar (`uvicorn api.main:app`). Precisa de um lugar para hospedar. As opções abaixo escalam bem até 100k usuários.

**Pergunta:** Onde fazer o deploy da API?

**Opções:**

| Opção | Custo | Prós | Contras |
|---|---|---|---|
| **Railway** | ~$5-10/mês | Deploy em 2 min com git push, simples, boa DX | Menos controle |
| **Render** | $0 (free tier com sleep) ou $7/mês | Free tier existe | Free tier dorme após inatividade (ruim para prod) |
| **Fly.io** | ~$3-10/mês | Rápido, global | Curva de aprendizado |
| **AWS/GCP/Azure** | Variável | Máximo controle e escala | Over-engineering agora |

**Recomendação Claude:** **Railway** para começar. Deploy simples, sem surpresas, $5/mês é razoável. Migra para infraestrutura própria na Fase 2 quando tiver receita. Não use Render free em produção — o sleep quebra a experiência.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-05*
