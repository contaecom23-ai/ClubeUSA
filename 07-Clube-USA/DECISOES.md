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

### [2026-08-24] Provedor de email para confirmação de email (Fase 0.1)

**Contexto:** O cadastro atual é 100% via telefone + OTP WhatsApp (prova de posse do número). Email é coletado mas não verificado. Para completar o item 0.1 ("email confirmado") e para o 0.4 (anti-fraude), precisamos enviar emails de verificação.

**Pergunta:** Qual provedor de email transacional usar para confirmação de cadastro?

**Opções:**
- **Resend** (resend.com): simples, 100 emails/dia gratuitos, API moderna, fácil integração. Prós: setup em 5 min, gratuito para começar. Contras: menos features avançadas.
- **SendGrid**: mais robusto, 100 emails/dia grátis no tier free. Prós: market leader, analytics built-in. Contras: interface mais complexa, setup mais demorado.
- **Mailgun**: 1.000 emails/mês grátis. Prós: bom custo-benefício. Contras: domínio próprio necessário para produção.
- **Postmark**: melhor entregabilidade. Prós: excelente para transacional. Contras: pago desde o início (~$15/mês).

**Recomendação:** **Resend** — setup em 5 minutos, API Python clean, free tier suficiente para os primeiros 1.000 usuários, e pode escalar. Conta gratuita em resend.com, precisa verificar o domínio clubeusa.com.

**Impacto se não decidir:** Fase 0.1 fica parcialmente pendente; a plataforma funciona sem email (autenticação por WhatsApp), mas perdemos um canal de reengajamento e anti-spam.

**Próximos passos após aprovação:**
1. Criar conta no Resend e verificar domínio clubeusa.com
2. Adicionar `RESEND_API_KEY` no .env e no Render
3. Claude implementa: token de verificação + rota `/auth/email/verify/{token}` + campo `email_verified_at` na tabela `members`

**Status:** PENDENTE

---

### [2026-08-24] Formato da URL de referral (Fase 0.2)

**Contexto:** O sistema de referral está implementado e funcional. O link gerado é `{APP_URL}?ref=CODE8CHAR` (ex: `clubeusa.com?ref=ABCD1234`). O ROADMAP original menciona `clubeusa.com/i/joao` (slug personalizado com nome).

**Pergunta:** Quer manter o formato `?ref=CODE` atual ou implementar slug personalizado tipo `/i/joao`?

**Opções:**
- **Manter `?ref=CODE`**: já implementado, funciona hoje. Prós: zero esforço. Contras: link menos memorável/social.
- **Slug personalizado `/i/joao`**: ex: `clubeusa.com/i/maria`. Prós: mais viral, memorizável, "dono" do link. Contras: colisões de nome, moderação de slugs ofensivos, requer campo extra no DB e rota nova.

**Recomendação:** Manter `?ref=CODE` para os primeiros 1.000 usuários — zero fricção, zero risco. Reavaliar slug personalizado na Fase 1.3 (influenciadores), onde o link "de marca" tem mais valor.

**Status:** PENDENTE (baixa urgência — atual funciona bem)

---

*Atualizado em: 2026-08-24*
