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

### [2026-09-24] Provedor de email para confirmação de cadastro

**Contexto:** A infraestrutura de confirmação de email está pronta (migration SQL + endpoints + service). Para funcionar em produção, precisa de um provedor SMTP configurado via variáveis de ambiente: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`.

**Pergunta:** Qual provedor SMTP usar em produção?

**Opções:**
- **SendGrid** (tier free: 100 emails/dia): prós — mais popular, boa reputação, API REST disponível; contras — free tier apertado para crescimento
- **Resend** (tier free: 3.000 emails/mês): prós — moderno, developer-friendly, plano free generoso, domínio fácil de verificar; contras — menor histórico de mercado
- **AWS SES** ($0,10/1.000 emails): prós — mais barato em escala, confiável; contras — requer conta AWS, configuração mais complexa (verificação de domínio, saída do sandbox)
- **Gmail SMTP** (conta Google): prós — zero custo para começar; contras — limite de 500/dia, reputação de spam mais baixa, inadequado para produção escalável

**Recomendação:** **Resend** para começar — plano free cobre os primeiros 1.000 usuários com folga, API simples, e troca de provedor é trivial (só mudar as env vars). Se o volume escalar para >3k emails/mês, migrar para AWS SES.

**Ação necessária após decisão:**
1. Criar conta no provedor escolhido
2. Verificar domínio `clubeusa.com`
3. Aplicar migration `db/email_confirmation_migration.sql` no Supabase (Dashboard > SQL Editor)
4. Configurar no Render: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`

**Status:** PENDENTE

---

*Atualizado em: 2026-09-24*
