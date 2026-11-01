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

### [2026-11-01] Escolha do provedor de email transacional

**Contexto:** A Fase 0.1 implementou o fluxo completo de confirmação de email (token seguro, endpoints, testes). Para funcionar em produção, a variável `EMAIL_PROVIDER` precisa ser configurada com um provedor real. Duas opções já codificadas no `services/email_service.py`.

**Pergunta:** Qual provedor de email transacional usar para enviar os links de confirmação?

**Opções:**

- **Opção A — SendGrid** (`EMAIL_PROVIDER=sendgrid`)
  - Prós: plano gratuito generoso (100 emails/dia para sempre), API REST simples, excelente deliverability, fácil setup, SDK oficial
  - Contras: conta a criar (gratuita), `SENDGRID_API_KEY` nas env vars
  - Custo: $0 até 100 emails/dia; ~$20/mês acima de 50k/mês
  - Adequado para: 1k a 100k usuários sem custo inicial

- **Opção B — SMTP próprio** (`EMAIL_PROVIDER=smtp`)
  - Prós: sem conta extra se já tiver servidor SMTP (ex: Google Workspace, Zoho, AWS SES via SMTP)
  - Contras: deliverability mais fraca com provedores genéricos; Google Workspace custa $6/usuário/mês; AWS SES SMTP boa opção mas precisa sair de sandbox (aprovação AWS)
  - Custo: variável — $0 com SES em escala baixa, mas setup mais trabalhoso

- **Opção C — Resend** (`EMAIL_PROVIDER=sendgrid` com ajuste mínimo no código)
  - Prós: produto mais novo, API compatível com SendGrid, plano grátis 3k emails/mês, painel moderno
  - Contras: menos estabelecido; requer código ajuste pequeno (não está codificado ainda)
  - Custo: grátis até 3k emails/mês, depois $20/mês

**Recomendação:** **Opção A (SendGrid)** para começar. Plano gratuito aguenta os primeiros 1.000 usuários sem custo. Setup de 5 minutos (criar conta, gerar API key, adicionar `SENDGRID_API_KEY` e `EMAIL_FROM` nas env vars do Render/servidor). Não cria dependência técnica irreversível — trocar de provedor é mudar 1 variável de ambiente.

**Ação necessária:**
1. Criar conta em sendgrid.com (gratuita)
2. Criar API Key com permissão "Mail Send"
3. Adicionar no ambiente de produção:
   - `EMAIL_PROVIDER=sendgrid`
   - `SENDGRID_API_KEY=SG.xxx...`
   - `EMAIL_FROM=noreply@clubeusa.com` (ou o domínio que tiver)
4. Verificar domínio remetente no SendGrid (recomendado para deliverability)

**Status:** PENDENTE

---

*Atualizado em: 2026-11-01*
