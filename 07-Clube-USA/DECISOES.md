# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 D-001 — PARALISIA DE MERGE (BLOQUEIO CRÍTICO) — 2026-11-08

**Status:** PENDENTE — ação do dono necessária

**Contexto:**
O projeto está em **paralisia total de merge** desde junho 2026. A branch `main` está congelada no commit `86d3122` e há **162 PRs abertos** — nenhum foi mergeado. Cada sessão autônoma do agente cria novos PRs porque não enxerga o trabalho anterior (que está em branches não mergeadas). O resultado é duplicação massiva: a funcionalidade de email confirmation (Fase 0.1) tem pelo menos 10 PRs diferentes para a mesma coisa (#106, #115, #147, #148, #150, #152, #153, #160, #161). Os PRs de DECISOES.md (#162, #159, #156, etc.) também nunca foram mergeados, por isso o agente continua criando novos. Nenhuma das Fases 0.1–0.4 está em produção.

**O que fazer (5 minutos):**

### Passo 1 — Mergear estes PRs (em ordem)

| Ordem | PR | O que entrega |
|-------|-----|---------------|
| 1º | **#161** | Fase 0.1 completa: email confirmation token + serviço SMTP + testes |
| 2º | **#157** | Fase 0.2: link `/i/{code}` rastreável + atribuição de cadastro |
| 3º | **#158** | Correções de segurança (PII em logs, OTP timing, CSP) |
| 4º | **#109** | Fase 0.3: GET /admin/analytics/growth — série temporal |
| 5º | **este PR** | CORS fix + este DECISOES.md atualizado |

### Passo 2 — Fechar os PRs duplicados (sem mergear)

Fechar: #106, #115, #147, #148, #150, #152, #153, #160, #159, #156, #155, #154, #151, #114, #111, #81

### Passo 3 — Comunicar ao agente

Depois de mergear, responda: "PRs mergeados, pode continuar." O agente seguirá para Fase 0.4 e 1.1.

**Recomendação:** Mergear o PR #161 agora mesmo. É seguro, bem testado, e desbloqueia tudo.

---

## D-002 — CONFIGURAÇÃO DE SERVIDOR SMTP PARA EMAIL — 2026-11-08

**Status:** PENDENTE

**Contexto:** A Fase 0.1 (email de confirmação) requer SMTP. O código está pronto (PR #161), mas sem credenciais o email não sai.

**Opções:**
- **A — Resend.com** (recomendado): gratuito até 100 emails/dia. Criar conta, pegar API key, adicionar `.env`: `SMTP_HOST=smtp.resend.com`, `SMTP_PORT=587`, `SMTP_USER=resend`, `SMTP_PASS=<api-key>`
- **B — Gmail SMTP**: gratuito mas credenciais no .env são risco menor
- **C — Sem email por agora**: verificação via WhatsApp/Telegram (Z-API já configurada)

**Recomendação:** Opção A (Resend.com) — 10 minutos de setup, gratuito para MVP de 1.000 usuários.

---

## D-003 — Z-API WEBHOOK SEM AUTENTICAÇÃO — 2026-11-08

**Status:** PENDENTE (já registrado em PR #110, mas não mergeado)

**Contexto:** O endpoint `POST /webhook/group` (Z-API) não verifica autenticidade do chamador. Qualquer pessoa pode chamar e manipular contagens de grupos. PR #110 tem a correção mas não foi mergeado.

**Recomendação:** Mergear PR #110 ou incluir o fix no próximo ciclo de segurança.

---

*Atualizado em: 2026-11-08*
