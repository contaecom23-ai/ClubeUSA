# DECISOES — Clube USA

> Fila de decisoes que dependem do dono do produto (voce).
> Para cada item: data, contexto, pergunta objetiva, opcoes com pros/contras e recomendacao.
> Claude NAO age em itens desta lista sem sua aprovacao explicita.

---

## Como usar

Quando o Claude travar em algo que so voce pode decidir (orcamento, precos, escolhas de produto/negocio, aprovacao de gasto, chaves/contas externas, direcao estrategica, qualquer coisa irreversivel ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisoes Pendentes

### [2026-08-19] URGENTE: Fila de PRs acumulados sem merge

**Contexto:**
O repositorio acumulou 17 PRs abertos sem nenhum merge. O codigo no main esta basicamente nos arquivos originais — toda a implementacao das Fases 0 e 1 existe APENAS em branches. Isso cria risco real: branches envelhecem, ficam conflitantes, e o trabalho feito perde valor se nao for integrado.

**Pergunta:**
Voce quer revisar e mergear os PRs das Fases 0.1, 0.2, 0.3 e 0.4 agora, ou quer mudar de abordagem?

**PRs prioritarios para revisar (todos draft, todos alvos do main):**
- **PR #46** - feat: Fase 0.1 Cadastro + auth [MERGEAR ESTE - marcado pelo proprio agente]
- **PR #54** - feat(0.1): confirmacao de email (endpoints + migracao + testes)
- **PR #52** - feat(0.2): referral rastreavel (/i/{code} redirect)
- **PR #57** - fix(referral): captura ?ref=CODE no frontend
- **PR #55** - feat(0.3): analytics basico
- **PR #56** - ci: workflow pytest automatico
- **PR #53** - docs: ROADMAP + DECISOES refletindo estado real
- **Novo PR** - feat(0.4): cadastro valido + anti-fraude (aberto hoje)

**Opcoes:**

- **Opcao A (RECOMENDADA):** Mergear os PRs em ordem: #46 -> #54 -> #52 -> #57 -> #55 -> #56 -> novo #0.4. Depois aplicar as migracoes SQL no Supabase. Isso leva a plataforma ao estado real que o codigo representa.

- **Opcao B:** Descartar os PRs antigos (da chain stacked: #3, #4, #5, #9, #12, #14, #16, #19, #20) que sao versoes antigas, e mergear APENAS os novos que apontam para main (#46, #52, #53, #54, #55, #56, #57, novo 0.4). Os antigos podem ser fechados sem merge.

- **Opcao C:** Solicitar ao Claude um PR consolidado que junte tudo em um so commit limpo sobre main.

**Recomendacao:** Opcao B. Fechar os 9 PRs stacked antigos (eles sao versoes supercedidas) e mergear os PRs novos em ordem. O agente pode fechar os antigos se voce confirmar.

**Status:** PENDENTE — aguardando sua decisao

---

### [2026-08-19] Anti-fraude: blocklist local vs API externa

**Contexto:**
Fase 0.4 implementou anti-fraude com blocklist local de ~90 dominios descartaveis. Funciona para os primeiros 1k-10k usuarios. Em escala maior, novos dominios surgem constantemente.

**Pergunta:**
Em qual momento (numero de usuarios) migrar para API externa de validacao de email?

**Opcoes:**
- **Opcao A (atual):** Blocklist local. Custo zero. Cobre >95% dos casos praticos para 1k-50k usuarios.
- **Opcao B:** API externa (ex: Abstract API, Hunter.io) em ~50k usuarios. Custo: ~$20-50/mes. Precisao muito maior.

**Recomendacao:** Ficar com Opcao A ate 50k usuarios. Atualizar a blocklist periodicamente.

**Status:** PENDENTE (nao urgente — revisitar quando chegar em 50k)

---

*Atualizado em: 2026-08-19*
