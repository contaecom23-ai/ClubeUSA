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

### [2026-08-23] Fase 1.2 — Precisamos rodar a migration do banco?

**Contexto:**
PR `feat/fase-1.2-zip-search` implementou busca por ZIP: migration SQL, geocoding (Nominatim), haversine, endpoints. O código está pronto e testado (17 testes passando). Para funcionar em produção precisa rodar `db/zip_search_migration.sql` no Supabase.

**Pergunta:** Você tem projeto Supabase ativo e pode rodar a migration?

**Opções:**
- **A — Sim:** Abra o SQL Editor do Supabase e execute `07-Clube-USA/clubeusa/db/zip_search_migration.sql`. Claude valida em seguida.
- **B — Ainda sem Supabase:** Decida sobre deploy primeiro (ver decisão de 2026-08-22 abaixo).

**Recomendação:** Opção A se Supabase existe. Migration é não-destrutiva (ADD COLUMN IF NOT EXISTS).

**Status:** PENDENTE

---

### [2026-08-22] Sistema de autenticação — WhatsApp OTP confirmado?

**Contexto:**
O código já em `main` usa **WhatsApp OTP** (Sistema A):
- Registro por telefone → OTP de 6 dígitos via WhatsApp → JWT válido por 7 dias
- Sem senha, sem email obrigatório (email é opcional no cadastro)
- Alinhado com o público: imigrantes brasileiros, WhatsApp é onipresente
- Já implementa: auth, perfil, referral, deals, price tracker, Stripe VIP, painel admin

**Pergunta:** Você confirma o Sistema A (WhatsApp OTP) como base definitiva da plataforma?

**Opções:**
- **A — Sim, WhatsApp OTP (RECOMENDADO):** Plataforma pode ir ao ar em dias. Claude fecha PR #46 e avança para Fase 1.2+.
- **B — Não, quero email + senha:** Claude precisa migrar o código atual. Estimativa: +2–3 semanas.

**Recomendação:** Opção A. WhatsApp OTP é mais simples para o usuário final e alinhado com o hábito do público.

**Status:** PENDENTE

---

### [2026-08-22] Deploy — a plataforma está rodando em algum servidor?

**Contexto:**
O código em `main` está pronto para produção mas não há evidência de deploy. DEPLOY_RENDER.md tem o guia completo.

**Pergunta:** A plataforma está deployada?

**Opções:**
- **A — Sim:** Informe a URL. Claude faz health check e valida o sistema.
- **B — Não:** Siga o guia em `07-Clube-USA/clubeusa/DEPLOY_RENDER.md` (~45 min, ~$7/mês Render).

**Status:** PENDENTE

---

### [2026-08-22] Supabase — banco de dados criado e schema rodado?

**Contexto:**
Schema SQL está em `07-Clube-USA/clubeusa/db/`. Precisa ser rodado no Supabase para criar as tabelas.

**Pergunta:** Você já tem projeto Supabase para o Clube USA com as tabelas criadas?

**Opções:**
- **A — Sim:** Compartilhe `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`. Claude configura e testa.
- **B — Não:** Free tier do Supabase aguenta os primeiros 10.000 usuários. Crie em supabase.com e rode os SQLs em `db/` em ordem (schema.sql → rpc_functions.sql → migrations).

**Status:** PENDENTE

---

## 🚨 Situação atual (2026-08-23) — 14 dias sem merge

PRs esperando revisão/merge:
- **PR #62** (consolida 0.2+0.3+segurança) — MERGEAR PRIMEIRO
- **PR #56** (CI automático) — MERGEAR SEGUNDO
- **PR #65** (Fase 1.2 ZIP search) — MERGEAR APÓS #62

PRs para **fechar** (desatualizados): #3, #4, #5, #9, #12, #14, #16, #19, #20, #46, #51, #52, #53, #54, #55, #57, #58, #59, #60, #61, #63, #64

---

*Atualizado em: 2026-08-23*
