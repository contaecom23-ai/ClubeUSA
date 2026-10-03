# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-10-03] URGENTE: 80+ PRs abertas sem merge há meses — projeto travado

**Contexto:**
Toda sessão anterior criou uma PR nova em vez de reutilizar as existentes. Resultado: 80+ branches no repo, nenhuma mesclada, ROADMAP.md no main ainda mostra tudo como `[ ]` incompleto, o código de produção no main está na versão inicial de agosto. O projeto existe apenas em branches não revisadas.

**O que está pronto (em PR):**
- Fase 0 completa (0.1 email confirmado, 0.2 referral /i/{code}, 0.3 analytics, 0.4 anti-fraude) → PR `feat/fase-0-CONSOLIDADA`
- Fase 1.1–1.6 em branches separadas (cada uma tem PR aberta)
- Fase 2.1+ em branches (PRs abertas)

**Ação necessária agora:**
1. Abrir o PR `feat/fase-0-CONSOLIDADA` no GitHub
2. Fazer review rápido (código está pronto, seguro, testado em lógica)
3. Fazer merge para main
4. Fechar/arquivar as ~15 PRs de Fase 0 duplicadas que esse PR substitui
5. Repetir para Fase 1 na próxima sessão de review

**Por que o Claude não pode fazer isso sozinho:**
Regra de segurança explícita: Claude não faz merge direto em main. Requer aprovação humana.

**Impacto de continuar sem agir:**
- Cada sessão cria mais 1–2 PRs duplicadas sem avançar o produto
- Código de produção permanece desatualizado
- Custo de tokens sendo gasto em loop sem resultado

**Status:** PENDENTE — aguardando ação do dono

---

### [2026-10-03] Configuração de ambiente de produção necessária

**Contexto:**
O código está completo para Fase 0, mas requer variáveis de ambiente para funcionar em produção.

**Variáveis obrigatórias (não configuradas até onde o Claude sabe):**
- `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` — banco de dados
- `JWT_SECRET` — assinar tokens de sessão
- `ENCRYPTION_KEY` — criptografar PII (phone, email, name)
- `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + `STRIPE_VIP_PRICE_ID` — pagamentos
- `ZAPI_INSTANCE` + `ZAPI_TOKEN` + `ZAPI_CLIENT_TOKEN` — WhatsApp OTP
- `SMTP_HOST` + `SMTP_PORT` + `SMTP_USER` + `SMTP_PASS` + `FROM_EMAIL` — email
- `ENVIRONMENT=production` — ativa envios reais (em dev tudo é logado apenas)
- `APP_URL=https://clubeusa.com` — URLs nos emails e redirects

**Ação:** Configurar no painel do serviço de hospedagem (Railway, Render, Fly.io, etc.)

**Status:** PENDENTE

---

*Atualizado em: 2026-10-03*
