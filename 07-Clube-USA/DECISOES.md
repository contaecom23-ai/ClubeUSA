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

### [2026-10-15] Provedor de email transacional para confirmação de cadastro

**Contexto:** A Fase 0.1 implementou o fluxo completo de cadastro por email com confirmação. O backend está pronto. Falta configurar o provedor de email para produção.

**Pergunta:** Qual provedor usar para enviar emails de confirmação e boas-vindas?

**Opções:**
- **A) SendGrid** — $0 até 100 emails/dia grátis, SDK Python pronto, muito confiável. Recomendado para 1k-100k usuários. Ação: criar conta em sendgrid.com, pegar API key, setar `SENDGRID_API_KEY` e `EMAIL_FROM` no .env de produção.
- **B) Supabase Auth nativo** — gratuito até 4 emails/h no free tier, limitado demais para crescimento. Exigiria refatorar auth para usar Supabase Auth em vez do nosso JWT customizado.
- **C) Amazon SES** — mais barato em escala (USD 0.10/1k emails), mais complexo de configurar (DNS, verificação de domínio).

**Recomendação:** Opção A (SendGrid). Menor fricção para começar, escala para 100k, integração já codificada no `services/email_service.py`. Custo zero até 100 emails/dia (ok para primeiros 1k usuários). Para ativar: só precisa setar `SENDGRID_API_KEY=SG.xxxxx` e `EMAIL_FROM=noreply@clubeusa.com` no ambiente de produção (Render, Railway, etc.).

**Status:** PENDENTE

---

### [2026-10-15] Rate limit de registro em-memória (limitação conhecida)

**Contexto:** O rate limit atual (auth: 5 req/min por IP) usa dict em memória. Em instância única é suficiente para 1k usuários. Em múltiplas instâncias (escala horizontal), perde estado.

**Pergunta:** Quando migrar rate limit para Redis/Supabase?

**Recomendação:** Não agir agora. Em instância única (Render free/starter) é suficiente até ~10k usuários. Migrar para Redis quando for para múltiplas instâncias ou notar abusos. Registrado aqui para não esquecer.

**Status:** PENDENTE (baixa prioridade — ok para Fase 0-1)

---

*Atualizado em: 2026-10-15*
