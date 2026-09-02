# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.
> Formato: data, contexto, pergunta objetiva, opções com prós/contras, recomendação.

---

## ⚠️ SITUAÇÃO CRÍTICA — 2026-09-02

**O projeto tem código funcionando mas zero usuários porque o app nunca foi deployado.**

Passos exatos de deploy estão em `07-Clube-USA/SETUP_PENDENTE.md`. Leva < 30 minutos.
**Isto é a prioridade absoluta acima de qualquer nova feature.**

---

## Decisões Pendentes

---

### D-001 — [2026-09-01] Deploy do app no Render (CRÍTICA — BLOQUEIO TOTAL)

**Contexto:** O banco Supabase está criado (21 tabelas, projeto `susnhkgrejvyhdhoyeev`). O código está pronto. Nenhum usuário consegue usar o app porque o Render nunca foi configurado.

**Pergunta:** Quando o dono vai seguir o `SETUP_PENDENTE.md` e colocar o app online?

**O que fazer:**
1. Abrir `07-Clube-USA/SETUP_PENDENTE.md`
2. Copiar chaves Supabase → `.env`
3. Gerar `ENCRYPTION_KEY` + `JWT_SECRET` (`python utils/security.py`)
4. Render → New → Blueprint → apontar para `07-Clube-USA/clubeusa/render.yaml`
5. Preencher variáveis de ambiente
6. Testar `curl https://<url>.onrender.com/health`

**Tempo estimado:** 20–30 minutos.

**Status:** PENDENTE — aguardando ação do dono

---

### D-002 — [2026-09-02] Plano de merge dos 30 PRs abertos (ALTA)

**Contexto:** Há 30 PRs abertos sem merge desde meados de agosto. O código base em `main` está desatualizado em relação a várias features já desenvolvidas. O Claude continua abrindo PRs mas nenhum é mergeado, criando um acúmulo inútil.

**Pergunta:** Qual o plano para limpar o backlog?

**Opções:**

- **Opção A (recomendada): Merge seletivo** — mergear apenas os PRs essenciais em ordem, fechar o resto:
  1. **PR #46** — `feat/fase-0.1-cadastro-auth` (Fase 0.1 base, marcar como ready-to-merge)
  2. **PR #62** — `feat/consolida-0.2-0.3-seguranca` (consolida referral + analytics + webhook security)
  3. **PR #78** — `fix/relogin-vip-plan-token` (bug fix crítico: VIP plan perdido no re-login)
  4. Fechar todos os outros 27 PRs com comentário explicando o motivo.
  - **Prós:** Código de main fica atualizado, backlog zero, Claude começa a trabalhar em cima de código atual.
  - **Contras:** Requer revisar 3 PRs manualmente.

- **Opção B: Fechar tudo e começar do zero** — fechar todos os 30 PRs, trabalhar a partir do main atual.
  - **Prós:** Backlog zero imediato.
  - **Contras:** Perde bugfix (#78) e consolidação (#62).

- **Opção C: Continuar como está** — não fazer nada.
  - **Prós:** Nenhum.
  - **Contras:** Claude continuará abrindo PRs que se acumulam. O main fica cada vez mais desatualizado.

**Recomendação:** Opção A. Leva ~1 hora de revisão. O PR #78 é especialmente importante — é um bug real que perde plano VIP de membros pagantes.

**Status:** PENDENTE — aguardando ação do dono

---

### D-003 — [2026-09-02] Estratégia de autenticação: phone OTP vs email (MÉDIA)

**Contexto:** O ROADMAP original diz "email confirmado" (Fase 0.1). O código implementado usa **phone number + OTP via Telegram/WhatsApp** como auth primário. São estratégias diferentes.

- Phone OTP: mais simples para imigrantes (todos têm WhatsApp), sem caixa de entrada de email pra verificar, mais rápido para conversão.
- Email: mais universal, funciona sem WhatsApp, padrão da indústria, necessário para newsletters e comunicação futura.

**Pergunta:** Qual canal de auth quer usar? Phone OTP é o primário para sempre, ou email será adicionado?

**Opções:**
- **A (recomendada):** Phone OTP como primário, email como campo opcional para newsletter/recuperação. Já está implementado.
- **B:** Adicionar email como obrigatório + confirmação por email. PRs #54/#75 já fizeram isto, aguardam merge.
- **C:** Duplo canal (phone + email, ambos válidos). Mais complexo, não recomendado para essa fase.

**Recomendação:** Opção A. Phone OTP é diferencial para o público-alvo (imigrante brasileiro), já está funcionando. Email pode ser adicionado como opcional depois.

**Status:** PENDENTE — aguardando decisão do dono

---

### D-004 — [2026-09-02] Programa de influenciadores: definir valores de pagamento (MÉDIA, pós-deploy)

**Contexto:** Fase 1.3 define "pago por resultado" com selos Parceiro/Embaixador/Hall da Fama. O leaderboard já está implementado. O que falta é: (a) valor por cadastro válido, (b) teto de orçamento mensal, (c) método de pagamento (Zelle? Venmo? PayPal?).

**Pergunta:** Quais os valores e método de pagamento para influenciadores?

**Opções exemplo:**
- $2–5 por cadastro válido (email confirmado + ≥1 ação)
- Teto: $500/mês por influenciador
- Pagamento via Zelle/Venmo mensalmente

**Recomendação:** Definir valores apenas DEPOIS do deploy e primeiros 100 usuários reais. Não gastar antes de validar conversão.

**Status:** PENDENTE — não urgente, só relevante pós-deploy

---

## Decisões Resolvidas

*(nenhuma ainda)*

---

*Atualizado em: 2026-09-02*
