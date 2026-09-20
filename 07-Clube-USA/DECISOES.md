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

### [2026-09-20] Provedor de email para confirmação de cadastro (Fase 0.1)

**Contexto:** O fluxo de confirmação de email está implementado (Fase 0.1). O código suporta Resend e SendGrid via variáveis de ambiente (`RESEND_API_KEY` ou `SENDGRID_API_KEY`). Sem uma chave configurada, o link é apenas logado no console — o cadastro funciona mas o email não é enviado em produção.

**Pergunta:** Qual provedor de email usar e com qual domínio remetente?

**Opções:**

- **A — Resend** (recomendado)
  - Pros: 3.000 emails/mês grátis, API simples, boa reputação de entrega, suporte a domínio próprio fácil.
  - Contras: serviço mais novo (fundado 2022), menos conhecido que SendGrid.
  - Custo: grátis até 3k/mês; $20/mês para 50k. Para os primeiros 1.000 usuários: zero custo.

- **B — SendGrid**
  - Pros: market leader, amplamente testado.
  - Contras: free tier limitado (100/dia), configuração mais burocrática, Twilio dono.
  - Custo: grátis até 100/dia; $19.95/mês para 50k.

- **C — AWS SES**
  - Pros: mais barato em escala ($0,10/1.000), já usado com AWS.
  - Contras: requer conta AWS, setup mais complexo (sandbox → produção), não suportado no código atual (precisaria adicionar).
  - Relevante a partir de ~50k usuários.

**Recomendação:** Resend para os primeiros 1.000 usuários — zero custo, setup em 10 min, domínio verificado em 1 passo. Migrar para SES quando chegar perto de 50k/mês.

**Ação necessária do dono:**
1. Criar conta em resend.com
2. Verificar domínio `clubeusa.com` (adicionar DNS TXT)
3. Gerar API key e adicionar como `RESEND_API_KEY` no Render (Environment > Secret Files)
4. Definir `EMAIL_FROM=noreply@clubeusa.com` no Render

**Status:** PENDENTE

---

*Atualizado em: 2026-06-23*
