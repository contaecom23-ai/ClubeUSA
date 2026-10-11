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

### [2026-10-11] Provedor de email para confirmação de cadastro

**Contexto:** O sistema de confirmação de email (Fase 0.1) foi implementado. O código abstrai o envio atrás de `email_service.py`. Em desenvolvimento, o token é logado. Em produção, precisa de um provedor real configurado via variáveis de ambiente.

**Pergunta:** Qual provedor de email usar para enviar os emails de confirmação de conta?

**Opções:**

- **Resend** (`EMAIL_PROVIDER=resend` + `RESEND_API_KEY=...`):
  - *Pros:* Free tier 3.000 emails/mês, API simples e moderna, boa reputação de entrega, criado para devs.
  - *Contras:* Menor histórico que SendGrid; free tier pode ser apertado se crescer rápido.

- **SendGrid** (`EMAIL_PROVIDER=sendgrid` + `SENDGRID_API_KEY=...`):
  - *Pros:* Líder de mercado, free tier 100 emails/dia, muito documentado.
  - *Contras:* Interface mais complexa; free tier baixo (~3.000/mês se usar todos os dias).

- **Amazon SES** (requer implementação adicional no `email_service.py`):
  - *Pros:* Custo baixíssimo em escala ($0.10/1.000), ideal para 10k–1M.
  - *Contras:* Exige conta AWS + verificação de domínio; overhead de setup maior.

**Recomendação:** **Resend** para começar — free tier suficiente para os primeiros 1.000 usuários, API limpa, e pode ser trocado por SES depois sem reescrever a lógica (só `email_service.py`). Próximos passos: criar conta em resend.com, verificar domínio clubeusa.com, pegar a API key e adicionar `EMAIL_PROVIDER=resend` + `RESEND_API_KEY=re_...` nas env vars do Render.

**Status:** PENDENTE

---

*Atualizado em: 2026-10-11*
