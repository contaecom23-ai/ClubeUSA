# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-09-01] D-001 🚨 BLOQUEIO CRÍTICO: App não está deployado — nada funciona

**Contexto:**
O código no `main` está **completo e funcional**, mas o app nunca foi deployado. Não há URL pública, nenhum usuário consegue acessar, e nenhum dos 30 PRs em aberto faz sentido enquanto o serviço não estiver rodando.

**O que já existe e funciona no main (sem precisar mergear nada):**
- ✅ Auth completo: cadastro por telefone + OTP WhatsApp + JWT + perfil de membro
- ✅ Sistema de referral: `referral_code` único gerado no cadastro, contagem de indicações
- ✅ Billing Stripe: plano VIP $4.99/mês, webhook com verificação HMAC
- ✅ Rastreador de preços Amazon (Fase 1.6): histórico, cupons, alertas
- ✅ Forum + Notícias + Assistente IA
- ✅ Painel Admin: métricas, listagem de membros, aprovação de deals
- ✅ Supabase: banco criado (`susnhkgrejvyhdhoyeev`), 21 tabelas, migrations rodaram
- ✅ Render config (`render.yaml`): tudo pronto para deploy com 1 clique

**Ação necessária (VOCÊ, não o Claude — envolve credenciais):**

Siga `07-Clube-USA/SETUP_PENDENTE.md` (já existe no repo):
1. Copiar chaves Supabase para `.env`
2. Gerar `ENCRYPTION_KEY` + `JWT_SECRET`
3. Render → New → Blueprint → apontar para `render.yaml`
4. Preencher as variáveis de ambiente no Render
5. Acessar a URL gerada e testar cadastro/login

**Depois do deploy (opcional, mas recomendado):**
- Mergear PR #46 (email confirmation — se quiser adicionar email além do WhatsApp OTP)
- Fechar os outros 28 PRs — estão desatualizados e em conflito entre si

**Pergunta direta:** Você vai seguir o SETUP_PENDENTE.md esta semana?

**Recomendação:** Sim. Leva < 30 minutos. O app está pronto para rodar. Enquanto não estiver deployado, qualquer PR novo que o Claude criar é trabalho desperdiçado.

**Status:** PENDENTE

---

### [2026-09-01] D-002: 30 PRs abertos sem merge desde 14/08 — o que fazer?

**Contexto:**
Desde 14 de agosto de 2026, o agente abriu 30+ PRs e nenhum foi mergeado. Parte deles adiciona features legítimas sobre o main. Mas como estão todos abertos ao mesmo tempo, têm conflitos entre si e não há ordem clara de merge.

**Situação real dos PRs mais importantes:**
- PR #46 (não-draft): Fase 0.1 — email confirmation. Limpo, pode mergear direto.
- PR #62 (não-draft): Consolida 0.2 + 0.3 + segurança webhook. Já marcado "PRONTO PARA MERGE".
- PR #75 (draft): Outra implementação de email confirmation (duplica #46).
- PRs #16, #19, #20: Fases 1.3, 1.4, 1.5 — features de negócio (influenciadores, empregos, moradia).
- ~25 outros: docs, fixes pontuais, duplicatas.

**Opções:**
- **A (recomendada):** Deploy do main primeiro. Depois mergear #46, depois #62. Fechar os outros 27.
- **B:** Fechar TODOS os 30 PRs. Claude começa do zero a partir do main deployado.
- **C:** Não fazer nada agora (o ciclo de PRs sem merge continua, sem progresso real).

**Pergunta:** Qual das opções você escolhe?

**Recomendação:** Opção A. O código em #46 e #62 é bom e não vai no lixo. Mas SOMENTE faz sentido depois do deploy.

**Status:** PENDENTE

---

### [2026-09-01] D-003: Estratégia de autenticação — WhatsApp OTP vs Email

**Contexto:**
O main usa WhatsApp OTP (via Z-API) para login. Não tem email. O ROADMAP diz "email confirmado". São abordagens diferentes com trade-offs reais.

**WhatsApp OTP (atual):**
- ✅ Funciona sem senha, excelente UX para imigrantes brasileiros
- ✅ Já implementado no main
- ❌ Depende de Z-API ativo (`ZAPI_INSTANCE`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN` nas env vars)
- ❌ Se Z-API cair, login para de funcionar

**Email confirmation (nos PRs #46, #75):**
- ✅ Mais universal, não depende de WhatsApp
- ✅ Gratuito via SendGrid/SES
- ❌ UX pior para quem está acostumado com WhatsApp
- ❌ Requer configurar serviço de email

**Pergunta:** Qual estratégia usar para o lançamento?

**Recomendação:** Manter WhatsApp OTP para lançar rápido (já funciona). Adicionar email como backup em V2. Precisa configurar as credenciais Z-API no Render para funcionar.

**Status:** PENDENTE

---

*Atualizado em: 2026-09-01*
