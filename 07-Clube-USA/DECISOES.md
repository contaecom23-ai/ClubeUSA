# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio,
aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo),
ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### 🚨 [2026-08-12] BLOQUEIO CRÍTICO — 49 PRs abertos, loop parado

**Contexto:**
O builder automatizado rodou ~49 vezes e criou **49 PRs abertos** para a mesma feature (Fase 0.1),
porque nenhum PR foi mergeado na `main`. A cada execução, o builder lê o ROADMAP.md da `main`,
vê o item 0.1 como `[ ]` (não concluído), e cria um novo PR. O projeto está preso em loop.

**A causa raiz:** Você nunca revisou/mergeou nenhum PR. Os PRs se acumularam na lista.

**O que PRECISA ser feito (SEM ISSO O LOOP NÃO PARA):**

**Ação obrigatória — escolha UMA das opções:**

**Opção A (recomendado) — Mergear o PR canônico:**
1. Abra o PR `#42` (branch `claude/fase-0.1-cadastro-perfil`) — tem o código mais completo
2. Revise: backend FastAPI + Supabase Auth + migration SQL + frontend HTML + testes
3. Configure as credenciais no `.env` (Supabase URL + service_role key + email SMTP)
4. Clique em "Merge pull request"
5. Feche os outros 48 PRs como "outdated/duplicate"

**Opção B — Fechar todos e recomeçar do zero:**
- Feche todos os 49 PRs com a mensagem "Fechando duplicatas — loop corrigido"
- O builder criará um PR limpo na próxima execução

**Opção C — Pausar o builder:**
- Desative o workflow em `.github/workflows/clubeusa-builder.yml` até você ter tempo de revisar

**Nota técnica:** O workflow YAML também está malformado (indentação incorreta), o que pode
impedir que o builder do GitHub Actions funcione corretamente. O PR #48 corrige isso.

**Recomendação do Claude:** Mergear o **PR #42** + fechar os outros 48 + configurar Supabase.
É o mais recente e mais completo. Depois mergear o PR #48 (fix do workflow YAML).

**Status:** BLOQUEANTE — O projeto não avança até esta decisão ser tomada.

---

### [2026-08-02] Configuração do Supabase (bloqueador de Fase 0.1)

**Contexto:** O backend FastAPI usa Supabase Auth para cadastro, login e confirmação de email. Sem
as credenciais de um projeto Supabase real, o código está pronto mas não pode ser testado nem implantado.

**O que precisa ser feito:**
1. Crie um projeto em [supabase.com](https://supabase.com) (plano gratuito suficiente para Fase 0 com 1k usuários)
2. Em **Settings → API**, copie:
   - `SUPABASE_URL` (ex: `https://xyzxyz.supabase.co`)
   - `service_role key` (NÃO a `anon key` — é a chave secreta de servidor)
   - `JWT Secret` (em Settings → API → JWT Settings)
3. Em **Authentication → URL Configuration**, configure:
   - **Site URL**: a URL onde o frontend estará hospedado (ex: `https://clubeusa.com`)
   - **Redirect URLs**: mesma URL + `/profile`
4. Em **Authentication → SMTP Settings**, configure provedor de email (ver decisão abaixo)
5. Execute a migration em **SQL Editor → New Query**: conteúdo de `07-Clube-USA/migrations/001_initial_schema.sql`
6. Crie o arquivo `.env` em `07-Clube-USA/backend/` com base no `.env.example`

**Status:** PENDENTE

---

### [2026-08-12] Provedor de email para confirmação de cadastro

**Contexto:**
A Fase 0.1 usa **Supabase Auth** para cadastro/login, e o email de confirmação é enviado pelo próprio
Supabase (configurado no dashboard em Authentication → SMTP Settings). O backend não envia email diretamente.

**Pergunta:**
Qual provedor de email configurar no Supabase para enviar o email de confirmação?

**Opções:**

- **Opção A — SendGrid (recomendado para início)**
  - Prós: free tier 100 emails/dia, boa entregabilidade, integração simples no dashboard Supabase
  - Contras: mais um serviço externo; requer conta Twilio/SendGrid
  - Preço: grátis até 100/dia; ~$15/mês acima disso

- **Opção B — SMTP do Gmail / Google Workspace**
  - Prós: zero custo se já tem a conta
  - Contras: limite 500/dia (Gmail) / 2000/dia (Workspace); má reputação de IP; menos confiável em produção

- **Opção C — Amazon SES**
  - Prós: $0.10/1.000 emails, escala para 1M+ sem problema
  - Contras: conta AWS necessária; setup mais complexo (verificar domínio, sair do sandbox)
  - Melhor para Fase 2+ quando o volume crescer

- **Opção D — Resend.com**
  - Prós: DX excelente, free tier 3.000/mês, API moderna
  - Contras: startup menor (bem financiada mas menor que Twilio/Amazon)

**Recomendação:** Começar com **SendGrid (A)** — gratuito, confiável, se integra diretamente nas
configurações de SMTP do Supabase. Migrar para Amazon SES quando o volume justificar (Fase 2+).

**Como configurar no Supabase:**
Dashboard → Authentication → Settings → SMTP Provider:
```
Host: smtp.sendgrid.net
Port: 587
User: apikey
Pass: SG.xxxxxxxxxxxxxxxxx (sua API Key do SendGrid)
Sender: noreply@clubeusa.com
```

**Status:** PENDENTE

---

### [2026-08-02] Hospedagem do backend e frontend

**Contexto:** O backend FastAPI precisa rodar em algum servidor. O frontend são arquivos HTML estáticos.

**Opções:**

- **Opção A — Railway** (recomendado para início)
  - Prós: deploy automático via GitHub, plano gratuito $5/mês de crédito, zero config de servidor
  - Contras: pago para produção contínua (~$5–20/mês)

- **Opção B — Render**
  - Prós: plano gratuito para serviços web, bom para testes
  - Contras: cold start lento (~30s) no plano gratuito — ruim para UX de usuário real
  - Pago: $7/mês quando lançar para usuários reais

- **Opção C — Fly.io**
  - Prós: plano gratuito generoso, rápido, global
  - Contras: um pouco mais complexo de configurar

**Recomendação:** Render (gratuito, plano free) para testes internos. Migre para Railway ou Render pago
quando lançar para os primeiros usuários.

**Status:** PENDENTE

---

### [2026-08-12] Domínio e URL de produção

**Contexto:**
O Supabase Auth usa o Site URL para gerar links de confirmação de email. Essa URL precisa ser
definida antes do lançamento.

**Pergunta:**
Qual será o domínio final da plataforma? Você já tem o domínio registrado?

**Opções:**
- `clubeusa.com` (ideal — direto, memorável, disponível para registro)
- `clubeusa.com.br` (alternativa BR)
- Subdomínio temporário enquanto o .com não está pronto

**Recomendação:** Registre `clubeusa.com` agora se disponível (~$12/ano no Namecheap ou Cloudflare).
É o ativo mais barato e mais irreversível — configure no Supabase assim que tiver.

**Status:** PENDENTE

---

### [2026-08-02] Alerta: workflow do GitHub Actions com YAML malformado

**Contexto:** O arquivo `.github/workflows/clubeusa-builder.yml` tem indentação incorreta no YAML,
o que provavelmente impede que o workflow rode como esperado no GitHub Actions.

**Pergunta:** Quer que o Claude corrija o YAML para que o workflow automatizado funcione?

**Recomendação:** Sim — é um fix simples e sem risco. Pode resolver no próximo ciclo se aprovar.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-12*
