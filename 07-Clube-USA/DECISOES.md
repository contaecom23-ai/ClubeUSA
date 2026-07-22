# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-07-22] Provedor de envio de e-mail transacional

**Contexto:**
O sistema de confirmação de e-mail e reset de senha já está implementado e funcionando. O código tem um backend plugável (`EMAIL_BACKEND` no `.env`). Em dev/teste imprime no console. Para produção precisa de um provedor real.

**Pergunta:**
Qual provedor de e-mail usar para envio transacional (confirmação de conta, reset de senha)?

**Opções:**

- **Resend** (`resend.com`)
  - Prós: API moderna e simples, 100 e-mails/dia grátis, excelente deliverability, dashboard limpo, SDK Python disponível
  - Contras: empresa nova (fundada 2022), menor histórico que SendGrid
  - Custo: grátis até 3.000/mês; USD 20/mês para até 50k
  - **← Minha recomendação para começar**

- **SendGrid** (Twilio)
  - Prós: líder de mercado, muito maduro, 100 e-mails/dia grátis
  - Contras: painel mais complexo, integração um pouco mais trabalhosa, tem histórico de problemas de deliverability em contas novas

- **AWS SES**
  - Prós: custo baixíssimo ($0.10/1k e-mails), escala infinita
  - Contras: requer conta AWS, sandbox inicial com restrições, mais trabalhoso de configurar
  - Faz mais sentido na Fase 2+ (> 10k usuários)

**O que fazer para ativar:**
1. Escolha o provedor
2. Crie a conta e obtenha a API key
3. Defina `EMAIL_BACKEND=resend` (ou `sendgrid`) e `RESEND_API_KEY=...` no `.env` de produção
4. Nenhuma mudança de código necessária

**Status:** PENDENTE

---

### [2026-07-22] URL de produção e domínio

**Contexto:**
O `APP_URL` no `.env` define a base dos links nos e-mails (ex: `APP_URL/auth/confirm-email?token=...`). Em dev está como `http://localhost:8000`.

**Pergunta:**
Qual será o domínio de produção da plataforma?

**Por que importa agora:**
Precisa estar correto antes de lançar para que os links nos e-mails funcionem.

**Exemplo:** `https://api.clubeusa.com` ou `https://clubeusa.com`

**Status:** PENDENTE

---

*Atualizado em: 2026-07-22*
