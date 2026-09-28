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

### [2026-09-28] Fase 0.1 — O que conta como "email confirmado"?

**Contexto:**  
O roadmap pede "Cadastro + perfil mínimo + email confirmado" (0.1). O sistema atual autentica via OTP no WhatsApp (número de telefone verificado) e armazena email opcionalmente (sem confirmação). O fluxo de cadastro funciona, mas email não é verificado.

**Pergunta:**  
Precisamos de confirmação de email separada, além do OTP via WhatsApp?

**Opções:**

- **Opção A — OTP WhatsApp = confirmação suficiente (recomendado)**  
  Pro: WhatsApp OTP é verificação mais forte que email (mais difícil de falsificar). Menos fricção para o usuário. Nenhum custo adicional de infra.  
  Contra: Não capturamos email confirmado para campanhas futuras de email marketing.

- **Opção B — Adicionar confirmação de email (link clicável)**  
  Pro: Permite email marketing. Email confirmado = dado de melhor qualidade.  
  Contra: Exige provedor de email transacional (SendGrid/Resend/AWS SES — custo ~$0-$20/mês dependendo volume). Adiciona fricção no cadastro (o usuário precisa abrir o email). Maior risco de abandono.

- **Opção C — Email opcional, não confirmado (status quo)**  
  Pro: Simples. Email não é central para o produto (WhatsApp-first).  
  Contra: Email sem verificação tem qualidade baixa para marketing futuro.

**Recomendação:**  
Opção A no curto prazo. O OTP via WhatsApp já confirma identidade real — é mais robusto que email. Email marketing pode vir depois quando tivermos volume para justificar o custo. Marcar 0.1 como concluído se você concordar.

**Status:** PENDENTE

---

*Atualizado em: 2026-09-28*
