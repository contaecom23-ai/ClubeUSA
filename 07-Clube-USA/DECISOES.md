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

### [2026-11-05] Email confirmation para fechar Fase 0.1

**Contexto:**
O cadastro atual é 100% via telefone (WhatsApp OTP). Email é campo opcional sem verificação. Para completar a Fase 0.1 ("email confirmado") e a definição de "cadastro válido" da Fase 0.4, precisamos de verificação de email.

**Pergunta:**
Qual serviço de email usar para enviar links de confirmação?

**Opções:**
- **A — Resend (resend.com):** gratuito até 3.000 emails/mês, fácil integração, boa entregabilidade. Exige criar conta + API key.
- **B — SendGrid:** gratuito até 100 emails/dia (plano free). Mais complexo de configurar. Muito usado, boa reputação.
- **C — AWS SES:** centavos por 1.000 emails, escala bem, mas exige conta AWS + configuração de domínio.
- **D — Adiar:** tratar email como opcional permanentemente; "cadastro válido" = apenas telefone verificado (OTP WhatsApp) + ≥1 ação real. Simplifica mas perde o canal de email.

**Prós/Contras:**
- A e B: fáceis, prontos em <1 hora, mas dependem de conta externa gratuita (limite)
- C: barato em escala, mas setup mais demorado
- D: elimina dependência externa — para os primeiros 1.000 usuários, o WhatsApp já é canal suficiente. Risco: perde email como canal de retargeting/retenção.

**Recomendação do Claude:**
**Opção D (curto prazo) + A (médio prazo).** Para os primeiros 1.000 usuários, o WhatsApp já é o canal principal — email é secundário. Avançar na Fase 1 (tração) é mais urgente do que email confirmation. Quando o produto estiver em produção e os primeiros usuários chegarem, criar uma conta Resend e implementar a confirmação em 2-3h. Registrar aqui quando isso for prioridade.

**Status:** PENDENTE — aguardando decisão do dono

---

*Atualizado em: 2026-11-05*
