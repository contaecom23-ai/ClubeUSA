# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## D-001 — PARALISIA DE MERGE (CRÍTICO — BLOQUEANDO TUDO)

**Data:** 2026-11-03  
**Status:** PENDENTE — ação humana necessária  

**Contexto:**  
O builder autônomo criou 154 PRs desde julho de 2026. Nenhum foi mergeado na `main`. Como resultado:
- O código na `main` está desatualizado (não tem email confirmado, referral redirect, analytics, etc.)
- O builder continua criando PRs duplicados a cada rodada, pois vê as tarefas como "pendentes"
- O projeto está tecnicamente parado há ~4 meses

**Pergunta:**  
Você quer desbloquear o projeto mergeando os PRs essenciais?

**Opções:**

- **Opção A — Mergear os 9 PRs essenciais (RECOMENDADO)**  
  Pros: desbloqueia o projeto, o builder para de criar duplicatas, você tem uma base funcional  
  Contras: ~15 min de trabalho manual no GitHub  
  Como: veja `07-Clube-USA/MERGE_GUIDE.md` com instruções passo a passo

- **Opção B — Abandonar o workflow de PRs e commitar direto na main**  
  Pros: mais simples, sem fila de review  
  Contras: perde o histórico de revisão, vai contra as regras de segurança do projeto  
  Como: alterar a instrução "Tudo via PR, nunca na main" no prompt do builder

- **Opção C — Pausar o builder**  
  Pros: para de acumular PRs enquanto você decide  
  Contras: sem progresso no projeto  
  Como: remover o scheduled task no Claude Code

**Recomendação:** Opção A. Leva 15 minutos e desbloqueia meses de trabalho acumulado.

Veja o guia detalhado: **`07-Clube-USA/MERGE_GUIDE.md`**

---

## D-002 — CONFIGURAÇÃO DO AMBIENTE DE PRODUÇÃO

**Data:** 2026-11-03  
**Status:** PENDENTE  

**Contexto:**  
Para o app funcionar em produção (Render), são necessárias as seguintes credenciais que o builder não tem acesso:

**Pergunta:**  
As seguintes variáveis de ambiente estão configuradas no Render/servidor?

| Variável | Descrição | Status |
|----------|-----------|--------|
| `SUPABASE_URL` | URL do projeto Supabase | ? |
| `SUPABASE_SERVICE_KEY` | Chave de service do Supabase | ? |
| `SECRET_KEY` | JWT secret (mínimo 32 chars aleatórios) | ? |
| `STRIPE_SECRET_KEY` | Chave secreta do Stripe | ? |
| `STRIPE_WEBHOOK_SECRET` | Webhook secret do Stripe | ? |
| `STRIPE_VIP_PRICE_ID` | Price ID do plano VIP no Stripe | ? |
| `ZAPI_INSTANCE` | ID da instância Z-API (WhatsApp) | ? |
| `ZAPI_TOKEN` | Token Z-API | ? |
| `ZAPI_CLIENT_TOKEN` | Client token Z-API | ? |
| `ENCRYPTION_KEY` | Chave de encriptação de PII (32 bytes base64) | ? |

**Opções:**
- **A** — Confirmar que estão configuradas → builder assume que está tudo ok e foca em features
- **B** — Não estão configuradas → registrar aqui quais faltam, builder cria guia de setup
- **C** — Usar ambiente de desenvolvimento apenas → builder cria `.env.local` de exemplo funcional

**Recomendação:** Responda qual é o status atual para que o builder possa avançar.

---

*Atualizado em: 2026-11-03*
