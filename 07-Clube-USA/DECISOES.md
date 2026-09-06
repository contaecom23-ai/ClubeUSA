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

### [2026-09-06] Serviço de envio de email para confirmação de cadastro (Phase 0.1)

**Contexto:** A Phase 0.1 exige "email confirmado". O cadastro atual usa OTP via WhatsApp (confirma posse do número, mas não do email). Para confirmar email, precisa de um serviço de envio transacional. Já existe `email_hash`/`email_enc` no schema e o campo `email` é aceito no cadastro — mas não há `email_confirmed` na tabela nem nenhum fluxo de verificação por email.

**Pergunta:** Qual serviço de email transacional usar e quem configura as credenciais?

**Opções:**

- **Opção A — Resend** (resend.com)
  - Prós: Freemium generoso (3.000 emails/mês free), DX excelente, integração Python simples, domínio próprio fácil
  - Contras: Serviço relativamente novo (menos histórico de deliverability)
  - Custo: $0 até 3k emails/mês → $20/mês até 50k

- **Opção B — SendGrid** (twilio)
  - Prós: Referência do mercado, 100 emails/dia free, reputação consolidada
  - Contras: UI mais complexa, free tier muito limitado, Twilio é corporativo
  - Custo: $0 até 100/dia → $19.95/mês até 100k

- **Opção C — Mailgun**
  - Prós: Histórico sólido, bom para devs, API clara
  - Contras: Free tier expirou (100 emails/dia apenas 30 dias de trial)
  - Custo: $15/mês para 10k emails

- **Opção D — Adiar por enquanto** (não implementar email confirmado)
  - Prós: O WhatsApp OTP já confirma identidade (mais forte que email); economiza tempo de dev agora
  - Contras: Não fecha Phase 0.1 formalmente; sem email de marketing ou recuperação futura
  - Obs: Realista para os primeiros 1.000 usuários — email pode ser adicionado depois sem quebrar nada

**Recomendação do Claude:** **Opção A (Resend)** se quiser fechar a Phase 0.1 formalmente — free tier é adequado para os primeiros 1.000 usuários, API simples, domínio clubeusa.com pode ser configurado em 10 minutos. Alternativamente, **Opção D** é defensável: o fluxo WhatsApp OTP já é melhor que email (número real, não descartável). Decida se email confirmado é requisito de negócio real ou formalidade.

**O que o Claude precisa para implementar:**
1. Sua escolha entre A/B/C/D
2. Se A/B/C: a API key e o domínio remetente (ex: noreply@clubeusa.com)

**Status:** PENDENTE

---

*Atualizado em: 2026-09-06*
