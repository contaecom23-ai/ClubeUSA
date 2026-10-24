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

### [2026-10-24] Provedor de email transacional para confirmação de cadastro

**Contexto:** A feature de confirmação de email (FASE 0.1) está implementada. O código envia o email via SMTP (variáveis de ambiente `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`). Se nenhuma dessas variáveis estiver configurada, o conteúdo do email é apenas logado (modo dev). Para produção, é preciso escolher e configurar um provedor.

**Pergunta:** Qual provedor de email transacional usar?

**Opções:**
- **Opção A — SendGrid (grátis até 100 emails/dia):** Boa reputação de entregabilidade, API REST simples. Prós: tier gratuito cobre as primeiras centenas de usuários facilmente; boa documentação. Contras: requer criar conta, verificar domínio remetente; acima de 100/dia passa a cobrar (~$19,95/mês).
- **Opção B — Postmark:** Especializado em email transacional, reputação excelente. Prós: entregabilidade superior; 100 emails/mês grátis no trial. Contras: pago desde cedo ($15/mês por 10k emails); sem tier gratuito escalável.
- **Opção C — Brevo (ex-Sendinblue, grátis até 300/dia):** Tier gratuito generoso. Prós: 300 emails/dia sem custo cobrem bem os primeiros 1.000 usuários; SMTP nativo. Contras: reputação de entregabilidade levemente inferior ao SendGrid/Postmark.
- **Opção D — SMTP próprio (Gmail/Zoho com domínio clubeusa.com):** Grátis. Prós: zero custo inicial. Contras: limite de envio baixo; reputação de IP sensível; não recomendado para produção acima de ~50 emails/dia.

**Recomendação:** Opção C (Brevo) para lançamento — tier gratuito de 300/dia cobre confortavelmente os primeiros 1.000 usuários sem custo. Migrar para SendGrid quando superar 300 confirmações/dia. Para configurar: criar conta em brevo.com, verificar domínio `clubeusa.com`, e definir as env vars no Render/servidor: `SMTP_HOST=smtp-relay.brevo.com`, `SMTP_PORT=587`, `SMTP_USER=<login brevo>`, `SMTP_PASS=<SMTP key brevo>`, `FROM_EMAIL=noreply@clubeusa.com`.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-24*
