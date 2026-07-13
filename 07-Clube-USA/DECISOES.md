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

### [2026-07-13] Provedor de email para confirmação de contas

**Contexto:** O backend de 0.1 envia emails de confirmação via SMTP. O código aceita qualquer provedor SMTP (configurado em `.env`). Sem SMTP configurado, o cadastro funciona mas o email não é enviado — o usuário precisaria confirmar manualmente (não viável em produção).

**Pergunta:** Qual provedor de email usar para enviar os emails transacionais (confirmação de conta, redefinição de senha futura)?

**Opções:**
- **Opção A: SendGrid** (sendgrid.com)
  - Prós: free tier 100 emails/dia, API REST bem documentada, alta deliverability, fácil integração
  - Contras: requer conta, domínio verificado recomendado para não cair em spam
  - Custo: grátis até 100/dia, $19.95/mês para 50k/mês (mais que suficiente para fase 0)

- **Opção B: Amazon SES**
  - Prós: muito barato ($0.10 por 1.000 emails), escala para qualquer volume
  - Contras: setup mais complexo (verificar domínio no AWS, sair do sandbox), requer conta AWS
  - Custo: praticamente grátis até 1k usuários

- **Opção C: Mailgun**
  - Prós: boa deliverability, API simples, 100 emails/dia grátis
  - Contras: trial de 3 meses grátis, depois pago

- **Opção D: Gmail SMTP** (conta sua)
  - Prós: grátis, imediato, sem setup
  - Contras: limite de 500 emails/dia, não escala, risco de bloqueio, não profissional para domínio `@clubeusa.com`

**Recomendação:** SendGrid (Opção A) para começar — setup em 30 minutos, free tier aguenta os primeiros 1.000 usuários sem custo, e migra facilmente para Amazon SES quando escalar. Você precisará: (1) criar conta em sendgrid.com, (2) verificar um domínio ou email remetente, (3) criar uma API key, (4) configurar no `.env` como SMTP (SendGrid suporta SMTP padrão).

**Status:** PENDENTE

---

### [2026-07-13] URL de produção da API e do Frontend

**Contexto:** O frontend HTML tem `window.APP_CONFIG = { api_url: "http://localhost:8000" }` em cada página. Em produção, isso precisa apontar para a URL real da API (ex: `https://api.clubeusa.com`). Hoje esse valor está hardcoded como localhost.

**Pergunta:** Qual será o domínio/URL de produção da API e onde o frontend será hospedado?

**Opções:**
- Opção A: Vercel/Netlify para frontend + Railway/Render para backend
  - Prós: deploy automático via GitHub, grátis no início, SSL automático
  - Contras: latência um pouco maior (servidores nos EUA/Europa), não é sua infraestrutura

- Opção B: VPS próprio (DigitalOcean, Linode, etc)
  - Prós: controle total, previsível em custo, mais barato em escala
  - Contras: você precisa gerenciar servidor, SSL, deploy manual ou CI/CD próprio

- Opção C: Supabase Storage para frontend + backend em VPS/Render
  - Prós: Supabase já está na stack, hospedagem de arquivos estáticos simples
  - Contras: não é a função principal do Supabase, CDN limitado

**Recomendação:** Render.com para a API (deploy automático do Docker, grátis para começar, fácil de escalar) + Netlify para o frontend (HTML estático, CDN global, grátis). Quando tiver o domínio `clubeusa.com`, configure os subdomínios `api.clubeusa.com` e `www.clubeusa.com`. Assim que decidir, atualizo o `APP_CONFIG` nas páginas HTML.

**Status:** PENDENTE

---

### [2026-07-13] Supabase — projeto e credenciais

**Contexto:** O backend usa Supabase como banco de dados (PostgreSQL). Para funcionar, precisamos de: `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`. A migration SQL em `migrations/001_users_and_auth.sql` precisa ser executada no projeto Supabase.

**Pergunta:** Você tem um projeto Supabase criado? Se sim, pode compartilhar as credenciais de forma segura (via `.env` no servidor, nunca no repositório)?

**Ação necessária:**
1. Criar projeto em supabase.com (ou usar existente)
2. Executar `migrations/001_users_and_auth.sql` no SQL Editor do projeto
3. Copiar `Project URL` e `service_role` key do painel Supabase
4. Configurar no `.env` do servidor de produção

**Status:** PENDENTE

---

*Atualizado em: 2026-07-13*
