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

### [2026-09-07] Provedor de email transacional para confirmação de cadastro

**Contexto:**
O cadastro agora coleta email opcional e envia um link de confirmação. O código já está implementado para SendGrid (via REST API, sem dep extra além de `requests`). Em dev, o link é apenas logado. Para produção funcionar, é preciso escolher e configurar um provedor.

**Pergunta:**
Qual provedor de email transacional usar para enviar a confirmação de cadastro?

**Opções:**

- **Opção A — SendGrid (já implementado)**
  - Prós: amplamente usado, free tier 100 emails/dia (suficiente para os primeiros 1k usuários), boa entregabilidade, suporte a templates dinâmicos, integração já codificada.
  - Contras: free tier exige verificação de domínio; se escalar além de 100/dia, custa ~$15/mês (6k emails/dia).
  - Configuração: criar conta em sendgrid.com, verificar domínio clubeusa.com, gerar API key → setar `SENDGRID_API_KEY` e `EMAIL_FROM` nas env vars do Render.

- **Opção B — Resend (alternativa moderna)**
  - Prós: API mais simples, free tier 100 emails/dia, boa DX.
  - Contras: exigiria pequena mudança no código (uma função nova em `utils/email.py`).

- **Opção C — SES da AWS**
  - Prós: custo baixíssimo em volume ($0.10/1k emails), excelente entregabilidade.
  - Contras: requer conta AWS, configuração mais complexa (IAM, domínio verificado, saída de sandbox). Faz mais sentido a partir de volume maior.

**Recomendação:**
**Opção A (SendGrid)** — código já pronto, free tier suficiente para os primeiros meses. Migrar para SES quando o volume justificar (>3k emails/dia).

**Ação necessária:**
1. Criar conta SendGrid
2. Verificar domínio `clubeusa.com` (DNS TXT record)
3. Gerar API key com permissão "Mail Send"
4. Adicionar no Render: `EMAIL_PROVIDER=sendgrid`, `SENDGRID_API_KEY=SG.xxx`, `EMAIL_FROM=no-reply@clubeusa.com`

**Status:** PENDENTE

---

*Atualizado em: 2026-09-07*
