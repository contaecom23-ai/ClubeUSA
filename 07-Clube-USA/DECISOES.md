# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> O agente NÃO age em itens desta lista sem sua aprovação explícita.

---

## ⚠️ D-001 — AÇÃO URGENTE: 36 PRs abertas, nenhuma mergeada

**Data:** 2026-10-19  
**Status:** PENDENTE — aguardando ação do dono

### Diagnóstico honesto

O agente automático rodou centenas de sessões desde junho de 2026, mas **nenhum código chegou ao main**. O DECISOES.md estava vazio em main porque todas as atualizações ficaram em branches. O loop está quebrado:

```
código criado → PR aberta → PR não mergeada → agente cria outra PR → repetir
```

**Consequência prática:** o produto está no mesmo estado técnico de junho de 2026. Fase 0 não está em main. Nada foi deployado.

### O que você precisa fazer (estimativa: 30 minutos)

**Passo 1 — Merge PR #135** (2 minutos)
- O quê: 2 linhas, correção de segurança (proxy headers Render + timing attack em OTP)
- Risco: zero
- Link: https://github.com/contaecom23-ai/ClubeUSA/pull/135

**Passo 2 — Merge PR #125** (5 minutos)
- O quê: Fase 0 completa (confirmação de email, /i/{code} referral redirect, analytics, anti-fraude IP)
- Estado: limpo, sem conflitos, 16 dias esperando
- Link: https://github.com/contaecom23-ai/ClubeUSA/pull/125

**Passo 3 — Fechar todas as outras PRs** (10 minutos)
- As ~34 PRs restantes são versões antigas e redundantes do mesmo código
- Todas podem ser fechadas sem merge
- O agente não pode fazer isso sozinho (ação no shared state que afeta o projeto)

**Passo 4 — Deploy no Render** (15 minutos)
- Seguir SETUP_PENDENTE.md
- Supabase já está configurado

### Decisão de processo: continuar com o agente?

**Pergunta:** Faz sentido continuar rodando o agente 3x/dia se as PRs não são mergeadas?

**Opções:**
- **A) Mergear + continuar** (recomendado): fazer os 4 passos acima e o agente avança para Fase 1
- **B) Pausar o agente** até ter rotina de revisar PRs (mínimo 1x por semana)
- **C) Continuar igual**: o agente continuará criando PRs sem valor prático

**Recomendação do agente:** Opção A. O código está pronto e com qualidade de produção. O único bloqueio é processo — as PRs não estão sendo mergeadas.

---

## Como usar este arquivo

Quando o agente travar em algo que só você pode decidir (orçamento, preços, produto, gastos, chaves externas, direção estratégica, ações irreversíveis), ele registra aqui e segue para outra tarefa. Você revisa quando quiser.

Formato de cada entrada:
```
### [DATA] Título
**Contexto:** ...
**Pergunta:** ...
**Opções:** ...
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

*Atualizado em: 2026-10-19*
