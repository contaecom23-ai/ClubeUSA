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

### [2026-08-17] Fase 0.1 — Estratégia de confirmação de identidade (email vs WhatsApp OTP)

**Contexto:**
O ROADMAP pede "email confirmado" na Fase 0.1, mas a arquitetura atual usa **WhatsApp OTP** (código de 6 dígitos via Z-API) como único mecanismo de auth. O campo `email` existe no schema (nullable), mas não há fluxo de confirmação implementado.

Problema: email confirmado requer um provedor de envio de email (SendGrid, Mailgun, Resend, etc.) com chave paga ou free-tier limitado — e pode ser uma mudança arquitetural relevante.

**Pergunta:**
Qual estratégia de confirmação de identidade adotar para o cadastro?

**Opções:**
- **Opção A — Manter WhatsApp OTP como único auth** (status quo): Pro: mais forte que email (verifica número real, que é o contato principal de brasileiros nos EUA), já implementado, zero custo extra. Contra: exige WhatsApp ativo, depende da Z-API.
- **Opção B — Adicionar email PARALELO ao WhatsApp OTP**: usuário pode cadastrar e confirmar email (opcional/obrigatório). Pro: atende exatamente o que o roadmap pede; útil para notificações e recuperação. Contra: precisa de provedor de email (escolher + configurar + custo). Qual provedor? Resend.com tem free tier generoso (3k emails/mês).
- **Opção C — Usar Supabase Auth nativo** (email magic link ou senha): Pro: email confirmado "de graça" via Supabase (até 30k emails/mês no tier pago). Contra: migração arquitetural significativa — a tabela `members` usa auth.uid() nas RLS mas a auth atual é JWT próprio; seria necessário alinhar as duas.

**Recomendação do Claude:**
Opção B com Resend.com (free tier). É cirúrgico — adiciona email ao fluxo existente sem reescrever a auth. O campo já existe no schema. Implementação: backend `/auth/email/confirm` envia link tokenizado; frontend adiciona campo de email no cadastro; confirmação muda `email_verified` para TRUE. Custo: zero no início. **Mas precisa que o dono configure `RESEND_API_KEY` no env.**

**Próximo passo após decisão:**
O Claude implementa. Basta responder qual Opção (A, B ou C) e, se B, confirmar uso do Resend.

**Status:** PENDENTE

---

### [2026-08-17] Fase 0.1 — Supabase: credenciais e schema executado?

**Contexto:**
Todo o código do backend assume `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` configurados. O `schema.sql` + migrations precisam ter sido executados no Supabase para o sistema funcionar.

**Pergunta:**
O Supabase já está configurado? O schema já foi executado? Ou ainda precisamos de:
1. Criar projeto no Supabase
2. Executar `schema.sql` + migrations no SQL editor
3. Configurar as env vars no servidor/Render

**Status:** PENDENTE — sem isso, nada do backend funciona em produção.

---

*Atualizado em: 2026-08-17*
