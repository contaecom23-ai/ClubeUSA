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

### [2026-10-26] Provedor de email para confirmação de email em produção

**Contexto:** A feature de confirmação de email (Fase 0.1) está implementada. Em desenvolvimento, o link de verificação é apenas logado no console. Em produção, precisa de um provedor SMTP real para enviar os emails. O código já suporta qualquer provedor SMTP padrão via variáveis de ambiente (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM`).

**Pergunta:** Qual provedor de email usar para envio transacional em produção?

**Opções:**
- **Opção A — SendGrid** (sendgrid.com): Tier gratuito de 100 emails/dia. Configurado via SMTP ou SDK. Mais popular, boa reputação de entregabilidade. Pago acima de 100/dia: ~$19.95/mês para 40k emails. Prós: muito confiável, analytics de abertura. Contras: custo após tier grátis.
- **Opção B — Resend** (resend.com): Tier gratuito de 3.000 emails/mês (100/dia). Interface moderna. Prós: excelente DX, bom gratuito. Contras: mais novo, menos adotado.
- **Opção C — Amazon SES**: $0.10/1.000 emails. Praticamente gratuito na escala dos primeiros 1.000 usuários (~$0.10 total para 1.000 confirmações). Prós: custo mínimo, alta escala. Contras: precisa de conta AWS, configuração de domínio mais complexa.
- **Opção D — Brevo** (ex-Sendinblue): 300 emails/dia grátis. Prós: generoso tier gratuito. Contras: menor reputação de entregabilidade.

**Recomendação:** Para o lançamento (0–1.000 usuários), **Resend ou SendGrid** free tier são suficientes e têm zero custo. A longo prazo (10k+), Amazon SES é o mais econômico. Sugiro **Resend** para simplicidade: UI boa, 3.000 emails grátis/mês cobre bem os primeiros 3.000 usuários, e migrar depois é fácil (só trocar as vars de ambiente).

**Ação necessária:** Criar conta no provedor escolhido, configurar domínio `clubeusa.com` para envio, e adicionar as variáveis `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM` ao ambiente de produção (Render ou onde for deployado).

**Status:** PENDENTE

---

*Atualizado em: 2026-10-26*
