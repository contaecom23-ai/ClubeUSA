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

### [2026-08-19] URGENTE: 18 PRs abertos sem merge — plataforma bloqueada

**Contexto:**
Durante as últimas semanas, o Claude abriu 18 PRs e **nenhum foi merged**. Isso está causando problemas sérios:

1. PRs que tardam a mergiar acumulam conflitos entre si
2. A `main` não reflete o trabalho feito — Claude não sabe o que está "deployado"
3. PRs #12–#20 (Fase 1.1–1.5) estão em cadeia de branches encadeados entre si, **não baseados em `main`** — precisarão de rebase completo quando a Fase 0 for merged
4. Claude não pode construir sobre código que não está na `main`

**Pergunta:**
Qual estratégia adotar para limpar esse backlog e desbloquear o desenvolvimento?

**Opções:**

**Opção A — Você faz merge dos PRs principais em ordem (RECOMENDADO):**
- Ordem sugerida: PR #46 → PR #52 → PR #54 → PR #55 → PR #57 → PR #58 → PR #56
- Se der conflito, comente no PR e o Claude resolve
- Prós: controle total, vê cada mudança individualmente, fundação sólida
- Contras: requer ~30–45 min do seu tempo

**Opção B — Claude consolida toda a Fase 0 em 1 PR único:**
- Claude fecha os PRs existentes de Fase 0, cria branch limpa `feat/fase-0-completa` com tudo junto
- Prós: 1 PR único fácil de revisar, histórico limpo
- Contras: diff maior; requer sua aprovação explícita aqui antes de Claude agir

**Opção C — Manter como está e Claude constrói sobre branches encadeadas:**
- Claude continua abrindo PRs em cima de branches que não estão em `main`
- Prós: nenhum esforço seu agora
- Contras: aumenta a dívida técnica; eventual merge será caótico; não recomendado

**Recomendação:** Opção A. Comece pelo PR #46 (marcado `[MERGEAR ESTE]`) — ele é a base. Leva ~10 min revisar. Se aparecer conflito, escreva "conflito no PR #XX" nos comentários e o Claude resolve.

**Status:** PENDENTE — aguardando decisão do dono

---

### [2026-08-19] Modelo de autenticação: WhatsApp OTP vs Email obrigatório

**Contexto:**
O ROADMAP define "email confirmado" como requisito da Fase 0.1. A API atual em `main` usa **WhatsApp OTP** como autenticação primária — email é campo opcional no cadastro. Os PRs #46 e #54 tornam email obrigatório com confirmação por link.

**Pergunta:**
Qual é o modelo correto de auth para o público-alvo (imigrantes brasileiros nos EUA)?

**Opções:**

**Opção A — Manter WhatsApp-first (atual em `main`):**
- Usuário autentica pelo número de telefone via OTP WhatsApp; email é opcional
- Prós: WhatsApp é onipresente entre brasileiros; zero friction; maior taxa de conversão
- Contras: email marketing limitado; plataformas de afiliados exigem email verificado
- Impacto: não mergear PRs que tornam email obrigatório

**Opção B — Email obrigatório (PRs #46/#54):**
- Usuário confirma email no cadastro; WhatsApp é secundário
- Prós: email marketing completo; padrão do mercado para parcerias
- Contras: friction maior; emails de imigrantes podem ser menos ativos
- Impacto: mergear PRs #46 e #54

**Opção C — Ambos aceitos (WhatsApp OU Email, usuário escolhe):**
- Prós: máxima conversão
- Contras: ~2× complexidade de implementação; mais bugs potenciais

**Recomendação:** Opção A. O público é 100% imigrante brasileiro — WhatsApp é o canal nativo. Email como campo opcional coletado no perfil é suficiente para marketing inicial. Não adicione friction no momento crítico de cadastro. Reavalie quando atingir 5.000 membros se email marketing se tornar prioritário.

**Status:** PENDENTE — aguardando decisão do dono

---

### [2026-08-19] Ambiente de deploy — a plataforma está rodando em algum lugar?

**Contexto:**
`SETUP_PENDENTE.md` existe no repositório e o código exige variáveis de ambiente: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SECRET_KEY`, `STRIPE_SECRET_KEY`, `ZAPI_INSTANCE`, `ZAPI_TOKEN`. Não há evidência de que o banco foi criado ou que o `schema.sql` foi rodado.

Sem deploy, todo o código escrito não é testável em produção. Sem Supabase configurado, o schema pode estar desatualizado com os múltiplos PRs abertos.

**Pergunta:**
A plataforma está deployada em algum ambiente (produção ou staging)?

**Opções:**

**Opção A — Já está deployada (ex: Render, Railway, VPS):**
- Comente qual URL e o Claude pode verificar o health check e estado dos endpoints
- Importante: compartilhe apenas nomes das vars (não valores) para o Claude verificar o que falta

**Opção B — Ainda não foi deployada:**
- Claude pode criar um guia completo de setup no **Render** (plano gratuito suficiente para 1.000 usuários)
- Custo: $0 até ~$7/mês dependendo do uso
- Tempo de setup com o guia: ~45 min

**Recomendação:** Responda aqui. Sem saber se há um ambiente rodando, o Claude não pode validar que o código funciona end-to-end. Um ambiente de staging (mesmo que gratuito) é crítico para verificar antes de promover para usuários reais.

**Status:** PENDENTE — aguardando resposta do dono

---

*Atualizado em: 2026-08-19*
