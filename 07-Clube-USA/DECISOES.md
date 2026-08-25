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

### [2026-08-25] BLOQUEIO CRÍTICO: 26 PRs abertas, zero merges — plataforma parada

**Contexto:**
O agente (sessions anteriores + esta) criou 26+ PRs cobrindo as Fases 0.1 a 2.1. Nenhuma foi mergeada. O código existe e está funcional, mas nunca chega à `main`. Cada nova sessão cria mais PRs sem saber que as anteriores existem, gerando duplicatas e divergência crescente. A plataforma está tecnicamente completa no GitHub mas não em produção.

**Avaliação técnica honesta (FRANQUEZA):**
- Criar mais PRs de feature agora é contra-produtivo: adiciona ruído e aumenta conflitos
- As PRs mais antigas (#3, #4, #5) têm alta chance de conflito com as mais novas
- As PRs de consolidação (#62) e as versões mais recentes (#54, #58) são provavelmente as mais completas
- O problema raiz NÃO é o código — é a ausência de revisão + merge

**Pergunta objetiva:**
Você pode reservar 30-60 minutos para revisar e mergar as PRs na ordem abaixo?
E qual provedor de email quer usar para a confirmação de email (Fase 0.1)?

**Ordem de merge recomendada (do mais seguro ao mais complexo):**

| Prioridade | PR | O que faz | Risco |
|---|---|---|---|
| 1 | **#56** | CI: testes automáticos nos PRs | Baixíssimo — só GitHub Actions |
| 2 | **#9** | fix(security): headers HTTP + validações | Baixo — additive |
| 3 | **#61** | fix(security): verificar token Z-API webhook | Baixo — isolado |
| 4 | **#62** | Consolida 0.2 + 0.3 + webhook — **"MERGE ESTE PRIMEIRO"** | Médio — revisar conflitos |
| 5 | **#54** OU **#46** | feat(0.1): confirmação de email | Médio — requer chave de email |
| 6 | **#58** | feat(0.4): cadastro válido + anti-fraude | Médio — depende de #54 |
| 7+ | #12, #14, #16, #19, #20 | Fase 1 (promoções, ZIP, influenciadores, empregos, moradia) | Dependem da Fase 0 mergeada |

**PRs que podem ser FECHADAS sem merge (obsoletas/duplicadas):**
- **#3** (0.2 referral) — substituída por #52 e #62
- **#4** (0.3 analytics) — substituída por #55 e #62
- **#5** (0.4 anti-fraude) — substituída por #58
- **#64, #66** (docs de status) — substituídas por este arquivo após merge

**Opções para você:**

- **Opção A — Merge em cascata esta semana:** Siga a tabela acima. O agente na próxima sessão verifica conflitos e ajuda a resolver, mas o merge final é seu.
- **Opção B — Consolidar tudo num squash:** Feche todas as PRs e deixe o agente criar UMA nova PR com tudo o que foi implementado, em base limpa. Mais trabalho agora, menos confusão depois.
- **Opção C — Manter o status quo:** Mais PRs serão criadas sem saber das anteriores. Não recomendado.

**Recomendação:** Opção A. Comece pelo #56 (CI) e #9 (segurança) — ambos são triviais. Se o #62 não tiver conflito, merge imediato. Isso desbloquearia 0.2 e 0.3 de uma vez.

**Para email (Fase 0.1 — PR #54):**
O código está pronto, só falta a chave. Opções com custo zero ou muito baixo:
- **Resend** (resend.com) — 100 emails/dia grátis, fácil integração, recomendado
- **SendGrid** — 100 emails/dia grátis no tier free
- **Brevo (ex-Sendinblue)** — 300 emails/dia grátis
Crie conta, gere a `RESEND_API_KEY` (ou equivalente) e adicione ao `.env` no Render/Supabase.

**Status:** PENDENTE — aguardando revisão e merge das PRs pelo dono

---

### [2026-08-25] Provedor de email para confirmação de conta (Fase 0.1)

**Contexto:**
O fluxo de confirmação de email (PR #54) está implementado mas precisa de um serviço de envio de email configurado. A escolha afeta custo, deliverability e integração.

**Pergunta:** Qual provedor usar para enviar emails de confirmação?

**Opções:**
- **Resend** — Prós: API simples, 100/dia grátis, excelente deliverability, SDK Python oficial. Contras: menos conhecido. **RECOMENDADO.**
- **SendGrid** — Prós: muito usado, tier free 100/dia. Contras: setup mais burocrático, frequentemente cai em spam em tier free.
- **Brevo** — Prós: 300/dia grátis, boa deliverability. Contras: UI mais complexa.
- **AWS SES** — Prós: custo muito baixo em escala ($0.10/1000 emails). Contras: precisa conta AWS + DNS setup + sair do sandbox.

**Recomendação:** Resend para os primeiros 1.000 usuários. Migrar para AWS SES quando volumes crescerem (> 10k/mês). Custo de migração é baixo — é só trocar a variável de ambiente.

**Ação necessária:**
1. Criar conta em resend.com
2. Adicionar domínio (clubeusa.com) e verificar DNS
3. Gerar API key
4. Adicionar `RESEND_API_KEY=re_xxx` no Render e no `.env.example`
5. Mergear PR #54

**Status:** PENDENTE — aguardando escolha do dono

---

### [2026-08-25] Agente deve pausar criação de features até Fase 0 estar em main

**Contexto:**
Com 26+ PRs pendentes cobrindo as Fases 0 a 2, criar mais código é desperdício. O agente continuará rodando 3x/dia mas sem saber quais PRs existem se não ler o DECISOES.md.

**Decisão interna do agente (documenta para consistência):**
A partir desta sessão, a regra é:
- Se Fase 0.1–0.4 NÃO estiver em `main`: fazer apenas polimento, testes, docs e verificação de conflitos nas PRs existentes
- Se detectar conflito em PRs #62, #54 ou #58: resolver o conflito e push na MESMA branch (não criar nova PR)
- Não criar novas PRs de feature até Fase 0 estar completa em main

**Status:** DECIDIDO PELO AGENTE — sem necessidade de aprovação do dono (é decisão técnica reversível)

---

*Atualizado em: 2026-08-25*
