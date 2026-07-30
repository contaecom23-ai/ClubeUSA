# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-07-30] Serviço de envio de email para produção

**Contexto:** A Fase 0.1 (cadastro + email confirmado) está implementada. O backend envia emails de confirmação. Em desenvolvimento, ele printa o link no console (modo console, sem custo, sem configuração). Para produção, precisamos de um serviço real.

**Pergunta:** Qual serviço de email usar para enviar os emails de confirmação (e futuramente promoções, notificações)?

**Opções:**

- **Opção A — Resend** (https://resend.com)
  - Prós: Developer-first, API simples, free tier generoso (3.000 emails/mês), boa reputação de deliverability, SDK Python
  - Contras: Empresa menor, menos histórico que SendGrid
  - Custo: Grátis até 3k/mês → $20/mês até 50k → escala bem

- **Opção B — SendGrid** (Twilio)
  - Prós: Líder de mercado, free tier 100 emails/dia, muito documentado
  - Contras: Interface complexa, Twilio às vezes tem problemas de suporte, free tier pequeno
  - Custo: Grátis 100/dia → $19.95/mês até 50k

- **Opção C — AWS SES**
  - Prós: Extremamente barato ($0.10 por 1.000), escala para milhões
  - Contras: Setup mais complexo (verificação de domínio, sandbox mode), requer conta AWS
  - Custo: $0.10/1.000 emails — mais barato em escala

- **Opção D — SMTP de provedor de domínio** (ex: Google Workspace, Zoho)
  - Prós: Já pode estar disponível se tiver o domínio
  - Contras: Limites de envio, não ideal para transacional em escala

**Recomendação do Claude:** **Opção A (Resend)** para começar — simples de configurar, free tier suficiente para os primeiros 1.000 usuários, e fácil de migrar para AWS SES quando escalar para 10k+. Mudar o serviço de email depois é reversível (1-2h de trabalho).

**O que você precisa fazer:**
1. Criar conta em resend.com
2. Verificar o domínio clubeusa.com
3. Gerar uma API Key
4. Fornecer ao Claude para atualizar o backend (ou configurar no `.env` do servidor)

**Status:** PENDENTE

---

### [2026-07-30] Projeto Supabase e variáveis de ambiente de produção

**Contexto:** O backend precisa de um banco de dados PostgreSQL para funcionar. A stack escolhida é Supabase. Sem isso, o servidor não pode rodar em produção.

**Pergunta:** Você tem um projeto Supabase criado? Se sim, qual é a Connection String?

**O que você precisa:**
1. Criar projeto em supabase.com (se não tiver)
2. Ir em Settings > Database > Connection string > URI
3. Rodar a migration `07-Clube-USA/supabase/migrations/001_initial_schema.sql` no SQL Editor do Supabase
4. Gerar `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
5. Preencher o arquivo `.env` no servidor (baseado no `.env.example`)

**Status:** PENDENTE

---

### [2026-07-30] Onde hospedar o backend

**Contexto:** O backend FastAPI precisa rodar em algum servidor para ser acessível ao público.

**Pergunta:** Onde hospedar o backend?

**Opções:**

- **Opção A — Railway** (railway.app): Simples, deploy via GitHub, ~$5-10/mês, bom para começar
- **Opção B — Render** (render.com): Similar ao Railway, free tier existe mas hiberna após inatividade
- **Opção C — Fly.io**: Mais controle, free tier generoso, CLI-based
- **Opção D — VPS (DigitalOcean/Linode/Vultr)**: $6-10/mês, mais controle, mais trabalho de setup

**Recomendação:** **Railway** para começar — deploy via GitHub em minutos, previsível, sem hibernação. Migrar para VPS quando tiver > 1.000 usuários ativos.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-30*
