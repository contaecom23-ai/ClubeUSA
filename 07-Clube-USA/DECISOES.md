# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## ⚠️ LEIA ISTO PRIMEIRO — BLOQUEIO CRÍTICO (2026-11-09)

### Resumo em 2 linhas
O agente rodou ~3x/dia por meses e criou **167 PRs abertos** sem que nenhum fosse mergeado.
O resultado: **zero código novo está na main**. O projeto não avançou.

### Por que isso aconteceu
1. O agente cria código em branches → abre PR → espera review
2. O owner não mergea → main não muda
3. Na próxima rodada, o agente vê main igual → recria o mesmo trabalho → abre mais um PR
4. Loop se repete indefinidamente

### O que existe hoje na `main`
- `07-Clube-USA/clubeusa/api/main.py` — API FastAPI base (~40KB)
- `07-Clube-USA/clubeusa/api/routers/` — forum.py, news.py, assistant.py
- `07-Clube-USA/clubeusa/platform.html` — frontend
- **NÃO existe na main**: confirmação de email (Fase 0.1), referral (Fase 0.2), analytics (Fase 0.3), nada das fases

### O que existe nas branches (trabalho feito, aguardando merge)
- **Email confirmation (Fase 0.1)** — pelo menos 8 variações: PRs #152, #153, #161, #165, #166, #167 e outros
  - **Recomendação**: mergear o **PR #167** (mais recente, mais completo)
- **Referral rastreável (Fase 0.2)** — PR #157
- **Security fixes** — PR #158 (3 correções auditadas: PII em logs, OTP timing, CSP)
- **Analytics growth (Fase 0.3)** — PR #109

---

## D-001 — AÇÃO DO DONO: DESBLOQUEAR O PROJETO

**Data:** 2026-11-09  
**Contexto:** 167 PRs abertos, main congelada desde pelo menos junho 2026. O agente continuará criando PRs duplicados enquanto nada for mergeado.  
**Pergunta:** Você quer desbloquear o projeto? Se sim, o que fazer?

### Plano de saída (15 minutos do seu tempo)

**Passo 1 — Fechar os PRs duplicados em massa (GitHub UI):**
Vá em https://github.com/contaecom23-ai/ClubeUSA/pulls  
Filtre por "feat/fase-0.1" ou similar. Feche todos EXCETO os que você vai mergear.

**Passo 2 — Mergear em ordem (mínimo 3 PRs para desbloquear):**
1. **PR #167** — `feat(fase-0.1): verificação de email` — base de tudo
2. **PR #157** — `feat(fase-0.2): referral redirect` 
3. **PR #158** — `fix(security): 3 correções auditadas`

**Passo 3 — Atualizar o ROADMAP.md:**
Após mergear, marque `[x]` nos itens correspondentes.

**Passo 4 — O agente retoma:**
Na próxima rodada, o agente verá main atualizada e avançará para Fase 0.3/0.4 sem repetir o que já existe.

### Opções
- **Opção A: Mergear os PRs acima** → projeto desbloqueia, agente avança → RECOMENDADO
- **Opção B: Recomeçar do zero** → fechar todos os 167 PRs e deixar o agente reescrever tudo numa branch limpa → mais lento, mas limpa a bagunça
- **Opção C: Parar o agente** → cancelar o schedule se o projeto foi abandonado

**Recomendação:** Opção A, mergear pelo menos PR #167 esta semana para desbloquear.

**Status:** PENDENTE — aguardando ação do dono

---

## D-002 — CONFIGURAÇÃO DE EMAIL (bloqueio técnico)

**Data:** 2026-11-09  
**Contexto:** Fase 0.1 (email confirmado) requer um servidor SMTP configurado. O PR #167 já tem o código pronto, mas precisa de credenciais SMTP para funcionar em produção.  
**Pergunta:** Qual provedor de email usar para envio transacional?

**Opções:**
- **Resend.com** (free: 3.000/mês, $20/mês depois) — mais simples, API moderna → RECOMENDADO
- **Mailgun** (free: 5.000/mês) — mais maduro, mais configuração
- **SendGrid** (free: 100/dia) — confiável, integração fácil
- **Gmail SMTP** — funciona para testes, não para produção (limite 500/dia, reputação ruim)

**Recomendação:** Resend.com — crie conta gratuita, gere API key, adicione `RESEND_API_KEY=re_xxxxx` no .env  
**Status:** PENDENTE — aguardando ação do dono

---

## D-003 — URL DO PRODUTO (decisão de produto)

**Data:** 2026-11-09  
**Contexto:** O sistema de referral usa URL no formato `clubeusa.com/i/{code}`. Domínio precisa estar apontado.  
**Pergunta:** Qual domínio está registrado e apontado para a API?

**Status:** PENDENTE — aguardando informação do dono

---

## Como usar este arquivo

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

*Atualizado em: 2026-11-09 (tarde) — agente automático*
