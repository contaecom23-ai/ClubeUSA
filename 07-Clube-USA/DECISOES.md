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

### [2026-08-25] Fase 0.1 — Email confirmado vs. verificação por telefone (OTP)

**Contexto:** O ROADMAP 0.1 diz "email confirmado", mas o sistema atual é WhatsApp-first com autenticação por OTP de telefone. Email é campo opcional no cadastro — é armazenado criptografado, mas não há fluxo de confirmação (sem email enviado, sem link de verificação, sem coluna `email_confirmed` no banco). O OTP de WhatsApp já confirma que o número é real.

**Pergunta:** Para o Clube USA, "cadastro válido" (usado em 0.1 e 0.4) exige confirmação de email, ou a verificação por OTP de telefone já é suficiente?

**Opções:**
- **A) Manter WhatsApp-first — email opcional, sem confirmação (recomendado):**
  - Prós: menor fricção no cadastro (1 etapa em vez de 2), alinhado com o público-alvo (imigrantes que já vivem no WhatsApp), evita problemas de deliverability de email, OTP já prova posse do número.
  - Contras: sem email confirmado, canal de email marketing fica limitado a quem forneceu email voluntariamente.
- **B) Adicionar confirmação de email obrigatória:**
  - Prós: abre canal de email (newsletters, reativação), pode ser exigência de parceiros futuros.
  - Contras: adiciona fricção no cadastro (pode reduzir conversão em 20-40%), exige integração com SendGrid/Resend (~$20/mês a partir de certo volume), mais complexidade no fluxo.

**Recomendação:** Opção A. O WhatsApp é o canal principal e o OTP já valida posse do número. Adicionar email confirmado aumenta fricção sem benefício proporcional para os primeiros 1.000 usuários. Revisitar na Fase 3 quando precisar de email para reativação ou newsletter. Se escolher B, o Claude implementa a integração com Resend (grátis até 3k emails/mês) sem custo adicional imediato.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-25*
