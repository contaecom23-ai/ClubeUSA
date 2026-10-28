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

### [2026-10-28] Provedor de email para confirmação de conta

**Contexto:** Implementei o fluxo de confirmação de email (Fase 0.1): o backend gera um token seguro de 24h e o endpoint `GET /auth/email/confirm/{token}` confirma e redireciona. Em desenvolvimento o token é apenas logado. Em produção, o código tenta enviar via SendGrid — mas só funciona se `EMAIL_API_KEY` e `EMAIL_FROM` estiverem configurados.

**Pergunta:** Qual provedor de email usar em produção? E o envio de email de confirmação deve ser obrigatório (bloquear acesso sem confirmar) ou opcional (usuário pode usar sem confirmar, mas perde benefícios)?

**Opções:**

- **Opção A — SendGrid (já no código):** Free tier = 100 emails/dia. Fácil configurar. Custo: $0 até ~3k usuarios ativos confirmando email. Pró: simples, confiável. Contra: mais um serviço externo.
- **Opção B — Resend.com:** Free tier = 3k emails/mês. API moderna, melhor DX. Pró: gratis para 1k usuarios. Contra: requer ajuste no código (trocar endpoint).
- **Opção C — Supabase Auth email:** Usar o sistema de email nativo do Supabase (já pago). Pró: zero custo adicional, já integrado. Contra: exigiria migrar auth para Supabase Auth (mudança maior).
- **Opção D — Email opcional, sem bloqueio:** Não bloquear nada sem email confirmado; email confirmado só dá badge/benefício extra. Pró: menor fricção no cadastro, WhatsApp OTP já verifica identidade. Contra: menos dados verificados para Fase 0.4 (cadastro válido).

**Recomendação do Claude:** Opção D no curto prazo + Opção A quando escalar. Para os primeiros 1k usuários, o WhatsApp OTP já é verificação de identidade mais forte que email. Confirmar email é útil para comunicação (newsletters, alertas), mas não deve ser gate de acesso. Use email como confirmação soft: badge "email verificado" + acesso a alertas por email. Escolha SendGrid ou Resend na hora de ligar o email de fato.

**Status:** PENDENTE — aguarda decisão do dono

---

*Atualizado em: 2026-10-28*
