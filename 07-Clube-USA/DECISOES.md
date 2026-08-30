# DECISOES — Clube USA

> Fila de decisoes que dependem do dono do produto (voce).
> Para cada item: data, contexto, pergunta objetiva, opcoes com pros/contras e recomendacao do Claude.
> Claude NAO age em itens desta lista sem sua aprovacao explicita.

---

## Como usar

Quando o Claude travar em algo que so voce pode decidir (orcamento, precos, escolhas de produto/negocio, aprovacao de gasto, chaves/contas externas, direcao estrategica, qualquer coisa irreversivel ou com custo), ele registra aqui e segue para outra tarefa.

Formato de cada entrada:

```
### [DATA] Titulo da decisao
**Contexto:** ...
**Pergunta:** ...
**Opcoes:**
- Opcao A: pros / contras
- Opcao B: pros / contras
**Recomendacao:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## Decisoes Pendentes

### [2026-08-30] Provedor de email para confirmacao de cadastro

**Contexto:** A Fase 0.1 implementou o fluxo de email confirmation. O codigo suporta 3 modos via `EMAIL_PROVIDER`: `dev` (log no console), `smtp` (qualquer servidor SMTP) e `resend` (API Resend). Para producao, e necessario escolher e configurar um provedor real.

**Pergunta:** Qual provedor de email usar para envio transacional (confirmacao de cadastro)?

**Opcoes:**
- **Resend** (`EMAIL_PROVIDER=resend`): API moderna, free tier generoso (3.000 emails/mes, sem cartao), SDK simples, excelente deliverability. Unico ponto de falha: necessario criar conta em resend.com e adicionar `RESEND_API_KEY` + dominio verificado. **Recomendado para o start.**
- **Gmail SMTP** (`EMAIL_PROVIDER=smtp`): Gratis ate 500/dia (conta pessoal) ou 2.000/dia (Google Workspace). Requer `EMAIL_SMTP_*` vars. Funciona imediatamente com conta Google existente, mas Google pode bloquear por parecer spam se dominio nao estiver configurado.
- **SendGrid** (`EMAIL_PROVIDER=smtp` com relay deles): Free tier 100/dia, muito confiavel, mais complexo de configurar. Faz sentido se ja escalar para 10k+ emails/mes.

**Recomendacao:** Resend. Mais simples, free tier suficiente para os primeiros 1.000 usuarios, deliverability profissional, dominio proprio verificado aumenta taxa de entrega. Passos: (1) criar conta em resend.com, (2) verificar dominio clubeusa.com no painel, (3) adicionar `RESEND_API_KEY=re_...` e `EMAIL_FROM=noreply@clubeusa.com` no .env do servidor, (4) definir `EMAIL_PROVIDER=resend`.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-30*
