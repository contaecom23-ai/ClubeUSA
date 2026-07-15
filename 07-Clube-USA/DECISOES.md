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

---

### [2026-07-15] Provedor de e-mail para confirmação de conta e notificações

**Contexto:**
A Fase 0.1 (cadastro + confirmação de e-mail) está implementada. O código suporta qualquer servidor SMTP configurável por variável de ambiente. Em modo `DEBUG=true` os e-mails são apenas logados no console, o que serve para desenvolvimento local. Para produção, precisamos de um provedor real.

**Pergunta:**
Qual provedor de e-mail usar para o Clube USA em produção?

**Opções:**

| Opção | Custo | Prós | Contras |
|-------|-------|------|---------|
| **Resend** | Grátis até 3.000/mês; USD 20/mês depois | API moderna, fácil de usar, boa reputação de entrega, suporte a domínio customizado | Mais novo no mercado |
| **SendGrid** | Grátis 100/dia; USD 19.95/mês para 50k | Mais estabelecido, boa documentação | Plano gratuito muito limitado (100/dia) |
| **AWS SES** | USD 0,10 por 1.000 e-mails | Muito barato na escala, alta confiabilidade | Mais complexo de configurar (requer conta AWS, verificação de domínio) |
| **Postmark** | USD 15/mês para 10k | Foco em transacional, excelente entrega | Sem plano gratuito relevante |

**Recomendação:**
**Resend** — plano gratuito suficiente para os primeiros 1.000 usuários (3k e-mails/mês), API simples, e fácil de trocar depois. O código já abstrai o SMTP, então a migração futura é apenas trocar credenciais no `.env`.

**O que precisa do dono:**
1. Criar conta em resend.com (ou provedor de escolha)
2. Verificar o domínio `clubeusa.com` no painel do provedor
3. Adicionar as variáveis no ambiente de produção:
   ```
   SMTP_HOST=smtp.resend.com
   SMTP_PORT=587
   SMTP_USER=resend
   SMTP_PASSWORD=<API_KEY_DO_RESEND>
   SMTP_FROM=noreply@clubeusa.com
   ```

**Status:** PENDENTE

---

### [2026-07-15] Projeto Supabase e credenciais de banco de dados

**Contexto:**
O backend usa Supabase como banco PostgreSQL. Preciso das credenciais para rodar a migração `0001_initial_schema.sql` e para que a API funcione em produção/staging.

**Pergunta:**
Você já tem um projeto Supabase criado para o Clube USA? Se não, preciso que você crie um em supabase.com e compartilhe as variáveis.

**O que precisa do dono:**
1. Criar projeto em supabase.com (free tier suporta os primeiros 1.000 usuários com folga)
2. Ir em Settings > API e copiar:
   - `SUPABASE_URL` (ex: `https://xxxxxxxxxxx.supabase.co`)
   - `SUPABASE_SERVICE_ROLE_KEY` (a chave `service_role`, NÃO a `anon`)
3. Executar o arquivo `07-Clube-USA/supabase/migrations/0001_initial_schema.sql` no SQL Editor do Supabase
4. Adicionar as vars no ambiente de produção

**Status:** PENDENTE

---

*Atualizado em: 2026-07-15*
