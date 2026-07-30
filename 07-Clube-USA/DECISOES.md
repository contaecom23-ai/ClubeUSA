# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, a pergunta objetiva, opções com prós/contras e recomendação do Claude.
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

### [2026-07-30] Escolha do provedor de email transacional (confirmação de cadastro)

**Contexto:** A Fase 0.1 inclui confirmação de email. O backend já tem a estrutura — `services/email_service.py` tem um stub que loga o link de confirmação em desenvolvimento. Em produção, precisa de um provedor real. O link de confirmação é gerado, basta conectar o envio.

**Pergunta:** Qual provedor de email transacional usar para envio de emails de confirmação, boas-vindas e (futuramente) notificações?

**Opções:**
- **A) SendGrid** — plano gratuito 100 emails/dia; painel simples; muito bem documentado. Contra: limite baixo no free, US$19,95/mês para 40k emails.
- **B) Resend** — moderno, API simples, 100 emails/dia no free, $20/mês para 50k. Melhor DX (developer experience). Recomendado para novos projetos.
- **C) AWS SES** — escala ilimitada, custo por email (~$0.10/1000), mas requer verificação de domínio, mais complexo de configurar. Ótimo para escala (100k+).
- **D) Supabase Auth nativo** — Supabase tem envio de email embutido (usa SMTP configurável). Simplifica ao unificar auth + email. Mas exige migrar para Supabase Auth, o que implicaria refatoração do módulo de auth atual.

**Recomendação:** **Resend** (opção B) para os primeiros 1.000 usuários — API moderna, free tier suficiente para MVP, fácil de integrar em um arquivo. Migrar para AWS SES quando o volume superar 10k emails/mês.

**O que precisa de você:**
1. Criar conta em resend.com
2. Verificar o domínio `clubeusa.com` no painel do Resend
3. Gerar a API key e colocar em `RESEND_API_KEY` no `.env` do servidor
4. Aprovar esta decisão para o Claude implementar o envio real

**Status:** PENDENTE

---

### [2026-07-30] Configuração do Supabase e deploy inicial do backend

**Contexto:** O código do backend (FastAPI) está pronto e testado localmente (24/24 testes passando). A migration SQL (`migrations/001_initial_schema.sql`) precisa ser aplicada em um projeto Supabase real. O backend precisa de uma URL de deploy.

**Pergunta:** Onde fazer o deploy do backend FastAPI e qual projeto Supabase usar?

**Opções para o backend:**
- **A) Railway** — gratuito até $5/mês de uso, deploy via `railway up`, ótimo para MVP. Recomendado.
- **B) Render** — plano gratuito disponível (spin-down após inatividade), adequado para teste.
- **C) Fly.io** — plano gratuito, mais controle, boa latência nos EUA.
- **D) VPS própria** — máximo controle, mais trabalho de manutenção.

**O que precisa de você:**
1. Ter (ou criar) um projeto no Supabase (supabase.com) — gratuito para começar
2. Copiar as credenciais: `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` (nunca a anon key)
3. Rodar a migration: abrir o SQL Editor no Supabase e executar `migrations/001_initial_schema.sql`
4. Escolher onde fazer o deploy do backend e configurar as env vars do `.env.example`
5. Configurar `ALLOWED_ORIGINS` com o domínio do frontend

**Status:** PENDENTE

---

*Atualizado em: 2026-07-30*
