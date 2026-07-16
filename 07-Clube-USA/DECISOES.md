# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-07-16] Consolidar implementação backend: `backend/` vs `api/`

**Contexto:** Dois runs autônomos implementaram a Fase 0.1 em paralelo, gerando duas implementações do backend:

- `07-Clube-USA/backend/` (run anterior, 2026-07-15): FastAPI com JWT via stdlib (hmac+hashlib), bcrypt com pré-hash SHA-256, 28 testes
- `07-Clube-USA/api/` (este run, 2026-07-16): FastAPI com python-jose, bcrypt direto sem passlib (compatível com bcrypt v5), 43 testes

Ambas funcionam. Ter dois backends é confuso e aumenta manutenção.

**Pergunta:** Qual backend manter como implementação canônica?

**Opções:**

- **Manter `api/`** *(recomendado)*
  - 43 testes vs 28
  - Usa bcrypt diretamente (passlib é unmaintained e incompatível com bcrypt v5)
  - python-jose para JWT (mais explícito e padrão da indústria Python)
  - Schema SQL em `schema.sql` (raiz de 07-Clube-USA)
  - Pode deletar `backend/` e `database/`

- **Manter `backend/`**
  - Evita dependência do python-jose (usa apenas stdlib)
  - Mais compacto em dependências
  - Pode deletar `api/` e `schema.sql`

**Recomendação:** Manter `api/`. A abordagem com python-jose é mais clara e testada. O bcrypt direto é a solução correta (passlib foi arquivado/unmaintained). Você pode deletar a pasta `backend/` e o arquivo `database/001_initial_schema.sql` quando decidir.

**Status:** PENDENTE (Claude não deleta sem sua aprovação)

---

### [2026-07-16] Provedor de email para confirmação de conta

**Contexto:** O fluxo de confirmação de email está implementado. Em dev, o token aparece no log do servidor. Em produção, um provedor de email é necessário.

**Pergunta:** Qual provedor de email usar para enviar confirmações em produção?

**Opções:**

- **Resend.com** *(recomendado)*
  - Prós: tier grátis 3.000 emails/mês, API moderna, boa entregabilidade
  - Custo: $0 até 3k/mês; $20/mês até 50k

- **SendGrid (Twilio)**
  - Prós: líder de mercado, muito confiável
  - Contras: tier grátis apenas 100 emails/dia (muito baixo)
  - Custo: $0 até 100/dia; $19.95/mês até 50k

- **AWS SES**
  - Prós: custo baixíssimo em escala ($0.10/1k emails)
  - Contras: configuração mais complexa (domínio verificado, sandbox)

**Recomendação:** Resend.com. Para os primeiros 1.000 usuários é suficiente e o código já está pronto.

**O que você precisa fazer:**
1. Criar conta em resend.com e verificar seu domínio (ex: clubeusa.com)
2. Gerar API key
3. Adicionar ao `.env`: `EMAIL_PROVIDER=resend` e `EMAIL_API_KEY=re_...`

**Status:** PENDENTE

---

### [2026-07-16] Projeto Supabase (banco de dados)

**Contexto:** A API usa Supabase como banco via `service_role`. O schema SQL está em `07-Clube-USA/schema.sql`.

**O que você precisa fazer:**
1. Criar projeto em supabase.com (grátis — 2 projetos grátis por conta)
2. Copiar `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` do painel (Settings → API)
3. Executar `07-Clube-USA/schema.sql` no SQL Editor do Supabase
4. Adicionar as vars ao `.env` do servidor

**Status:** PENDENTE

---

### [2026-07-16] URL/Domínio de produção

**Contexto:** O `FRONTEND_URL` e `API_URL` precisam ser configurados antes de ir a produção (são usados nos links de confirmação de email).

**O que você precisa definir:**
- Domínio da plataforma (ex: clubeusa.com)
- URL da API (pode ser o mesmo domínio ou um subdomínio como api.clubeusa.com)
- Configurar no `.env`: `FRONTEND_URL=https://clubeusa.com`, `API_URL=https://api.clubeusa.com`

**Status:** PENDENTE

---

### [2026-07-16] Infraestrutura de deploy

**Pergunta:** Onde hospedar a API inicialmente?

**Opções:**

- **Railway.app** *(recomendado para MVP)*
  - Deploy via GitHub em minutos, HTTPS automático
  - Custo: ~$5-10/mês

- **Render.com**
  - Tier grátis existe mas dorme após 15min (inaceitável para produção)
  - Custo: $7/mês para instância sempre-ativa

- **VPS (DigitalOcean/Hetzner)**
  - Mais barato em escala, requer configuração manual
  - Custo: $6-12/mês

**Recomendação:** Railway para MVP. Zero infra manual, deploy automático.

**Status:** PENDENTE

---

### [2026-07-16] Fix do workflow GitHub Actions — RESOLVIDO

**Contexto:** O workflow `.github/workflows/clubeusa-builder.yml` tinha YAML com indentação completamente quebrada. O builder nunca teria rodado com aquele YAML. Foi corrigido neste PR.

**Status:** RESOLVIDO (correção de bug técnico, não requer decisão)

---

*Atualizado em: 2026-07-16*
