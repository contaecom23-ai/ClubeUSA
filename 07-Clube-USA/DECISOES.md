# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ D-001 — PARALISIA DE MERGE (BLOQUEIO CRÍTICO) — 2026-11-07

**Status:** PENDENTE — ação do dono necessária

**Contexto:**
O projeto está em **paralisia total de merge** desde junho 2026. A branch `main` está congelada no commit `86d3122` e há **161 PRs abertos** nenhum foi mergeado. Cada sessão autônoma do agente cria novos PRs porque não consegue ver o trabalho anterior (que está em branches não mergeadas). O resultado é duplicação massiva: a funcionalidade de email confirmation (Fase 0.1) tem pelo menos 10 PRs diferentes para a mesma coisa (#106, #115, #147, #148, #150, #152, #153, #160, #161). Os PRs com atualizações de DECISOES.md (#159, #156, #155, #154, #111, #81) também nunca foram mergeados, por isso o agente continua criando novos.

**Impacto real:**
- Nenhuma das Fases 0.1–0.4 está em produção (zero usuários conseguem se cadastrar com email confirmado)
- O agente trabalha em loop: cria PR → não é mergeado → próxima sessão recomeça do zero
- A plataforma não avança mesmo com centenas de horas de trabalho feito

**Pergunta:**
Você pode mergear os PRs listados abaixo e fechar os duplicados?

**Plano de ação — O QUE FAZER:**

### Passo 1 — Mergear estes 4 PRs (em ordem)

| Ordem | PR | Branch | O que entrega |
|-------|-----|--------|---------------|
| 1º | **#161** | `feat/fase-0-1-email-confirmation` | Fase 0.1 completa: email confirmation token + serviço SMTP + testes |
| 2º | **#157** | `feat/fase-0.2-referral-redirect` | Fase 0.2: link `/i/{code}` rastreável + atribuição de cadastro |
| 3º | **#158** | `fix/security-audit-2026-11-05` | Correções de segurança: PII em logs, OTP timing, CSP |
| 4º | **#109** | `claude/fase-0.3-analytics-growth` | Fase 0.3: GET /admin/analytics/growth — série temporal |

> Para mergear: acesse cada PR no GitHub e clique "Merge pull request". Se houver conflito, resolva via GitHub ou avise o agente.

### Passo 2 — Fechar os PRs duplicados (sem mergear)

Fechar todos os outros PRs de email confirmation que ficaram para trás. O PR #161 é o mais recente e completo — os demais são versões antigas:

Fechar (Close without merge): #106, #115, #147, #148, #150, #152, #153, #160

Fechar também os PRs de DECISOES antigos (substituídos por este): #159, #156, #155, #154, #151, #114, #111, #81

### Passo 3 — Comunicar ao agente

Depois de mergear, responda aqui ou na próxima sessão: "PRs mergeados, pode continuar." O agente seguirá para Fase 0.4 (cadastro válido + anti-fraude — PR #104) e depois Fase 1.1 (promoções — PR #113).

**Por que não merg ar antes?**
Hipóteses (o agente não sabe a resposta — só você sabe):
1. Os PRs têm conflito com main → resolução necessária antes do merge
2. Você ainda não teve tempo/acesso ao GitHub
3. Aguardando algo (configuração de Supabase/Render/etc)
4. Os PRs têm algum problema de qualidade que não foi comunicado

**Recomendação do Claude:** Mergear o PR #161 agora mesmo. É seguro (não altera banco existente, só adiciona), bem testado, e desbloqueia tudo. Tempo estimado: 5 minutos.

---

## D-002 — CONFIGURAÇÃO DE SERVIDOR SMTP PARA EMAIL — 2026-11-07

**Status:** PENDENTE

**Contexto:**
A Fase 0.1 (email de confirmação) requer um servidor SMTP para enviar emails. O código está pronto (PR #161), mas sem credenciais SMTP o email não sai.

**Opções:**
- **Opção A — Resend.com** (recomendado): gratuito até 100 emails/dia, fácil integração. Criar conta, pegar API key, adicionar ao .env: `SMTP_HOST=smtp.resend.com`, `SMTP_PORT=587`, `SMTP_USER=resend`, `SMTP_PASS=<api-key>`
- **Opção B — SendGrid**: gratuito até 100/dia, maior setup
- **Opção C — Gmail SMTP**: gratuito com limite baixo (500/dia com Google Workspace), credenciais expostas em .env são risco
- **Opção D — Sem email por agora**: substituir confirmação por verificação via WhatsApp/Telegram (Z-API já configurada) — mais simples para MVP com brasileiros

**Pergunta:** Qual serviço de email você quer usar? Ou prefere começar sem email e usar WhatsApp para confirmar?

**Recomendação:** Opção A (Resend.com) — 10 minutos de setup, gratuito para MVP de 1.000 usuários.

---

## D-003 — FECHAR PRs DUPLICADOS EM MASSA — 2026-11-07

**Status:** PENDENTE

**Contexto:** Há ~150 PRs duplicados ou obsoletos que poluem o repositório. Fechar todos de uma vez pode ser feito via GitHub CLI:

```bash
# Listar todos os PRs abertos (exceto os 4 a mergear)
gh pr list --state open --limit 200

# Fechar um por um ou em lote (substitua os números)
gh pr close 106 115 147 148 150 152 153 160 159 156 155 154 151 114 111 81
```

**Pergunta:** Posso fechar em massa os PRs duplicados na próxima sessão (usando `gh pr close`)?

**Recomendação:** Sim — deixar 161 PRs abertos é ruído que atrapalha o trabalho. Manter apenas os 4 PRs a mergear + este docs PR.

---

*Atualizado em: 2026-11-07*
