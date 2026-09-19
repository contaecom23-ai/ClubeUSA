# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> O agente NÃO age em itens desta lista sem sua aprovação explícita.
> Revise 1x/dia — cada item tem contexto, opções e recomendação clara.

---

## Decisões Pendentes

---

### [2026-09-19] D-001 — URGENTE: 29+ PRs sem merge — projeto em paralisia

**Contexto:**
Desde julho/2026, o agente construiu as Fases 0.1 a 1.5 em branches separados, abrindo um PR por fase. Total: ~29 PRs abertos. **Nenhum foi merged.** O main continua com o código original (WhatsApp OTP + deals + referral schema). O agente não pode fazer merge — só você pode. Cada rodada sem merge gera mais branches e mais conflitos. O projeto não avança para produção.

**Lista dos PRs prontos para revisão (do mais simples ao mais complexo):**
- PR #100 — Consolidado: referral redirect `/i/{code}` + analytics básico (0.2 + 0.3) — NÃO é draft, pronto para merge
- PR #75 — Email confirmation infra (0.1)
- PR #93 — Vagas de emprego seed manual (1.4)
- PR #94 — Moradia/quartos seed manual (1.5)
- PRs #71–99 — Várias versões/tentativas das mesmas features (muita duplicação)

**Pergunta:** Como quer proceder com os 29 PRs abertos?

**Opções:**
- **A (Recomendado):** Merge o PR #100 agora (é o mais limpo e já está aprovado pelo agente). Feche os outros PRs duplicados manualmente ou me autorize a fechar os mais antigos de cada fase.
- **B:** Me autorize a criar um único "squash branch" consolidando tudo de 0.1 a 1.5 num PR limpo — eu faço isso na próxima rodada.
- **C:** Decida quais features você realmente quer agora (ex: só 0.1 email + 0.2 referral redirect) e me mande fechar o resto.
- **D:** Continue como está — cada rodada cria mais PRs sem merge (não recomendado).

**Recomendação:** Opção A no curto prazo (merge PR #100, fecha duplicatas), depois Opção B se quiser tudo consolidado.

**Status:** PENDENTE — aguardando aprovação do dono

---

### [2026-09-19] D-002 — Arquitetura: email como auth paralelo ou complemento do WhatsApp?

**Contexto:**
O sistema atual usa WhatsApp OTP como autenticação principal (phone_hash + otp_codes). A Fase 0.1 do roadmap pede "email confirmado". Há 6+ PRs abertos implementando email de formas diferentes. Antes de escolher um, você precisa decidir a arquitetura.

**Pergunta:** Qual o papel do email no produto?

**Opções:**
- **A:** Email como campo opcional para notificações (usuário continua entrando via WhatsApp, mas pode salvar um email para receber alertas de promoções). Mantém o que funciona. **Complexidade: baixa.**
- **B:** Email como segundo fator de login paralelo (usuário pode entrar via WhatsApp OU email+senha). **Complexidade: média.** Requer senha, reset flow, etc.
- **C (Recomendado para escala):** Email como auth principal no novo cadastro, WhatsApp como notificação. Alinha com padrão web (compatível com Google OAuth, magic link, etc.). Permite que pessoas que não têm WhatsApp entrem. **Complexidade: média.** Quebra experiência atual dos usuários existentes.

**Recomendação:** Opção A para lançar rápido (adiciona email sem quebrar nada), evoluindo para C no futuro quando houver base de usuários.

**Status:** PENDENTE — aguardando aprovação do dono

---

### [2026-09-19] D-003 — Deploy: onde o app está rodando hoje?

**Contexto:**
O repo tem `render.yaml` configurado e `DEPLOY_RENDER.md` com instruções para Render.com. O app também tem `.env.example` com variáveis de Supabase, Z-API, Stripe, OpenAI. Não sei se o app já está deployado ou só existe no código.

**Pergunta:** O app está rodando em produção? Qual URL?

**Impacto:** Sem saber o estado do deploy, não posso validar se as features funcionam end-to-end. Se não está deployado, a prioridade deveria ser deploy antes de novas features.

**Opções:**
- **A:** App já está em produção (me informe a URL para eu validar).
- **B:** App não está deployado — me autorize a ajustar o `render.yaml` e preparar o checklist de variáveis de ambiente.
- **C:** Não é prioridade agora — continuar apenas construindo localmente.

**Recomendação:** Sem deploy não há produto real. Se não está rodando, Opção B deveria ser a próxima tarefa antes de qualquer feature nova.

**Status:** PENDENTE — aguardando resposta do dono

---

## Decisões Resolvidas

*(nenhuma ainda)*

---

*Atualizado em: 2026-09-19 — Agente autônomo (rodada 3x/dia)*
