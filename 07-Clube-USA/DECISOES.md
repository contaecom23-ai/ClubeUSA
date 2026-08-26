# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age sem sua aprovação. Revise 1x/dia.

---

## ⚠️ SITUAÇÃO ATUAL — LEIA PRIMEIRO

**Data:** 2026-08-26

Há **31 PRs abertas sem merge** (PRs #4 a #71). Cada rodada do agente percebe que o trabalho já foi feito e cria mais documentação — o que cria mais PRs. Isso é um loop improdutivo. **O agente não consegue avançar enquanto nenhuma PR é mergeada.**

Todo o código das Fases 0.1 até 2.1 já foi escrito e está em PRs abertas. O bloqueio não é técnico — é de revisão humana.

---

## Decisões Pendentes

### [2026-08-26] #001 — URGENTE: Fechar/mergear PRs acumuladas

**Contexto:** 31 PRs abertas cobrindo todas as fases do roadmap (0.1 a 2.1). Nenhuma foi mergeada. O código existe, foi revisado pelo agente, mas fica invisível no main.

**Pergunta:** Qual estratégia de desbloqueio você quer?

**Opções:**
- **A) Mergear as 3 PRs mais importantes agora, fechar o resto:**
  - Mergear PR #61 (fix segurança — webhook sem verificação de token)
  - Mergear PR #70 (Fase 0.2 referral redirect + Fase 0.3 analytics)
  - Mergear PR #54 (Fase 0.1 confirmação de email)
  - Fechar todas as demais como duplicatas
  - **Prós:** Limpa a bagunça, código bom entra no main, agente recomeça com base limpa
  - **Contras:** Exige ~30 min de revisão sua
- **B) Fechar todas e deixar o agente refazer do zero sobre a main atual:**
  - O agente pode reescrever cada feature limpa, sem conflitos acumulados
  - **Prós:** Base limpa, sem dívida técnica de PRs antigas
  - **Contras:** Retrabalho — o código já existe nas PRs
- **C) Commit direto na main por agora (sem PRs):**
  - Abandona o modelo de revisão por PR temporariamente
  - **Prós:** Agente avança sem bloqueio
  - **Contras:** Perde controle de qualidade; não recomendado com código que vai a produção

**Recomendação do Claude:** Opção A. A PR #61 é crítica (segurança real). A PR #70 está atualizada e sem conflitos conhecidos. Investir 20 minutos agora desbloquearia semanas de trabalho.

**Status:** PENDENTE

---

### [2026-08-26] #002 — Fase 0.1: "Email confirmado" ou "WhatsApp OTP" é suficiente?

**Contexto:** O ROADMAP exige "email confirmado" na Fase 0.1. O sistema atual autentica via OTP no WhatsApp (Z-API). Email é coletado opcionalmente mas nunca verificado. A PR #54 adiciona confirmação de email via SMTP.

**Pergunta:** Qual é o critério de "usuário verificado" para o Clube USA?

**Opções:**
- **A) WhatsApp OTP é suficiente (manter como está):**
  - Imediato. Sem custo de infra adicional.
  - Contras: depende Z-API estar online; sem fallback se WhatsApp falhar.
- **B) Email confirmado como requisito (mergear PR #54):**
  - Mais robusto. Funciona sem WhatsApp.
  - Custo: precisará configurar SMTP ou Resend/SendGrid (plano free disponível).
- **C) WhatsApp OTP agora + email como adicional futuro:**
  - Marcar 0.1 como ✅ com WhatsApp OTP. Adicionar email quando houver demanda.

**Recomendação do Claude:** Opção C. Brasileiros nos EUA são 100% WhatsApp. Marcar 0.1 como concluída com OTP do WhatsApp e avançar. Email pode ser adicionado na Fase 3 (confiança).

**Status:** PENDENTE

---

### [2026-08-26] #003 — Segurança: webhook Z-API aceita eventos sem verificar origem

**Contexto:** O endpoint `POST /webhook/group` recebe eventos de entrada/saída de membros nos grupos WhatsApp, mas **não verifica o `Client-Token` da Z-API**. Qualquer um que descobrir a URL pode enviar eventos falsos e manipular a contagem de membros.

**Pergunta:** Autoriza mergear PR #61 (adiciona verificação do Client-Token)?

**Opções:**
- **A) Mergear PR #61:** Fix cirúrgico, sem quebra de funcionalidade se `ZAPI_CLIENT_TOKEN` está no env.
- **B) Ignorar por agora:** Risco baixo enquanto a URL não é pública, mas cresce com o produto.

**Recomendação do Claude:** Mergear imediatamente. É o fix de menor risco e maior impacto no conjunto de PRs abertas.

**Status:** PENDENTE

---

### [2026-08-26] #004 — Infraestrutura: onde está rodando a API hoje?

**Contexto:** O agente não consegue confirmar se a API FastAPI está deployada em algum lugar (Render, Railway, VPS, etc.). Sem isso, não é possível testar endpoints em produção nem avançar para features que dependem de dados reais.

**Pergunta:** Onde a API está deployada? Há uma URL de produção ativa?

**Opções:**
- **A) Está no Render:** Confirmar a URL e as env vars configuradas.
- **B) Está localmente (não deployada):** O agente pode adicionar instruções de deploy ao DEPLOYMENT.md.
- **C) Não está deployada ainda:** Decisão de produto — quando deploiar?

**Recomendação do Claude:** Informar onde está rodando para que o agente possa ajustar as configs e evitar trabalho desconectado da realidade de infra.

**Status:** PENDENTE

---

## Decisões Aprovadas

*(nenhuma ainda)*

---

*Atualizado em: 2026-08-26 pelo agente autônomo (3ª rodada do dia)*
*Para agir: acesse as PRs listadas diretamente no GitHub ou responda aqui.*
