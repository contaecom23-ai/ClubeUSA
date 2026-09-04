# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.
> Atualizado em: 2026-09-04

---

## ⚠️ BLOQUEIO CRÍTICO DO PROJETO

**30 PRs abertos, NENHUM foi mergeado desde o início do projeto.**

O projeto está parado. Tudo o que o Claude construiu está em branches que nunca entraram na main.
A app em produção (main) tem zero funcionalidades das Fases 0–4.

**Ação imediata necessária:** Você precisa decidir como tratar o backlog de PRs antes que o Claude continue qualquer trabalho novo.

---

## Decisões Pendentes

### [2026-09-04] D-001: O que fazer com os 30 PRs abertos sem merge

**Contexto:**
- 30 PRs abertos, todos draft, desde agosto de 2026.
- Nenhum foi revisado nem mergeado.
- Fases 0.1, 0.2, 0.3, 0.4, 1.2, 1.3, 2.1 foram implementadas em branches — nada está no main.
- A main só tem: landing page, deal scanner (1.6), forum/news/AI chat.
- Os PRs mais antigos (agosto) podem ter conflitos entre si e com os mais novos.
- O Claude continua rodando 3x/dia e criando novos PRs que ninguém revisa.

**Pergunta objetiva:**
Como você quer lidar com os PRs acumulados? Escolha uma opção abaixo.

**Opções:**

- **Opção A — Merge seletivo**: Você revisa e mergea os PRs críticos agora. Recomendados para merge imediato: #62 (consolida 0.2+0.3+segurança), #75 (email confirmation 0.1), #78 (fix auth token VIP). Os outros podem ser fechados.

- **Opção B — Cleanup + recomeço limpo**: Fechar todos os 30 PRs. O Claude recomeça as features mais importantes do zero, em um único PR por fase, com código atualizado sem conflitos.

- **Opção C — Pausa no Claude**: Você não tem tempo para revisar PRs agora. Desativar o schedule do Claude até ter bandwidth para revisar.

- **Opção D — Merge em massa (arriscado)**: Mergear todos os PRs de uma vez sem revisão. Não recomendado — há branches que se sobrepõem e podem quebrar a app.

**Recomendação do Claude:** **Opção B** (cleanup + recomeço). Os PRs antigos têm conflitos potenciais entre si, o código nas branches não foi testado em integração, e manter 30 PRs abertos torna impossível ter uma visão clara do estado do projeto. Fechar tudo e recomeçar com um PR por fase é mais seguro e mais rápido do que tentar mergear 30 branches conflitantes.

**Status:** PENDENTE — aguardando decisão do dono

---

### [2026-09-04] D-002: Deployment — a app está em produção?

**Contexto:**
- O PR #80 aponta que Z-API é obrigatório para OTP mas as credenciais não estão configuradas.
- Não há confirmação de que a app está rodando em produção (Render ou outro).
- O DEPLOYMENT.md existe no repo mas não está claro se foi seguido.

**Pergunta objetiva:**
A plataforma Clube USA tem uma URL pública funcionando hoje?

**Opções:**
- **Sim**: Me dê a URL e eu verifico o status.
- **Não (bloqueado por Z-API/Supabase)**: Me dê as credenciais (SUPABASE_URL, SUPABASE_KEY, ZAPI_TOKEN) como variáveis de ambiente no Render, e eu verifico o deploy.
- **Não (intencional — ainda não é hora)**: Ok, continuamos só com desenvolvimento local.

**Recomendação:** Esclarecer isso é pré-requisito para qualquer trabalho de Fase 0. Sem deploy, nenhuma feature de cadastro/referral pode ser testada por usuários reais.

**Status:** PENDENTE — aguardando confirmação do dono

---

### [2026-09-04] D-003: Prioridade real — o que você quer lançar PRIMEIRO?

**Contexto:**
O roadmap tem 6 fases. Mas o Claude precisa de foco. Com 30 PRs acumulados, fica claro que o escopo está grande demais.

**Pergunta objetiva:**
Se você pudesse ter UMA coisa funcionando para usuários reais nos próximos 7 dias, qual seria?

**Opções:**
- **A) Cadastro + email confirmado (Fase 0.1)** — base para tudo, sem isso nada funciona.
- **B) Link de referral (Fase 0.2)** — para você já começar a convidar pessoas e rastrear quem veio de quem.
- **C) Promoções/Achados (Fase 1.1)** — o carro-chefe do produto, o que vai fazer pessoas voltarem.
- **D) Diretório de empresas + assinatura (Fase 2.1)** — receita imediata.

**Recomendação:** **A) Cadastro + email (0.1)** — sem isso, as outras fases não têm base. É o desbloqueador universal.

**Status:** PENDENTE — aguardando decisão do dono

---

## Como responder

Abra o PR deste arquivo e deixe um comentário com sua decisão para cada item acima. O Claude lerá na próxima rodada e agirá imediatamente.

Ou envie uma mensagem direta: "D-001: Opção B", "D-002: Não, bloqueado por X", "D-003: A".

---

## Decisões Resolvidas

*(nenhuma ainda)*
