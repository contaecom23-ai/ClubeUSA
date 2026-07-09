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

### [2026-07-09] URGENTE: Fila de PRs acumulados — precisa de revisão humana

**Contexto:**
Encontrei 16+ PRs abertos de rodadas anteriores, nenhum mergeado. Isso cria um problema real:
cada rodada adiciona código em branches isoladas que o dono ainda não revisou nem integrou.
O ROADMAP.md no main ainda mostra tudo como `[ ]` (nada feito), mas na prática há código em staging.

PRs notáveis abertos (ordenados por prioridade):
- PR #10 (`claude/fix-workflow-yaml-e-docs-main`): **"MERGEAR ESTE PRIMEIRO"** — corrige o workflow de CI quebrado e sincroniza docs. Bloqueador para os outros.
- PR #11 (`feat/fase-0.1-cadastro-perfil`): Cadastro + perfil + email confirmado — atualizado nesta rodada com código limpo e 12 testes passando.
- PR #13 e #15: Outras implementações de 0.1 de rodadas anteriores. Depois do #11 ser mergeado, estes devem ser fechados (trabalho duplicado).
- PR #5 (0.4), #4 (0.3), #6, #7, #9: Fases posteriores em aberto.
- PR #12 (1.1), #14 (1.2), #16 (1.3): Fases 1.x sem a base (0.1) mergeada.

**Pergunta:**
Você quer revisar e mergear os PRs? Como proceder?

**Opções:**
- **Opção A — Revisar e mergear progressivamente:** Mergear #10 → #11 → fechar duplicatas (#13, #15) → revisar o restante. Recomendada. Permite que o Claude construa em cima de código já integrado.
- **Opção B — Fechar tudo e começar do zero:** Fechar todos os PRs abertos e deixar o Claude reconstruir sequencialmente. Mais lento mas base mais limpa.
- **Opção C — Manter acumulando:** Continuar com o ciclo atual. Não recomendado — o backlog vai crescer e nenhum PR terá valor real até ser mergeado.

**Recomendação:**
**Opção A.** Ordem: mergear #10 primeiro (corrige CI), depois #11 (base da plataforma com testes limpos), fechar #13 e #15 (duplicatas de 0.1). Depois revisar sequencialmente. Isso desbloqueia o Claude para avançar nas fases seguintes com código integrado.

**Status:** PENDENTE

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

*Atualizado em: 2026-07-09*
