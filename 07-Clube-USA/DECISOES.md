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

### [2026-08-08] Provedor de email para confirmação de conta

**Contexto:** A Fase 0.1 implementa o fluxo completo de confirmação de email.
O código tem uma abstração com adaptadores para `console` (logs no terminal, apenas para dev),
`sendgrid` e `resend`. Para ir para produção, é necessário escolher um provedor real
e fornecer uma API key.

**Pergunta:** Qual provedor de email usar para produção?

**Opções:**
- **Resend** (resend.com): Prós — DX excelente, free tier generoso (3k emails/mês), setup em 5min, domínio próprio. Contras — empresa nova (fundada 2023), menor histórico de entregabilidade. ~$20/mês para 50k emails.
- **SendGrid** (sendgrid.com): Prós — líder de mercado, entregabilidade provada, free tier 100 emails/dia. Contras — interface complexa, suporte ruim no free. ~$20/mês para 50k emails.
- **AWS SES**: Prós — baratíssimo ($0.10/1k emails), confiável. Contras — setup mais complexo, precisa de conta AWS, exige verificação de domínio.

**Recomendação:** **Resend** para começar. Setup rápido, DX superior, free tier suficiente para os primeiros 1k usuários. Se a entregabilidade for problema, migrar para SendGrid é trivial (só trocar o adaptador).

**Ação necessária do dono:**
1. Criar conta em resend.com
2. Verificar o domínio clubeusa.com (ou o domínio definitivo da plataforma)
3. Gerar API key e adicionar como `EMAIL_API_KEY` no .env de produção
4. Setar `EMAIL_PROVIDER=resend` no .env de produção

**Status:** PENDENTE

---

### [2026-08-08] Domínio e URL definitivos da plataforma

**Contexto:** O backend gera links de confirmação de email com base em `APP_URL`.
Em produção, este deve ser o domínio real (ex: `https://api.clubeusa.com` ou `https://clubeusa.com`).
O frontend usa `CLUBE_USA_API_URL` para apontar para o backend.

**Pergunta:** Qual é o domínio definitivo da plataforma e onde será feito o deploy?

**Opções:**
- **Render.com** + domínio próprio: Prós — free tier funcional para MVP, deploy simples via Git. Contras — cold start no free. ~$7/mês para plan básico sem cold start.
- **Railway.app**: Prós — UX excellent, zero cold start, bom para FastAPI. Contras — sem free tier permanente. ~$5-10/mês.
- **Fly.io**: Prós — edge computing, barato. Contras — mais complexo de configurar.

**Recomendação:** **Render.com** (plano Starter ~$7/mês) para o backend Python/FastAPI. Frontend estático no **Cloudflare Pages** (gratuito). É a stack mais barata e simples para chegar aos primeiros 1k usuários.

**Ação necessária do dono:** Confirmar domínio e plataforma de deploy para configurar variáveis de ambiente de produção.

**Status:** PENDENTE

---

### [2026-08-08] Credenciais do Supabase para produção

**Contexto:** O backend precisa de `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` de um projeto Supabase real.
A migration `001_initial_schema.sql` precisa ser executada no projeto.

**Ação necessária do dono:**
1. Criar projeto em supabase.com (free tier suficiente para MVP)
2. Executar `07-Clube-USA/migrations/001_initial_schema.sql` via SQL Editor do Dashboard
3. Copiar `Project URL` e `service_role` key para o .env de produção

**Status:** PENDENTE

---

*Atualizado em: 2026-08-08*
