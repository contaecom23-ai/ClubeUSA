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

### [2026-08-05] Credenciais Supabase — projeto de produção

**Contexto:**
O backend está implementado e testado (com mocks). Para fazer o smoke-test real e ativar o fluxo de email de confirmação, precisamos de credenciais de um projeto Supabase real:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`

Além disso, no painel Supabase você precisa configurar:
1. **Authentication > URL Configuration > Site URL**: `http://localhost:8000` (dev) / domínio real (prod)
2. **Authentication > Email Templates**: personalizar o email de confirmação para Clube USA
3. **Authentication > Settings > JWT expiry**: recomendo 604800 (7 dias)

**Pergunta:**
Você já tem um projeto Supabase criado para o Clube USA? Se sim, pode compartilhar as credenciais via `.env` (sem commitar)?

**Opções:**
- **A) Projeto Supabase já existe**: forneça as credenciais — Claude sobe o schema (`001_users_profile.sql`) e faz smoke-test real.
- **B) Criar projeto novo agora**: acesse app.supabase.com, crie projeto "clube-usa-prod", copie as credenciais.
- **C) Manter mock por ora**: seguir para Fase 0.2 (Referral) no mesmo modo mock; conectar ao Supabase real antes do lançamento.

**Recomendação:**
Opção A ou B o quanto antes — o fluxo de email de confirmação só pode ser validado com Supabase real. Leva ~5 minutos criar o projeto e rodar a migration.

**Status:** PENDENTE

---

### [2026-08-05] Domínio e hospedagem do frontend

**Contexto:**
O frontend é HTML estático (sem framework). Para o lançamento inicial (1k usuários), precisa de hospedagem.

**Pergunta:**
Qual é o domínio e onde quer hospedar o frontend?

**Opções:**
- **A) Vercel/Netlify (gratuito, CDN global)**: melhor opção para HTML estático — deploy em 2 minutos, HTTPS grátis. Recomendado.
- **B) VPS próprio (nginx)**: mais controle, custo baixo (~$5/mês DigitalOcean), mais trabalho de setup.
- **C) Subdomínio Supabase**: não recomendado — acopla infra.

**Recomendação:**
Vercel para o frontend + qualquer VPS ou Railway/Render para o backend FastAPI. Custo mínimo para 1k usuários.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-05*
