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

### [2026-11-09] Provedor de email transacional para confirmação de conta (Fase 0.1)

**Contexto:**
O backend de confirmação de email (Fase 0.1) está implementado e pronto. O único bloqueio
para colocar em produção é a escolha e configuração do provedor de email. Sem isso,
o sistema funciona mas não envia emails reais (em dev, loga o link no console).

**Pergunta:**
Qual provedor de email usar para os emails transacionais (confirmação de conta, futuros
alertas de preço)?

**Opções:**

| Provedor | Custo | Setup | Escala até 1M |
|---|---|---|---|
| **Resend** (já no código) | 3.000/mês free, depois $20/mês até 50k | 10 min (API key + DNS) | Sim, sem mudar código |
| **SendGrid** | 100/dia free (~3k/mês), depois $19.95/mês | 20 min | Sim, mudaria 1 arquivo |
| **AWS SES** | $0.10/1.000 emails (mais barato em escala) | 1-2h (AWS account + DNS) | Mais barato mas complexo |

**Recomendação:** Resend — plano free suficiente para os primeiros 3.000 usuários,
API mais simples, já está integrado no código. Troca para AWS SES quando passar de
50k emails/mês (~10k usuários ativos).

**O que você precisa fazer:**
1. Criar conta em resend.com (grátis)
2. Verificar domínio `clubeusa.com` (adicionar 2 registros DNS)
3. Criar API key em Account → API Keys
4. Adicionar ao Render (ou .env): `RESEND_API_KEY=re_...` e `EMAIL_FROM=noreply@clubeusa.com`

**Status:** PENDENTE

---

*Atualizado em: 2026-11-09*
