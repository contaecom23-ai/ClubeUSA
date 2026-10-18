# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## ⚠️ D-001 [2026-10-18] PARALISIA DE MERGE — PLANO DE DESBLOQUEIO

**Status:** PENDENTE — requer ação do dono

**Contexto:**

Há 35+ PRs abertos desde junho de 2026. Nenhum foi mergeado. O agent roda 3x/dia, vê `main` estático com ROADMAP todo desmarcado, e continua criando PRs que se acumulam sem uso. O código para Fase 0.1–0.4 está pronto e esperando há semanas. A plataforma não avança porque o processo de revisão está travado.

**Ação necessária — execute nesta ordem:**

### PASSO 1 — Merge PR #135 (5 minutos, zero risco)
**Link:** https://github.com/contaecom23-ai/ClubeUSA/pull/135  
**O que é:** Correção de segurança em 2 linhas — `--proxy-headers` no uvicorn (fix rate limiting em produção) + comparação de OTP via `hmac.compare_digest` (resistência a timing attack)  
**Risco:** Reversível. Não requer migração de banco. Não muda API.  
**Por que primeiro:** É um fix de segurança que afeta a produção hoje.

### PASSO 2 — Merge PR #125 (30 minutos, revisão do diff)
**Link:** https://github.com/contaecom23-ai/ClubeUSA/pull/125  
**O que é:** Fase 0 completa (0.1 email confirmado + 0.2 referral rastreável + 0.3 analytics + 0.4 anti-fraude). 833 linhas, 12 arquivos. Criado em 2026-10-03. Sem conflitos com main.  
**O que você precisa fazer após o merge:**
- Executar as 2 migrações SQL no painel Supabase (idempotentes, ordem: email_confirmation_migration.sql → fase0_complementar_migration.sql)
- Configurar variáveis de ambiente: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM no Render  

### PASSO 3 — Fechar todos os outros 30+ PRs como supersedidos
Após os merges acima, fechar os PRs duplicados com a mensagem: "Superseded by PR #125 and PR #135."  
Os PRs de docs/DECISOES (#111, #114, #118, #122, #124, #126, #131) também podem ser fechados — este arquivo (via novo PR) é a versão atual.

---

## D-002 [2026-10-18] Configuração SMTP para email de confirmação

**Status:** PENDENTE — requer ação do dono

**Contexto:** PR #125 implementa email de confirmação mas a funcionalidade só opera em produção com credenciais SMTP configuradas. Sem elas, a plataforma cai em modo de desenvolvimento (loga a URL de confirmação em vez de enviar email).

**Pergunta:** Qual provedor SMTP usar?

**Opções:**
- **A) Resend.com** — $0/mês até 3.000 emails/mês, API simples, deliverability alta. Recomendado para 0–1.000 usuários.
- **B) SendGrid** — freemium 100 emails/dia, mais complexo, escala melhor mas overkill agora.
- **C) Gmail SMTP** — grátis mas frágil para produção (bloqueio por volume/spam, má deliverability).

**Recomendação:** Opção A (Resend.com). Cria conta gratuita, gera API key, configura como SMTP em `api.resend.com:465` no Render.

---

*Atualizado em: 2026-10-18*
