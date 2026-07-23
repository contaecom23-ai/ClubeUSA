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

### [2026-07-23] Credenciais de infraestrutura para ativar o backend

**Contexto:** O backend da Fase 0.1 está implementado e pronto para deploy, mas requer três grupos de configurações externas que só você pode fornecer. Sem elas o servidor se recusa a iniciar (por design — evitar rodar sem segredos).

**Pergunta:** Quais credenciais você quer usar para o ambiente inicial (staging/produção)?

**Item A — Supabase (banco de dados)**
- Crie um projeto grátis em supabase.com
- Vá em: Project Settings → Database → Connection string (URI mode)
- Copie a "Transaction" URL
- Coloque em `DATABASE_URL` no `.env`
- Execute `migrations/001_initial_schema.sql` no SQL Editor do Supabase
- Opção alternativa: qualquer PostgreSQL ≥14 (Railway, Neon, Render) funciona igual

**Item B — Email transacional (para confirmação de cadastro)**

| Opção | Custo | Facilidade |
|-------|-------|------------|
| Resend (recomendado) | Grátis até 3.000 emails/mês | API key + SMTP simples |
| SendGrid | Grátis até 100/dia | Mais burocrático |
| Mailgun | 5.000/mês por 3 meses grátis | Ok |
| SMTP Gmail | Grátis mas instável | Não recomendado prod |
| Deixar em branco | Grátis (link impresso no log) | Só para dev/testes |

**Recomendação:** Resend — mais simples, free tier generoso para 1.000 usuários.
Crie conta em resend.com, pegue o API key e configure:
```
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=re_SEU_API_KEY
EMAIL_FROM=noreply@seudominio.com
```

**Item C — Domínio / URL pública**
- Qual URL pública o app vai usar? Ex: `clubeusa.com`, `app.clubeusa.com`
- Preciso saber para configurar `APP_URL` e `ALLOWED_ORIGINS` corretamente
- E para configurar o redirect de confirmação de email no Resend/SendGrid

**Status:** PENDENTE — aguardando você fornecer as credenciais e rodar o schema SQL

---

### [2026-07-23] Onde fazer o deploy inicial

**Contexto:** O backend é um servidor FastAPI. Precisa de um lugar para rodar.

**Pergunta:** Qual plataforma de deploy você prefere?

**Opções:**

| Plataforma | Custo inicial | Esforço de setup |
|------------|---------------|------------------|
| **Railway** (recomendado) | ~$5/mês | Mínimo — conecta o repo e deploya |
| Render | Grátis (dorme após 15min) / $7/mês para não dormir | Fácil |
| Fly.io | Grátis até certo limite | Médio |
| VPS (DigitalOcean/Linode) | $4-6/mês | Alto — você gerencia |
| AWS/GCP | Pago por uso | Alto |

**Recomendação:** Railway para começo — deploy via GitHub, env vars no dashboard, não dorme, $5/mês é suficiente para 1.000 usuários. Migra para VPS ou ECS quando precisar de mais controle (10k+ usuários).

**Status:** PENDENTE — aguardando sua decisão

---

*Atualizado em: 2026-07-23*
