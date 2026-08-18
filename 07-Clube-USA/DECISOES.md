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

### [2026-08-18] Provedor de email para confirmação de email (Fase 0.1)

**Contexto:** A feature de confirmação de email foi implementada com stub plugável (`EMAIL_PROVIDER` env var). Em dev, o link de confirmação é apenas logado no console. Em produção, o sistema precisa de um provedor de email real para entregar o link ao usuário. A lógica de envio está pronta para Resend.com e SendGrid — basta configurar as env vars.

**Pergunta:** Qual provedor de email usar para enviar os emails de confirmação em produção?

**Opções:**
- **Resend.com** *(recomendado)*: $0 até 100 emails/dia no free tier, API moderna e simples, excelente DX, boa reputação de entregabilidade.
  - Pró: free tier generoso para os primeiros 1k usuários, setup em < 30 minutos, suporte a domínio próprio
  - Contra: menos maduro que SendGrid, ecossistema menor
- **SendGrid**: free tier até 100 emails/dia, muito usado, bem documentado.
  - Pró: maduro, grande ecossistema, bom suporte
  - Contra: UI mais complexa, processo de verificação de domínio mais trabalhoso, não é open-source
- **Amazon SES**: $0.10 por 1.000 emails (mais barato em escala).
  - Pró: custo muito baixo a partir de 10k+ emails/mês
  - Contra: requer conta AWS ativa, sandbox mode inicial exige aprovação manual, mais configuração

**Recomendação:** Resend.com para começar (free tier suficiente para os primeiros 1k usuários, setup rápido). Migrar para SES quando chegar em 10k+ usuários ativos.

**Ação necessária pelo dono:**
1. Criar conta em resend.com
2. Verificar o domínio `clubeusa.com` (adicionar registros DNS conforme instruções do Resend)
3. Criar uma API key
4. Configurar env vars em produção:
   ```
   EMAIL_PROVIDER=resend
   RESEND_API_KEY=re_xxxxxxxxxxxxx
   ENVIRONMENT=production
   ```

**Status:** PENDENTE — aguardando decisão do dono

---

*Atualizado em: 2026-08-18*
