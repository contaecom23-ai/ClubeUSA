# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## Decisões Pendentes

---

### [2026-08-20] CRITICO: Dois sistemas de backend paralelos — qual é a base real?

**Contexto:**
Em 2026-08-20 o Claude leu o código completo de `main` e descobriu que existem **dois sistemas de backend distintos e incompatíveis** no repositório:

**Sistema A — `07-Clube-USA/clubeusa/api/` (existe em `main`, funcionando):**
- Auth por **telefone + WhatsApp OTP** (sem email)
- Registro: `POST /auth/register` (phone, name, email opcional, referral_code)
- Perfil: `GET/PATCH /member/profile`
- Referral completo: `GET /member/referral` (código único, stats, histórico)
- Deals: `GET /member/deals`
- Stripe VIP: `POST /billing/subscribe`
- Admin: `GET /admin/*`
- Rastreador de preço: `POST /products/track`
- Segurança: rate-limit por IP, OTP com TTL 10min no Supabase, HMAC Stripe

**Sistema B — `07-Clube-USA/backend/` (proposto em PR #46, não merged):**
- Auth por **email + senha + confirmação de email**
- Estrutura de diretório completamente diferente
- Schema SQL próprio (`schema/001_users_profile.sql`)
- PRs #52, #54, #55, #57, #58 foram construídos assumindo que este sistema existe

**Por que isso causa caos:**
Os 18 PRs abertos estão divididos entre os dois sistemas. PR #46 (email auth) nunca foi merged, mas PRs posteriores agiam como se fosse. Resultado: código em PRs que não se aplica a `main`.

**Pergunta:**
Qual sistema é a base real da plataforma?

**Opções:**

**Opção A — Manter e evoluir `clubeusa/` (WhatsApp OTP, já em `main`) — RECOMENDADO:**
- O Sistema A já implementa: 0.1 (auth), 0.2 (referral backend), 1.1 (deals), 1.6 (rastreador)
- PRs #3, #4, #5, #9, #12, #14, #16, #19, #20 (stacked) e #46, #54 (email auth) devem ser FECHADOS
- PRs #52 e #57 (referral frontend/redirect) podem ser adaptados para `clubeusa/`
- PRs #55 (analytics) e #58 (anti-fraude) precisam ser avaliados para compatibilidade
- Próxima tarefa real: merge PR #52 + #57 (completar 0.2), depois analytics (0.3)
- Pros: não joga fora 2.000+ linhas de código que já funcionam
- Cons: fechar muitos PRs (visual de "trabalho perdido")

**Opção B — Migrar para `backend/` (email auth, PR #46):**
- Mergear PR #46 como base; adaptar os demais PRs para esta estrutura
- Pros: estrutura mais moderna para email marketing
- Cons: descarta o Sistema A (2.000+ linhas); requer rebase de todos os PRs; mais 2-3 semanas de trabalho
- Cons: email não é o canal nativo do público (imigrantes brasileiros usam WhatsApp)

**Recomendação do Claude:**
Opção A. O Sistema A em `main` é mais maduro, mais alinhado com o público-alvo e já cobre as fases 0.1, 0.2 (parcial), 1.1 e 1.6. Fechar os PRs conflitantes não é trabalho perdido — é limpeza de débito técnico. Com a Opção A, a plataforma pode ir ao ar em dias, não semanas.

**Ação necessária:** Responda aqui com "Opção A" ou "Opção B".

**Status:** PENDENTE — aguardando decisão do dono

---

### [2026-08-19] URGENTE: 18 PRs abertos sem merge — plataforma bloqueada

**Contexto:**
Durante as últimas semanas, o Claude abriu 18 PRs e nenhum foi merged. Isso causa:
1. PRs que tardam acumulam conflitos entre si
2. A `main` não reflete o trabalho feito
3. PRs #12–#20 estão em cadeia de branches encadeados, não baseados em `main`
4. Claude não pode construir sobre código que não está na `main`

**Pergunta:** Qual estratégia adotar para limpar esse backlog?

**Opções:**

**Opção A — Você faz merge dos PRs em ordem (depende da decisão #1 acima):**
- Se escolher Sistema A (WhatsApp): fechar PRs #3, #4, #5, #9, #12–#20, #46, #54. Mergear #52, #55, #57, #58, #56.
- Se escolher Sistema B (email): mergear #46 primeiro, depois adaptar os demais.
- Pros: controle total
- Contras: requer ~1h do seu tempo

**Opção B — Claude consolida em 1 PR único por fase:**
- Claude fecha os PRs conflitantes, cria branches limpas com o código correto
- Pros: menos PRs para revisar
- Contras: diff maior; requer sua aprovação aqui antes de Claude agir

**Recomendação:** Opção A, mas SOMENTE após decidir a questão #1 (qual sistema). A ordem certa é: decidir Sistema A/B → Claude fecha os incompatíveis → você mergeia os corretos em 30 min.

**Status:** PENDENTE — aguardando decisão do dono (depende da decisão #1)

---

### [2026-08-19] Modelo de autenticação: WhatsApp OTP vs Email obrigatório

**Contexto:**
Ver decisão #1 acima para o contexto completo. Esta decisão está INCORPORADA na decisão #1.

**Resumo:** O Sistema A usa WhatsApp OTP. O Sistema B usa email. Decidir qual sistema (questão #1) resolve esta questão automaticamente.

**Status:** PENDENTE — resolvida quando decisão #1 for tomada

---

### [2026-08-19] Ambiente de deploy — a plataforma está rodando em algum lugar?

**Contexto:**
O código exige variáveis de ambiente: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SECRET_KEY`, `STRIPE_SECRET_KEY`, `ZAPI_INSTANCE`, `ZAPI_TOKEN`. Não há evidência de que o banco foi criado ou que o `schema.sql` foi rodado.

Sem deploy, todo o código escrito não é testável em produção.

**Pergunta:** A plataforma está deployada em algum ambiente?

**Opções:**

**Opção A — Já está deployada:**
- Informe qual URL e o Claude verifica o health check
- Compartilhe apenas os nomes das vars (não os valores)

**Opção B — Ainda não foi deployada:**
- Claude pode criar um guia completo de setup no Render (plano gratuito suficiente para 1.000 usuários)
- Custo: $0 até ~$7/mês
- Tempo de setup: ~45 min

**Recomendação:** Responda aqui. Sem um ambiente rodando, não é possível validar o código end-to-end.

**Status:** PENDENTE — aguardando resposta do dono

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa. Você revisa 1x/dia.

---

*Atualizado em: 2026-08-20*
