# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio,
aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo),
ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-08-12] Provedor de email para confirmação de cadastro

**Contexto:**
A Fase 0.1 inclui confirmação de email obrigatória antes do primeiro login. O backend já tem o código
de envio implementado via SMTP genérico (funciona com qualquer provedor SMTP). Em desenvolvimento, o
link de confirmação é impresso no log (stdout) — nenhum email real é enviado enquanto as env vars
`EMAIL_SMTP_*` não forem configuradas.

**Pergunta:**
Qual provedor de email usar em produção, e você pode fornecer as credenciais?

**Opções:**

- **Opção A — SendGrid (recomendado para início)**
  - Prós: free tier generoso (100 emails/dia), API robusta, boa entregabilidade, sem SMTP headache
  - Contras: mais um serviço externo, requer conta Twilio/SendGrid
  - Config: converter o código SMTP para SDK SendGrid (30 min de trabalho)
  - Preço: grátis até 100/dia; ~$15/mês acima disso

- **Opção B — SMTP do Gmail / Workspace**
  - Prós: você provavelmente já tem a conta, zero custo
  - Contras: limites baixos (500/dia Gmail, 2.000/dia Workspace); má reputação de IP; menos confiável em produção
  - Config: `EMAIL_SMTP_HOST=smtp.gmail.com`, porta 587, senha de app do Google

- **Opção C — Amazon SES**
  - Prós: muito barato (~$0.10/1.000 emails), escala para 1M+ sem reprovar
  - Contras: conta AWS necessária; setup mais complexo (verificar domínio, sair do sandbox)
  - Melhor escolha para Fase 2+ quando o volume crescer

- **Opção D — Resend.com**
  - Prós: DX excelente, free tier 3.000/mês, API moderna
  - Contras: startup menor (risco de longevidade, mas bem financiada)

**Recomendação do Claude:**
Começar com **SendGrid (A)** para os primeiros 1k usuários — gratuito, confiável, fácil de configurar.
Migrar para Amazon SES quando o volume justificar (Fase 2+). Evite Gmail SMTP em produção.

**Ação necessária:** Crie conta no SendGrid → gere API Key → me passe ou coloque em `.env`:
```
EMAIL_SMTP_HOST=smtp.sendgrid.net
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=apikey
EMAIL_SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxx
EMAIL_FROM=noreply@clubeusa.com
```

**Status:** PENDENTE

---

### [2026-08-12] Domínio e URL de produção

**Contexto:**
O link de confirmação de email usa `APP_URL` (ex: `https://clubeusa.com`). O sistema funciona com
qualquer URL, mas o dono precisa configurar `APP_URL` no `.env` de produção.

**Pergunta:**
Qual será o domínio final da plataforma? Você já tem o domínio registrado?

**Opções:**
- `clubeusa.com` (ideal — direto, memorável)
- `clube.usa.com` (não existe, só exemplo)
- Subdomínio temporário (ex: `app.clubeusa.com.br`) enquanto o .com não está disponível

**Recomendação:** Registre `clubeusa.com` agora se disponível (~$12/ano no Namecheap/Cloudflare).
O nome é o ativo mais barato e mais irreversível do produto.

**Status:** PENDENTE

---

### [2026-08-12] Credenciais do Supabase

**Contexto:**
O backend precisa de `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` (service_role). O projeto Supabase
precisa ser criado, e a migration SQL em `07-Clube-USA/migrations/001_initial_schema.sql` precisa
ser executada no SQL Editor do Supabase.

**Ação necessária:**
1. Crie um projeto no Supabase (free tier suficiente para Fase 0)
2. Vá em Project Settings → API → copie `URL` e `service_role key`
3. Execute `migrations/001_initial_schema.sql` no SQL Editor
4. Adicione ao `.env` de produção:
   ```
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_SERVICE_KEY=eyJhbGc...
   ```

**Status:** PENDENTE

---

*Atualizado em: 2026-08-12*
