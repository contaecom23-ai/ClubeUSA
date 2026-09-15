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

### [2026-09-15] Provedor de email para confirmação (Fase 0.1)

**Contexto:** O backend de confirmação de email está pronto (tabela, tokens, rotas, templates). Para funcionar em produção, precisamos de um serviço de envio de email. Em desenvolvimento, o sistema só loga o link (sem custo). A escolha é entre dois provedores modernos e baratos para o volume inicial (< 1.000 usuários).

**Pergunta:** Qual provedor de email usar para enviar o link de confirmação de cadastro?

**Opções:**

- **Opção A — Resend (resend.com):**
  - ✅ Plano gratuito: 3.000 emails/mês, 100/dia — suficiente para 1k usuários
  - ✅ API moderna, DX excelente, SDK Python simples
  - ✅ Reputação crescente, fácil de configurar domínio
  - ✅ Sem cartão de crédito no plano free
  - ❌ Serviço relativamente novo (fundado 2022) — menos track record que SendGrid
  - **Config:** `EMAIL_PROVIDER=resend`, `RESEND_API_KEY=re_...`, verificar domínio clubeusa.com no painel Resend

- **Opção B — SendGrid (sendgrid.com/twilio):**
  - ✅ Plano gratuito: 100 emails/dia (3.000/mês) — mesma capacidade
  - ✅ Mais estabelecido (Twilio), alta deliverability
  - ❌ Interface mais complexa, onboarding mais burocrático
  - ❌ Suporte piorou após aquisição pela Twilio
  - **Config:** `EMAIL_PROVIDER=sendgrid`, `SENDGRID_API_KEY=SG....`, verificar domínio

- **Opção C — Não implementar por agora:**
  - ✅ Zero custo, zero configuração
  - ❌ Fase 0.1 não está 100% completa sem confirmação funcionando
  - ❌ Sem email confirmado, a definição de "cadastro válido" (Fase 0.4) fica prejudicada
  - Pode fazer sentido se você quiser lançar sem email obrigatório (auth é por WhatsApp)

**Recomendação:** **Opção A (Resend)** — melhor DX, plano free suficiente para os primeiros 1k usuários, sem burocracia. O código já suporta ambos. Para ativar: criar conta em resend.com, verificar o domínio clubeusa.com, pegar a API key e configurar as env vars. Se preferir adiar (Opção C), tudo continua funcionando — confirmação de email só não é enviada em produção, mas o fluxo de auth por WhatsApp já funciona.

**Status:** PENDENTE

---

*Atualizado em: 2026-09-15*
