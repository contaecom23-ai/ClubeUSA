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

### [2026-10-25] Provedor de email transacional para confirmação de conta

**Contexto:** A Fase 0.1 (email confirmado) exige envio de email. O backend já foi implementado com abstração de provedor — sem chave configurada, os links são apenas logados no console (modo dev). Para produção precisamos de um provedor real.

**Pergunta:** Qual provedor de email transacional usar?

**Opções:**
- **Resend.com** (recomendado): API moderna, free tier 3.000 emails/mês, setup em 5 min, domínio verificado por DNS. Integração já codificada em `services/email_service.py`. Custo além do free: ~$20/mês para 50k emails.
- **SendGrid**: Mais maduro, 100 emails/dia no free tier (limitante), mais complexo de configurar. $19.95/mês a partir de 50k.
- **AWS SES**: Mais barato em escala ($0.10 por 1k), mas requer conta AWS, região, IAM policy, etc. Overhead desnecessário para 0-1k usuários.

**Recomendação:** **Resend.com**. Free tier cobre confortavelmente os primeiros 1-2k usuários sem custo. Setup: criar conta, verificar domínio `clubeusa.com`, gerar API key e adicionar `RESEND_API_KEY=re_...` no `.env` e nos secrets do Render.

**Para ativar em produção:**
1. Criar conta em resend.com
2. Verificar domínio `clubeusa.com` (adicionar registros DNS: SPF, DKIM)
3. Gerar API Key
4. Adicionar ao `.env`: `RESEND_API_KEY=re_...` e `EMAIL_FROM=noreply@clubeusa.com`
5. No Render: Settings > Environment > adicionar as mesmas vars

**Status:** PENDENTE (aguarda aprovação e criação de conta pelo dono)

---

*Atualizado em: 2026-10-25*
