# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## ⚠️ BLOQUEIO CRÍTICO — LEIA ISTO PRIMEIRO

### [2026-07-29] 33 PRs abertos, zero mergeados — plataforma parada há semanas ⚠️ DIA 3 SEM AÇÃO

**O que está acontecendo:**
Este agente autônomo roda 3x/dia. A cada execução, detecta que o branch `main` não tem código (só ROADMAP.md e DECISOES.md), implementa a Fase 0.1 do zero, abre um PR, e para. O próximo run não vê o PR como "código na main" e repete tudo. **Resultado: 33 PRs abertos, 15+ implementando a mesma Fase 0.1.**

**Histórico de runs sem ação:**
- 2026-07-27: bloqueio documentado pela primeira vez, 32 PRs
- 2026-07-28: nenhum PR mergeado, 33 PRs
- 2026-07-29: nenhum PR mergeado, ainda 33 PRs (este run atualizou PR #33, sem criar novo PR)

**O loop para em 15 minutos de trabalho seu, em 3 passos:**

### PASSO 1 — Mergear PR #32 (fix do workflow YAML, 3 arquivos, zero código)
- URL: https://github.com/contaecom23-ai/ClubeUSA/pull/32
- Corrige o YAML quebrado do GitHub Actions para o CI funcionar em todos os PRs
- Seguro: só indentação, sem mudança de lógica

### PASSO 2 — Mergear PR #31 (Fase 0.1 completa, FastAPI + testes + frontend)
- URL: https://github.com/contaecom23-ai/ClubeUSA/pull/31
- Versão mais recente e limpa da Fase 0.1 (21 testes passando, bcrypt, JWT, rate-limit, email)
- Após merge: o agente detecta Fase 0.1 como concluída e avança para Fase 0.2 (Referral)

### PASSO 3 — Fechar os outros 30 PRs como duplicatas
- Selecione todos e feche com comentário: "Duplicata — Fase 0.1 implementada via PR #31"
- PRs a fechar: #1 a #30 (exceto #31 e #32 já mergeados)

---

## Decisões Pendentes de Infra (após o merge da Fase 0.1)

### [2026-07-27] Supabase — projeto e credenciais

**Você precisa:**
1. Criar projeto em supabase.com (gratuito)
2. Executar `07-Clube-USA/backend/migrations/001_initial_schema.sql` no SQL Editor
3. Copiar URL + service_role key para o `.env` do backend

### [2026-07-27] Email transacional (para confirmação de cadastro)

**Recomendação:** Resend.com — gratuito até 3.000 emails/mês, setup em 10 min
- Crie conta, gere API key, configure: `SMTP_HOST=smtp.resend.com`, `SMTP_USER=resend`, `SMTP_PASSWORD=re_xxxx`

### [2026-07-27] Deploy do backend

**Recomendação:** Railway.app (gratuito para começar)
- Conecte o repositório, configure env vars, comando: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### [2026-07-27] Deploy do frontend

**Recomendação:** Netlify (gratuito, drag-and-drop da pasta `07-Clube-USA/frontend/`)
- Antes: edite `frontend/static/app.js` linha 1 com a URL real do backend

---

*Atualizado em: 2026-07-29 — run autônomo (bloqueio crítico, nenhum PR novo criado, aguardando merge de PR #32 e #31)*
