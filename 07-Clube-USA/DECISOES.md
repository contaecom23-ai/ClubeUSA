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

### [2026-07-20] 🚨 CRÍTICO: 28 PRs abertos, nenhum mergeado — loop infinito

**Contexto (atualizado 2026-07-20):**
Há agora **28 PRs abertos**, todos de sessões autônomas, nenhum mergeado. O loop se mantém porque o ROADMAP.md na `main` mostra tudo como `[ ]` — então cada sessão nova reconstrói a Fase 0.1 do zero. Nesta sessão foram criados mais conflitos ao tentar criar o mesmo branch que já existia. O problema é estrutural e só tem uma saída: o dono mesclar PRs.

**Inventário atual (2026-07-20):**
- Fase 0.1 (cadastro): PRs #11, #13, #15, #17, #18, #22, #23, #24, #25, #26, #27 — **11 duplicatas**
- Triage/fix: PRs #10, #21, #28
- Fases posteriores (ainda sem base no main): PRs #12 (1.1), #14 (1.2), #16 (1.3), #19 (1.4), #20 (1.5)
- Outros: #9, #4, #5, #6, #7

**A versão de referência da Fase 0.1 é o PR #11** (`feat/fase-0.1-cadastro-perfil`):
- `backend/`: FastAPI com register, login, /profile (GET+PATCH), JWT validation, rate-limit
- `backend/tests/`: 12 testes com mock (passam sem Supabase real)
- `frontend/`: 5 páginas HTML (index, register, login, profile, verify)
- `backend/db/schema.sql`: migration do banco
- Todos os outros PRs de 0.1 são trabalho duplicado e podem ser fechados.

**O que o dono precisa fazer (ação única que desbloqueia tudo):**

1. **Mergear PR #11** — é a base limpa da plataforma com testes
2. **Fechar** PRs #13, #15, #17, #18, #22, #23, #24, #25, #26, #27 (duplicatas de 0.1)
3. **Fechar** PRs #10, #21, #28 (triage/fix — trabalho absorvido)
4. Avaliar fases posteriores (#12-#20) depois

Após o PR #11 ser mergeado na main, o Claude vai parar de rebuildar 0.1 e avançar para 0.2.

**Pergunta objetiva:** Você quer mergear o PR #11 agora?

**Opções:**
- **Opção A (RECOMENDADA) — Mergear #11 e fechar duplicatas:** 30 minutos de trabalho do dono. Desbloqueia o Claude completamente.
- **Opção B — Fechar TODOS os PRs e reconstruir:** Claude reconstrói do zero com base limpa. Similar ao A mas perde o código já escrito.
- **Opção C — Manter acumulando:** Não recomendado. A cada sessão surgirão mais duplicatas e o backlog fica ingerenciável.

**Recomendação:** Opção A. O PR #11 tem código com qualidade de produção e testes. Mergeá-lo é a ação com maior retorno por minuto gasto.

**Status:** PENDENTE — aguarda ação do dono

**Atualização [2026-07-20 — sessão atual]:** Esta sessão detectou o loop, NÃO criou novo PR duplicado e NÃO fez push de código redundante. O problema persiste apenas porque o dono ainda não mergeou o PR #11.

---

### [2026-07-09] Configuração do Supabase necessária para rodar o backend

**Contexto:**
O backend (PR #11) está pronto tecnicamente, mas precisa de um projeto Supabase configurado para funcionar. Sem isso, o Claude não pode testar o fluxo real de registro/login.

**Pergunta:**
Você já tem um projeto Supabase criado para o Clube USA?

**O que é necessário (sem custo no free tier):**
1. Criar projeto em supabase.com
2. Rodar `07-Clube-USA/backend/db/schema.sql` no SQL Editor
3. Copiar `backend/.env.example` para `backend/.env` e preencher:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_JWT_SECRET`
4. No dashboard Supabase > Auth > URL Configuration: definir `Site URL` e `Redirect URLs` para apontar para os arquivos HTML do frontend (pode ser `http://localhost:PORT` no início)

**Status:** PENDENTE (aguarda resposta do dono)

---

*Atualizado em: 2026-07-20*
