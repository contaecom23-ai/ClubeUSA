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

## ⚠️ BLOQUEIO CRÍTICO — AÇÃO NECESSÁRIA HOJE

---

### [2026-10-31] MERGE PARALYSIS: 145 branches sem merge — repositório bloqueado

**Contexto:**
As sessões Claude rodam 3x/dia desde junho/2026 e criam branches com código novo, mas NENHUM PR foi mergeado para `main`. Resultado: há **145 branches remotas** com código funcional que nunca chegou a produção. A base de código em `main` está no estado de junho/2026.

Exemplos de trabalho pronto nas branches (não exaustivo):
- `feat/fase-0.1-email-confirmation` / `feat/fase-0.1-email-confirmacao` e ~20 variações — confirmação de email implementada várias vezes
- `feat/fase-0.2-referral-link-rastreavel` — URL /i/[codigo] implementada
- `feat/fase-0.3-analytics-basico` — endpoints de analytics
- `feat/fase-0.4-valid-cadastro` — definição de cadastro válido
- `feat/fase-1.1-promocoes-comunidade` — promoções
- `feat/fase-1.2-zip-search` — busca por ZIP
- `feat/fase-1.3-influencer-tiers` — selos influenciadores
- `feat/fase-1.4-empregos` — seção de empregos
- `feat/fase-1.5-moradia` — seção de moradia
- `feat/fase-2.1-business-subscriptions` — assinatura empresas
- `fix/security-3-issues-2026-09-25` — correções de segurança
- `fix/referral-capture-and-redirect` — captura de referral no frontend
- Dezenas de branches `docs/decisoes-*` com análises e planos nunca aplicados

**O problema central:** Sem `main` atualizado, cada nova sessão lê o código original de junho e reimplementa o que já foi feito, multiplicando o caos. As branches conflitam entre si. O código de produção está desatualizado.

**Pergunta:** Como quer desbloqueio?

**Opções:**

**A — Revisão manual seletiva (recomendada para código de prod)**
- Você abre os PRs mais relevantes (lista abaixo), revisa o diff, e mergeia
- Claude pode preparar um guia de quais mergear primeiro e em que ordem
- Prós: controle total, código revisado antes de ir pra prod
- Contras: leva algumas horas do seu tempo

**B — Claude faz triage e consolida em uma branch limpa para você revisar uma vez**
- Claude analisa todas as branches, identifica o código mais maduro de cada feature, monta uma branch consolidada com o conjunto
- Você revisa uma vez só e mergeia
- Prós: economiza muito tempo seu, um PR em vez de 145
- Contras: Claude pode escolher a versão errada de uma implementação; você perde o histórico granular
- Para autorizar: responda "consolide tudo" ou equivalente

**C — Parar o loop de 3x/dia até o desbloqueio**
- Suspender as sessões automáticas para evitar mais ruído
- Reativar depois que `main` estiver atualizado
- Para autorizar: edite o workflow `.github/workflows/clubeusa-builder.yml` ou responda "pause o loop"

**Recomendação do Claude:**
Combine **B + A**: Claude consolida as branches em grupos temáticos por fase (0.x, 1.x etc), um PR por grupo, você revisa e mergeia grupo por grupo. Mais prático que revisar 145 branches mas mantém controle.

**Ordem de merge recomendada** (se optar por fazer manual):
1. `fix/security-*` — correções de segurança em produção (alta prioridade)
2. `feat/fase-0.1-email-confirmation` (ou `feat/0.1-email-confirmation`) — email confirmado
3. `feat/fase-0.2-referral-link-rastreavel` — URL /i/[codigo] de referral
4. `feat/fase-0.3-analytics-basico` — analytics básico
5. `feat/fase-0.4-valid-cadastro` — cadastro válido
6. Features de fase 1 em sequência

**Status:** PENDENTE — aguarda resposta do dono

---

### [2026-10-31] Provider de email para confirmação de email

**Contexto:**
A infraestrutura de confirmação de email está implementada em múltiplas branches (ver acima). O código detecta `EMAIL_PROVIDER` e escolhe o provider. Em dev/não-configurado, apenas loga o link. Precisa de uma decisão de produto/custo para ativar em produção.

**Pergunta:** Qual provider de email usar?

**Opções:**

- **A — Resend (resend.com)** ← Recomendado
  - Free tier: 3.000 emails/mês (suficiente para os primeiros 1.000 cadastros)
  - Setup: conta em resend.com, verificar domínio, gerar API key
  - Env vars no Render: `EMAIL_PROVIDER=resend`, `RESEND_API_KEY=re_xxx`, `EMAIL_FROM=noreply@clubeusa.com`

- **B — SMTP via Google Workspace**
  - Prós: zero custo extra se já tem Google Workspace
  - Env vars: `EMAIL_PROVIDER=smtp`, `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER=xxx`, `SMTP_PASS=app_password`

- **C — Adiar** (não recomendado)
  - Base de emails não verificada cria problema de spam e invalida métrica de "cadastro válido"

**Status:** PENDENTE — depende do desbloqueio acima

---

*Atualizado em: 2026-10-31*
