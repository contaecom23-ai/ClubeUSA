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

### [2026-10-11] Provedor de Email para Confirmação (Fase 0.1)

**Contexto:** O sistema de confirmação de email está implementado (código + endpoints) mas requer credenciais SMTP para funcionar em produção. Sem isso, o envio é apenas logado (modo dev — funciona mas não envia). A funcionalidade é necessária para "cadastro válido" (Fase 0.4).

**Pergunta:** Qual provedor de email usar para o Clube USA?

**Opções:**

- **A) Resend (resend.com)**
  - Prós: plano gratuito 3.000 emails/mês, API moderna, excelente deliverability, integração simples (SMTP ou API REST), dashboard limpo
  - Contras: serviço mais novo (menor histórico)
  - Setup: criar conta, verificar domínio, pegar chave API → `SMTP_HOST=smtp.resend.com SMTP_USER=resend SMTP_PASS=re_...`

- **B) SendGrid (Twilio)**
  - Prós: 100 emails/dia grátis (suficiente para beta), muito consolidado no mercado
  - Contras: interface mais complexa, 100/dia pode ser pequeno se crescer rápido
  - Setup: criar conta, verificar domínio, criar API key → `SMTP_HOST=smtp.sendgrid.net SMTP_USER=apikey SMTP_PASS=SG.xxx`

- **C) SMTP do Gmail / Zoho / similar (próprio)**
  - Prós: zero custo, controle total
  - Contras: limites diários baixos (Gmail: 500/dia), reputação de IP doméstico, configuração mais trabalhosa, não escala além de 1-2k
  - Não recomendado para produção

**Recomendação:** **Opção A — Resend**. Plano gratuito cobre os primeiros 3.000 emails/mês (suficiente para Fase 0 e 1). Deliverability excelente. Setup em 10 minutos. Se necessário, upgrade para $20/mês cobre 50.000 emails.

**Ação necessária:** Criar conta em resend.com, verificar o domínio `clubeusa.com`, gerar API key e configurar as variáveis no servidor (Render/Railway/etc.):
```
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=re_XXXXXXXXXXXXX
FROM_EMAIL=noreply@clubeusa.com
```

**Status:** PENDENTE

---

*Atualizado em: 2026-10-11*
