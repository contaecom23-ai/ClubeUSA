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

### [2026-09-07] Provedor de email transacional para confirmação de conta

**Contexto:**
A Fase 0.1 implementou o fluxo completo de confirmação de email (geração de token seguro, endpoints, email HTML). O código está pronto para produção, mas precisa de uma chave de API de um provedor de email configurada via env var `SENDGRID_API_KEY` (suporta SendGrid por padrão).

**Pergunta:**
Qual provedor de email transacional usar e qual conta configurar?

**Opções:**
- **Opção A — SendGrid (já suportado no código):**
  - Prós: gratuito até 100 emails/dia, fácil configurar, 99,9% entregabilidade, SDK maduro
  - Contras: pertence ao Twilio, requer cadastro
  - Custo: free tier suficiente para 1k usuários; pago ($19.95/mês) a partir de ~40k emails/mês
- **Opção B — Resend:**
  - Prós: mais moderno, DX melhor, gratuito até 3.000 emails/mês
  - Contras: requer pequena mudança no `email_service.py` (trocar o endpoint HTTP)
  - Custo: gratuito até 3k/mês, depois $20/mês para 50k
- **Opção C — Amazon SES:**
  - Prós: mais barato em escala ($0.10 por 1k emails), já integrado se usar AWS
  - Contras: mais complexo de configurar (verificação de domínio obrigatória, sandbox inicial)
  - Custo: praticamente zero para 1k usuários

**Recomendação:**
SendGrid free tier para começar (zero custo, zero risco, já funcionando no código). Migrar para SES quando chegar em 40k emails/mês. Resend também é boa opção se preferir DX moderno — apenas trocar 3 linhas no email_service.py.

**Para ativar (ação do dono):**
1. Criar conta em sendgrid.com
2. Verificar domínio clubeusa.com como remetente
3. Gerar API Key com permissão `Mail Send`
4. Adicionar no ambiente de produção:
   - `SENDGRID_API_KEY=SG.xxx...`
   - `EMAIL_FROM=no-reply@clubeusa.com`
   - `EMAIL_FROM_NAME=Clube USA`

**Status:** PENDENTE

---

### [2026-09-07] Email deve ser obrigatório ou opcional no cadastro?

**Contexto:**
O cadastro atual usa telefone como identificador primário (WhatsApp OTP). Email é opcional mas recomendado. A Fase 0.1 implementou confirmação de email — quem fornece email recebe link de confirmação. "Cadastro válido" (Fase 0.4) = phone confirmado + email confirmado + ≥1 ação real.

**Pergunta:**
Devemos tornar o email OBRIGATÓRIO no cadastro para forçar todos a confirmá-lo?

**Opções:**
- **Opção A — Manter opcional (status quo):**
  - Prós: menor fricção no cadastro → maior conversão; imigrantes às vezes não têm email fácil
  - Contras: muitos "cadastros inválidos" sem email; dificulta métricas 0.4
  - Recomendação para fase inicial: manter opcional, forte nudge para confirmar
- **Opção B — Tornar obrigatório:**
  - Prós: base limpa, todos confirmáveis, melhor para email marketing
  - Contras: reduz conversão no cadastro (estimativa: -20-30% baseado em benchmarks de mercado)
  - Implementar somente quando houver volume para absorver a perda de conversão

**Recomendação:**
Manter opcional agora. Adicionar tela pós-cadastro com forte incentivo ("confirme seu email e ganhe 50 pontos bônus"). Reavaliar quando atingir 500 cadastros.

**Status:** PENDENTE

---

*Atualizado em: 2026-09-07*
