# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

Formato de cada entrada:

```
### [DATA] Título da decisão
**Contexto:** ...
**Pergunta:** ...
**Opções:**
- Opção A: prós / contras
- Opção B: prós / contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## Decisões Pendentes

### [2026-07-18] Serviço de envio de email transacional

**Contexto:** A Fase 0.1 implementou o fluxo completo de confirmação de email. O código usa um adaptador com 3 drivers: `log` (desenvolvimento, imprime no console), `resend` e `sendgrid`. Para produção é necessário escolher e configurar um serviço real.

**Pergunta:** Qual serviço de email transacional usar para produção?

**Opções:**
- **Resend** (`resend.com`): API moderna, DX excelente, plano free 3.000 emails/mês, $20/mês para 50k. Fácil de configurar. Prós: simples, barato no início. Contras: mais novo, menor histórico de entregabilidade que SendGrid.
- **SendGrid** (`sendgrid.com`): padrão da indústria, entregabilidade alta, plano free 100 emails/dia. Prós: confiável, bem documentado. Contras: plano free mais restrito, UX de configuração mais complexo.
- **Amazon SES**: muito barato ($0.10/1000 emails), mas exige conta AWS e configuração de domínio/identidade mais trabalhosa.

**Recomendação:** Resend para começar — DX melhor, free tier suficiente para os primeiros meses, e pode migrar depois sem mudar código (só trocar `EMAIL_SERVICE=resend`). Se a entregabilidade virar problema, migrar para SendGrid.

**Ação necessária:** Criar conta no Resend, verificar domínio `clubeusa.com`, copiar API key para `RESEND_API_KEY` no .env de produção e setar `EMAIL_SERVICE=resend`.

**Status:** PENDENTE

---

### [2026-07-18] Credenciais Supabase para o ambiente de produção

**Contexto:** O backend usa `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` via env vars. O schema SQL (`database/migrations/001_users_schema.sql`) precisa ser executado uma vez no banco antes do deploy.

**Pergunta:** Você tem um projeto Supabase criado para o Clube USA? Se sim, pode fornecer a URL e a service_role key (em segredo — não no repositório).

**Ação necessária:**
1. Ir em `supabase.com` → projeto do Clube USA → Settings → API
2. Copiar `Project URL` → `SUPABASE_URL` no .env de produção
3. Copiar `service_role secret` → `SUPABASE_SERVICE_ROLE_KEY` (nunca no git)
4. Rodar a migration `001_users_schema.sql` no SQL Editor do Supabase

**Status:** PENDENTE

---

### [2026-07-18] Onde hospedar o frontend HTML (Fase 0.1)

**Contexto:** O frontend é HTML puro (sem framework), servido por qualquer CDN/host estático. O backend é FastAPI (Python).

**Pergunta:** Onde hospedar frontend e backend?

**Opções:**
- **Frontend:** Vercel, Netlify, ou GitHub Pages (todos free para HTML estático). Recomendo Vercel por integração nativa com GitHub.
- **Backend:** Railway, Render, ou Fly.io. Railway é o mais simples para FastAPI com deploy via push. Render tem free tier mas cold start lento. Fly.io mais controle mas mais configuração.

**Recomendação:** Frontend no Vercel + Backend no Railway. Total ~$5-10/mês para começo. Escala bem até 10k usuários sem mudança de plataforma.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-18*
