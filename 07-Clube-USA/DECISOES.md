# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## ⚠️ SITUAÇÃO REAL — 2026-09-08

**O projeto está parado por falta de revisão humana.**

Resumo técnico honesto do que existe hoje em `main`:

| Item | Status real em `main` |
|------|----------------------|
| Backend FastAPI (auth, OTP, deals, billing) | ✅ Completo |
| Cadastro com telefone + WhatsApp OTP | ✅ Funciona |
| Sistema de referral (código + pontos) | ✅ Existe em `main` |
| Stripe (VIP $4.99/mês) | ✅ Código pronto |
| Admin panel, alertas de preço, rastreador | ✅ Código pronto |
| App deployado em Render | ❌ **NÃO** — precisa de setup manual |
| Banco Supabase com dados reais | ❌ **NÃO** — precisa de chaves no `.env` |
| PRs abertos (acumulados) | ⚠️ **85 PRs abertos**, 0 mergeados |

---

## D-001 — BLOQUEADOR CRÍTICO: Deploy nunca foi feito

**Data:** 2026-09-08  
**Contexto:** O código está pronto em `main` mas o app não está deployado. O `SETUP_PENDENTE.md` lista os passos exatos. Sem deploy, nenhum usuário pode acessar a plataforma.

**Pergunta:** Você vai configurar o deploy agora?

**O que precisa fazer (leva ~30 minutos):**
1. Render.com → New → Blueprint → apontar para `07-Clube-USA/clubeusa/render.yaml`
2. Preencher variáveis de ambiente:
   - `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` (do projeto `susnhkgrejvyhdhoyeev`)
   - `ENCRYPTION_KEY` + `JWT_SECRET` (gerar com `python utils/security.py`)
   - `ADMIN_SECRET` (senha forte)
   - `APP_URL` (URL do Render)
   - `ZAPI_INSTANCE` + `ZAPI_TOKEN` + `ZAPI_CLIENT_TOKEN` (Z-API para WhatsApp OTP)
3. Rodar o schema SQL no Supabase (arquivo `07-Clube-USA/clubeusa/db/schema.sql`)

**Custo:** Render gratuito no início; Z-API ~$20/mês para WhatsApp.

**Status:** PENDENTE — depende do dono

---

## D-002 — 85 PRs abertos: o que fazer

**Data:** 2026-09-08  
**Contexto:** O agente automático criou 85 PRs ao longo de semanas. Nenhum foi revisado ou mergeado. Cada rodada cria mais PRs. O `main` está estagnado.

**Pergunta:** Qual a estratégia para limpar os PRs?

**Opção A — Fechar tudo e recomeçar limpo (recomendado)**
- Fechar todos os 85 PRs sem merge
- O `main` já tem o código base suficiente para lançar
- O agente foca em uma feature por vez a partir de agora
- Pros: limpo, sem conflitos, foco; Contras: descarta código dos PRs (mas a maioria é duplicate)

**Opção B — Revisar e manter os PRs importantes**
- Identificar 3-5 PRs com features reais e mergear
- Fechar o resto
- Pros: aproveita código; Contras: requer revisão manual de cada um

**Minha recomendação:** Opção A. O `main` já tem o essencial. Os PRs são mostly duplicatas e docs. Fechar tudo e fazer deploy do que está em `main` é o caminho mais rápido para ter usuários reais.

**Status:** PENDENTE — depende do dono

---

## D-003 — Autenticação: email ou só WhatsApp?

**Data:** 2026-09-08  
**Contexto:** O ROADMAP (Fase 0.1) diz "email confirmado". O sistema atual usa WhatsApp OTP (sem email). O schema tem campos de email mas sem `email_confirmed`. 

**Pergunta:** Para o público-alvo (imigrantes brasileiros nos EUA), qual fluxo faz mais sentido?

**Opção A — Manter WhatsApp OTP (atual)**
- Pros: natural para brasileiros, sem senha, sem spam
- Contras: requer Z-API pago, usuário precisa de WhatsApp

**Opção B — Adicionar email como alternativa**
- Pros: mais universal, sem custo de Z-API
- Contras: mais atrito, mais spam, implementação extra

**Minha recomendação:** Manter WhatsApp OTP. É diferencial competitivo para imigrantes brasileiros. Só adicionar email se houver reclamações reais de usuários.

**Status:** PENDENTE — depende do dono

---

## Como usar este arquivo

Quando Claude travar em algo que só você pode decidir, registra aqui.  
Formato: data, contexto, pergunta, opções com prós/contras, recomendação.  
Claude **não** age em itens desta lista sem sua aprovação explícita.

---

*Atualizado em: 2026-09-08*
