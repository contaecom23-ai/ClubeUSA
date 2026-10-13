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

### [2026-10-13] Provedor de email transacional para produção

**Contexto:** A Fase 0.1 implementou confirmação de email via SMTP. Em dev/staging, sem `SMTP_*` configurado, a URL de verificação é apenas logada (funciona para testes). Em produção, você precisa de um provedor real.

**Pergunta:** Qual provedor SMTP usar em produção?

**Opções:**
- **A) SendGrid (recomendado):** Free até 100 emails/dia. Confiabilidade alta, painel de analytics, fácil de configurar. `SMTP_HOST=smtp.sendgrid.net`, `SMTP_USER=apikey`, `SMTP_PASS=SG.xxx`. Pros: free tier generoso para MVP, boa entregabilidade. Cons: conta a criar.
- **B) Gmail (Google Workspace / conta pessoal):** Zero custo adicional se já tem conta Google. Mais fácil de configurar rapidamente. Pros: imediato. Cons: limite diário ~500 emails no Gmail gratuito (suficiente para MVP), requer App Password ativo.
- **C) AWS SES:** Custo muito baixo (US$0.10/1000 emails). Pros: escala bem. Cons: requer conta AWS, verificação de domínio, mais setup inicial — overkill para MVP.

**Recomendação:** SendGrid opção A — free tier cobre bem os primeiros 1.000 usuários, entregabilidade profissional, e a configuração é 3 variáveis de ambiente. Criar conta em sendgrid.com, gerar API key e adicionar ao ambiente de produção.

**Ação necessária:** Após escolher, adicionar ao `.env` de produção:
```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.<sua-chave>
FROM_EMAIL=noreply@clubeusa.com
```

**Status:** PENDENTE

---

*Atualizado em: 2026-10-13*
