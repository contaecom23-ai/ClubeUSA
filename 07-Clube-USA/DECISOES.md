# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ DECISÃO CRÍTICA — BLOQUEIO TOTAL DO PROJETO

### [2026-07-19] 27+ PRs abertos sem merge — o builder está em loop

**Contexto:**
O builder autônomo (Claude Code) roda 3x ao dia mas **nenhum PR foi mergeado até hoje**. Resultado: cada execução vê o `main` vazio (sem código), assume que nada foi feito e cria um novo branch com os mesmos arquivos. Há **27+ PRs abertos**, a maioria duplicatas da Fase 0.1.

Isso não é um bug do builder — é um processo quebrado. O builder fez sua parte (criou código, abriu PRs). A etapa que falta é você revisar e mergear.

**Diagnóstico técnico:**
- O workflow `.github/workflows/clubeusa-builder.yml` **estava com YAML inválido** (indentação errada), portanto provavelmente nunca rodou pelo Actions. Este PR inclui a correção.
- Mesmo que o Actions não tenha rodado, os PRs foram criados manualmente e existem no repositório.
- O `main` branch contém apenas `ROADMAP.md` e `DECISOES.md`. Zero código.

**O branch mais completo disponível:**
`claude/fase-0.1-cadastro-perfil-email` — tem commits através da Fase 1.1 (Promoções/Achados), incluindo:
- Fase 0.1: auth, perfil, email confirmado
- Fase 0.2: sistema de referral
- Fase 0.3: analytics básico
- Fase 0.4: cadastro válido + anti-fraude
- Fase 1.1: feed de promoções/achados

**Pergunta:**
Você quer mergear o progresso existente, ou prefere descartar tudo e recomeçar com uma estratégia diferente?

**Opções:**

- **Opção A — Mergear o PR mais completo (RECOMENDADO)**
  - Vá ao PR da branch `claude/fase-0.1-cadastro-perfil-email`
  - Revise rapidamente o código
  - Feche os outros 26+ PRs (são duplicatas)
  - O builder pode então continuar da Fase 1.2 em diante
  - Prós: aproveita todo o trabalho já feito; desbloqueia imediatamente
  - Contras: código não foi testado com banco real (ainda precisa de Supabase configurado)

- **Opção B — Descartar tudo e recomeçar limpo**
  - Feche todos os 27+ PRs
  - Responda aqui com "recomeçar" e defina a estratégia que quer
  - O builder começa do zero na próxima execução
  - Prós: código mais revisado, estrutura definida por você
  - Contras: perde todo o trabalho acumulado

- **Opção C — Revisar e selecionar manualmente**
  - Abra cada PR e escolha qual código usar
  - Prós: controle total
  - Contras: demanda tempo significativo (27+ PRs)

**Recomendação:**
**Opção A**. O código existente na branch `claude/fase-0.1-cadastro-perfil-email` tem qualidade suficiente para um MVP. Faz sentido aproveitar. Depois de mergear, configure o Supabase e o provedor de email (ver decisões abaixo) para ter o ambiente funcionando. O builder continua da Fase 1.2 em diante automaticamente.

**Ação imediata necessária (hoje):**
1. Abra a lista de PRs: https://github.com/contaecom23-ai/ClubeUSA/pulls
2. Encontre o PR do branch `claude/fase-0.1-cadastro-perfil-email` (ou o mais completo)
3. Mergea na main
4. Feche os outros PRs com a mensagem "Duplicata — mergeado via PR #X"

**Status:** PENDENTE (bloqueante — o projeto não avança sem esta decisão)

---

## Decisões Técnicas Pendentes

### [2026-07-19] Configuração do banco Supabase

**Contexto:**
O backend usa `asyncpg` conectando diretamente ao PostgreSQL do Supabase. A migration SQL existe em `07-Clube-USA/backend/migrations/001_initial_schema.sql` e precisa ser executada manualmente no painel Supabase.

**Ação necessária:**
1. Crie (ou use) um projeto em supabase.com
2. Execute o arquivo `001_initial_schema.sql` no SQL Editor do painel
3. Copie a connection string (Project Settings > Database > Connection string > Transaction mode)
4. Configure no servidor: `DATABASE_URL=postgresql://...`
5. Gere um SECRET_KEY seguro: `python -c "import secrets; print(secrets.token_hex(64))"`

**Status:** PENDENTE

---

### [2026-07-19] Provedor de email transacional

**Contexto:**
O serviço de confirmação de email existe mas em dev apenas loga no console. Para produção, precisa de um provedor configurado.

**Recomendação:** Resend (resend.com) — gratuito até 3.000 emails/mês, 5 min para configurar.

**Ação necessária:**
1. Crie conta em resend.com
2. Verifique o domínio do Clube USA
3. Gere API Key
4. Configure: `EMAIL_PROVIDER=resend` e `RESEND_API_KEY=re_xxx`

**Status:** PENDENTE

---

*Atualizado em: 2026-07-19*
