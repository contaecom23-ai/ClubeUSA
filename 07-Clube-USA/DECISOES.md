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

### [2026-07-05] Provedor de email para confirmação de conta

**Contexto:** O backend (Fase 0.1) já tem a lógica de envio de email por SMTP. Em modo dev, o link de confirmação aparece no console. Para produção, precisamos de um provedor SMTP configurado. A escolha afeta custo e entregabilidade.

**Pergunta:** Qual provedor de email transacional usar para o envio de confirmação de conta (e futuros emails)?

**Opções:**

- **Opção A — Resend (resend.com):** $0 nos primeiros 3.000 emails/mês, depois $20/mês. API simples, alta entregabilidade, ótima DX. Sem SMTP nativo — precisaria de um adapter, mas eles têm SDK Python.
  - Prós: Generoso no free tier, moderno, rápido de integrar.
  - Contras: Não é SMTP puro (precisaria de pequena adaptação no código).

- **Opção B — SendGrid (Twilio):** Free tier com 100 emails/dia (~3k/mês). SMTP disponível — plugaria direto no código atual sem nenhuma mudança.
  - Prós: Zero mudança de código, free tier suficiente para os primeiros 1k usuários.
  - Contras: Interface mais complexa, reputação de entregabilidade um pouco inferior ao Resend.

- **Opção C — AWS SES:** ~$0,10 por 1k emails. Baratíssimo em escala. Requer conta AWS e verificação de domínio.
  - Prós: Escala sem custo explosivo, SMTP disponível.
  - Contras: Setup mais trabalhoso, requer conta AWS ativa.

- **Opção D — Gmail SMTP (temporário):** Gratuito, mas limitado a 500 emails/dia e sujeito a bloqueios.
  - Prós: Imediato para testar.
  - Contras: Não é solução de produção. Bloqueável pelo Google. Não recomendado para uso real.

**Recomendação:** **SendGrid (Opção B)** para o lançamento — zero mudança de código, free tier cobre os primeiros 1k usuários, e quando escalar para 10k+ migrar para AWS SES. Resend também é boa opção se quiser a melhor DX.

**O que você precisa fazer:**
1. Criar conta no SendGrid (ou provedor escolhido)
2. Verificar seu domínio (clubeusa.com)
3. Configurar as env vars no servidor: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM`

**Status:** PENDENTE

---

### [2026-07-05] URL de produção do backend (FRONTEND_URL / API_URL)

**Contexto:** Os arquivos HTML do frontend têm `const API_URL = 'http://localhost:8000/api/v1'` hardcoded. Para produção, isso precisa apontar para o domínio real da API. Similarmente, o backend precisa saber o `FRONTEND_URL` para gerar o link de verificação no email.

**Pergunta:** Onde o backend FastAPI vai rodar em produção? (ex: Railway, Render, VPS, Supabase Edge Functions?)

**Opções:**

- **Opção A — Railway.app:** Deploy via GitHub, free tier limitado, $5/mês no plano básico. Mais simples.
- **Opção B — Render.com:** Free tier com cold start, $7/mês no plano básico. Similar ao Railway.
- **Opção C — VPS (DigitalOcean/Hetzner):** $4–6/mês, controle total, requer setup de nginx/systemd.
- **Opção D — AWS/GCP/Azure:** Mais complexo, mais caro no início, mas escala infinitamente.

**Recomendação:** **Railway ou Render** para começar — deploy em minutos, sem ops. Quando chegar a 10k usuários, avaliar migrar para VPS ou AWS.

**O que você precisa fazer:**
1. Escolher e configurar o host
2. Definir o domínio da API (ex: `api.clubeusa.com`)
3. Atualizar `API_URL` nos HTMLs (ou criar um `config.js` centralizado)

**Status:** PENDENTE

---

*Atualizado em: 2026-07-05*
