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

### [2026-08-19] 0.1 — Email confirmado: obrigatório ou WhatsApp OTP basta?

**Contexto:**
O ROADMAP item 0.1 pede "email confirmado". O sistema atual usa OTP via WhatsApp para confirmar a identidade do membro — o telefone é verificado. Email é um campo opcional, armazenado criptografado, mas nunca verificado por link/código de email.

**Pergunta:**
Para dar 0.1 como concluído, é necessário implementar verificação de email por link (ex: SendGrid), ou o OTP via WhatsApp é suficiente como mecanismo de confirmação de identidade?

**Opções:**

- **Opção A — WhatsApp OTP é suficiente (recomendação):**
  - Prós: já implementado, a plataforma é WhatsApp-first, nenhuma infra adicional de email necessária, menos fricção para o usuário
  - Contras: email fornecido pelo usuário não é verificado; se o usuário errar o email, nunca saberemos
  - Impacto de não fazer: baixo no MVP (auth funciona via WhatsApp)

- **Opção B — Implementar email confirmation via SendGrid/SES:**
  - Prós: emails validados = base mais limpa; abre caminho para comunicação por email no futuro
  - Contras: requer conta SendGrid/SES (custo), mais complexidade no fluxo, mais fricção
  - Custo estimado: ~$0 nos primeiros 100 emails/dia (SendGrid free tier), mas requer criar conta e configurar chave API

**Recomendação:** Opção A para o MVP (WhatsApp OTP basta). Email confirmation pode entrar quando a plataforma começar a usar email como canal de comunicação (newsletters, alertas). Marcar 0.1 como concluído e mover para 0.3.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-19*
