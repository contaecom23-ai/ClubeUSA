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

### [2026-10-06] Provedor de email para confirmação de conta (Fase 0.1)

**Contexto:** Fase 0.1 implementa verificação de email. O código está pronto (SMTP genérico), mas precisa de um provedor configurado em produção. Em desenvolvimento o link é logado no terminal sem enviar email real.

**Pergunta:** Qual provedor de email usar para confirmação de cadastro?

**Opções:**
- **Resend.com** (recomendação): Free até 3.000 emails/mês, SMTP simples, excelente deliverability. Custo: $0 no início, depois $20/mês até 50k emails. Sem lock-in.
- **SendGrid**: Free até 100 emails/dia (muito baixo para crescimento). $19.95/mês para 40k.
- **AWS SES**: $0.10 por 1.000 emails. Mais barato em escala mas requer conta AWS + validação de domínio. Overhead de setup.
- **Mailgun**: Free até 100 emails/dia. Similar ao SendGrid.

**Recomendação:** Resend.com — o melhor custo-benefício para o estágio atual (0 a 10k usuários). Simples de configurar (5 min), boa deliverability, e o free tier cobre os primeiros 3.000 cadastros.

**Para ativar:** Criar conta em resend.com → obter API key → adicionar ao .env as variáveis SMTP_HOST=smtp.resend.com / SMTP_PORT=587 / SMTP_USER=resend / SMTP_PASS=re_XXXXX / EMAIL_FROM=noreply@clubeusa.com. Precisa também verificar o domínio clubeusa.com no Resend.

**Status:** PENDENTE

---

### [2026-10-06] Email obrigatório no cadastro?

**Contexto:** Fase 0.1 implementa verificação de email. O campo `email` foi mantido como opcional na API (para não quebrar clientes existentes). Para que "cadastro válido" (Fase 0.4) funcione, email precisa ser preenchido.

**Pergunta:** Devemos tornar o campo `email` obrigatório no endpoint `POST /auth/register`?

**Opções:**
- **Manter opcional (atual):** Menor fricção no cadastro. Usuários sem email completam a Fase 0.1 mas não têm "cadastro válido" (0.4). Funcional para WhatsApp-first.
- **Tornar obrigatório:** Garante que todo cadastro tem email para confirmação. Aumenta levemente a fricção. Melhor para comunicação e re-engajamento.

**Recomendação:** Tornar obrigatório. A plataforma é para imigrantes no EUA — todos têm email. O benefício (anti-fraude, re-engajamento, comunicação) supera a fricção marginal. É uma mudança de 1 linha de código quando decidir.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-06*
