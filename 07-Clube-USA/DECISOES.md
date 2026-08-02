# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-08-02] Credenciais externas para integração real (Supabase + Email)

**Contexto:** O backend Fase 0.1 está implementado e testado com mocks. Para rodar em produção real precisamos de 3 coisas:

**Pergunta 1 — Supabase:**
- Você já tem um projeto Supabase criado para o Clube USA?
- Se sim, forneça: `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` (não a anon key).
- Se não, criar é gratuito em supabase.com. Eu posso documentar o passo a passo.
- Após fornecer as credenciais, é preciso executar `backend/migrations/001_initial_schema.sql` no SQL Editor do Supabase.

**Pergunta 2 — Email transacional:**
- Para enviar emails de confirmação de cadastro, precisamos de um serviço SMTP.
- **Opção A: SendGrid** (gratuito até 100 emails/dia, depois $19.95/mês) — recomendado para começar.
- **Opção B: Resend** (gratuito até 3.000 emails/mês no plano free) — mais fácil de configurar.
- **Opção C: AWS SES** (custo muito baixo: ~$0.10/1.000 emails, mas setup mais complexo).
- **Recomendação Claude:** Opção B (Resend) — mais simples para os primeiros 1.000 usuários, sem cartão de crédito inicialmente.

**Pergunta 3 — Hospedagem da API:**
- Para expor a API FastAPI publicamente, precisamos de hospedagem.
- **Opção A: Railway.app** (plano Hobby $5/mês, deploy automático via Git) — recomendado para start.
- **Opção B: Render.com** (free tier com spin-down, plano pago $7/mês) — alternativa.
- **Opção C: Fly.io** (free tier generoso para apps pequenos).
- **Recomendação Claude:** Opção A (Railway) — mais simples de operar, sem cold starts.

**Pergunta 4 — Domínio/frontend:**
- O frontend HTML pode ser hospedado no Cloudflare Pages (gratuito, HTTPS automático).
- Você já tem domínio `clubeusa.com`? Se sim, posso configurar o CNAME para o Cloudflare Pages.

**Status:** PENDENTE — aguardando resposta do dono

---

*Atualizado em: 2026-08-02*
