# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, a pergunta, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-07-13] Provedor de email para confirmação de cadastro

**Contexto:** A Fase 0.1 implementou o fluxo completo de cadastro com confirmação de email. O backend suporta dois backends: `console` (imprime o link no terminal — só para dev) e `resend` (Resend.com — para produção). Sem um provedor real, usuários não recebem o email de confirmação e não conseguem fazer login.

**Pergunta:** Qual provedor de email transacional usar em produção?

**Opções:**

- **Resend.com** *(já implementado no código)*
  - Prós: API moderna e simples, tier grátis de 3.000 emails/mês, excelente deliverability, setup em 5 minutos, SDK limpo
  - Contras: serviço relativamente novo (2023), mas robusto; free tier acaba rápido se crescer rápido
  - Custo: grátis até 3k emails/mês; $20/mês para 50k

- **SendGrid**
  - Prós: market leader, muito robusto, tier grátis de 100 emails/dia
  - Contras: interface complexa, requer verificação de domínio mais trabalhosa, free tier baixo
  - Custo: grátis 100/dia; $19.95/mês para 40k

- **AWS SES**
  - Prós: custo mais baixo em escala ($0.10 por 1.000 emails), confiável
  - Contras: requer conta AWS, sandbox para novos projetos (necessita request de produção), mais configuração
  - Custo: $0.10/1k + custo de saída de dados

- **Postmark**
  - Prós: melhor deliverability de transacionais, excelente suporte
  - Contras: não tem free tier permanente (apenas 100 emails de teste)
  - Custo: $15/mês para 10k emails

**Recomendação do Claude:** **Resend.com** para começar. O código já está pronto (`EMAIL_BACKEND=resend`, `RESEND_API_KEY=...`). Para os primeiros 1.000 usuários o free tier de 3.000 emails/mês é suficiente. Se crescer, o custo é razoável e a migração para SES é simples.

**O que você precisa fazer:**
1. Criar conta em resend.com
2. Verificar o domínio clubeusa.com
3. Gerar uma API key
4. Adicionar ao `.env` ou secrets do deploy: `RESEND_API_KEY=re_xxxx` e `EMAIL_BACKEND=resend`

**Status:** PENDENTE

---

### [2026-07-13] Credenciais Supabase e ambiente de deploy

**Contexto:** O backend está construído e pronto para rodar, mas precisa de um banco de dados. A stack escolhida é Supabase (Postgres). Sem as credenciais, o backend não inicializa em produção.

**Pergunta:** Você tem um projeto Supabase criado? Onde o backend vai rodar?

**O que você precisa:**
1. **Supabase:**
   - Criar projeto em supabase.com (ou usar um existente)
   - Copiar a `DATABASE_URL` (Connection String → URI mode)
   - Executar a migration: `07-Clube-USA/backend/migrations/001_initial_schema.sql` no SQL Editor do Supabase
   
2. **Deploy do backend (opções):**
   - **Railway.app** — simples, plano Starter $5/mês, suporta Python/FastAPI direto do GitHub. Recomendado para MVP.
   - **Render.com** — similar ao Railway, tem free tier (mas dorme após inatividade)
   - **Fly.io** — mais controle, mais complexo, free tier pequeno
   - **VPS (DigitalOcean/Linode)** — mais barato em escala, mas mais setup

3. **Variáveis de ambiente obrigatórias para produção:**
   ```
   DATABASE_URL=postgresql://...  (do Supabase)
   SECRET_KEY=<64 chars aleatórios>
   EMAIL_BACKEND=resend
   RESEND_API_KEY=re_xxxx
   EMAIL_FROM=noreply@clubeusa.com
   APP_URL=https://clubeusa.com
   FRONTEND_URL=https://clubeusa.com
   ALLOWED_ORIGINS=https://clubeusa.com
   DEBUG=false
   ```

**Recomendação do Claude:** Railway + Supabase free tier para MVP. Custo total: ~$5-10/mês enquanto escala para os primeiros 1.000 usuários.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-13*
