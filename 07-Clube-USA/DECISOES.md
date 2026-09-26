# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## 🚨 Decisões Pendentes

---

### [2026-09-26] D-001: PARALISIA DE MERGE — 30+ PRs abertos, nenhum mergeado

**Contexto:**
O agente autônomo roda 3x/dia desde agosto. Abriu 30+ PRs. **Nenhum foi mergeado.** O ROADMAP.md no main mostra a Fase 0 inteira como não concluída — e a cada sessão o bot vê isso, assume que o trabalho não existe, e cria PRs duplicados para o mesmo item. Resultado: há 4+ PRs para email confirmation e 5+ para referral. O problema NÃO é falta de código. O problema é que **o projeto só avança quando você mergeia**.

Esta entrada D-001 existia no PR #111 (aberto 2026-09-25). Ainda não foi mergeado, então o main continua mostrando "nenhuma decisão pendente". Essa é a prova do problema.

**Estado atual do main (o que está em produção hoje):**
| Feature | Status no main | PR pronto |
|---|---|---|
| Segurança: webhook auth + fd leak | **ausente** | PR #110 (não-draft) |
| Email confirmation (Fase 0.1) | **ausente** | PR #106 |
| Referral `/i/{code}` (Fase 0.2) | **ausente** | PR #102 + PR #112 |
| Analytics growth (Fase 0.3) | **ausente** | PR #109 |
| Cadastro válido + anti-fraude (Fase 0.4) | **ausente** | PR #104 |
| Testes: 48 casos multi-tenant | **ausente** | PR #103 |
| Promoções/Achados (Fase 1.1) | **ausente** | PR #113 |

**O problema dos duplicados:** Os PRs mais antigos (#61–#101) cobrem o mesmo trabalho em versões mais velhas. Feche-os como supersedidos após mergear os novos.

**Recomendação — ordem exata de merge (30 minutos de trabalho):**

1. **PR #110** — fix(security): 3 correções de segurança. Não-draft. Zero risco funcional. Merge primeiro.
2. **PR #111** — docs: DECISOES.md atualizado (este arquivo). Merge para o main refletir a fila de decisões.
3. **PR #106** — feat(0.1): email confirmation. Merge para fechar Fase 0.1.
4. **PR #102** — feat(0.2): referral redirect `/i/{code}`. Depois: PR #112 (correção da captura de `?ref=`).
5. **PR #109** — feat(0.3): analytics growth endpoint. Fecha Fase 0.3.
6. **PR #104** — feat(0.4): cadastro válido + anti-fraude. Fecha Fase 0.4.
7. **PR #103** — test: 48 testes cobrindo auth + billing + isolamento multi-tenant.

**PRs antigos para fechar após o merge acima** (duplicatas):
`#61, #62, #63, #65, #66, #67, #68, #69, #70, #71, #72, #73, #74, #75, #76, #77, #78, #79, #80, #81` — feche como "Supersedido pelos PRs mais recentes".

**Opções:**
- **Opção A (recomendada):** Mergear os 7 PRs na ordem acima (~30 minutos). Projeto sai do zero.
- **Opção B:** Fechar TODOS os PRs e criar um PR consolidado limpo com todo o trabalho. Mais demorado, resultado mais organizado.
- **Opção C:** Criar branch `develop`, dar permissão ao bot para mergear lá automaticamente. Você só revisa `develop → main`. Reduz atrito mas requer configuração.

**Status:** PENDENTE — aguardando decisão do dono

---

### [2026-09-26] D-002: App não está deployado em produção

**Contexto:**
O Supabase tem 21 tabelas criadas. O código existe. Mas o app **não está no ar**. O SETUP_PENDENTE.md lista os 5 passos necessários (chaves Supabase, gerar JWT_SECRET, criar serviço no Render, configurar env vars, teste e2e).

Enquanto o app não estiver no ar, nenhum usuário real pode se cadastrar. Todo o trabalho de email confirmation, referral, analytics, etc. é irrelevante sem usuários reais.

**Pergunta:**
Quando você vai fazer o setup do Render + configurar as variáveis de ambiente?

**O que você precisa fazer (detalhado no SETUP_PENDENTE.md):**
1. Copiar as chaves do Supabase para `.env` (painel já estava aberto)
2. Rodar `python utils/security.py` para gerar `ENCRYPTION_KEY` e `JWT_SECRET`
3. Criar serviço no Render apontando para `07-Clube-USA/clubeusa/render.yaml`
4. Preencher as variáveis de ambiente no Render
5. Testar: cadastro → login → rastrear produto

**Observação:** Stripe não é necessário agora. `STRIPE_*` pode ficar em branco.

**Recomendação:** Faça isso imediatamente após resolver D-001 (merge dos PRs). O deploy leva ~20 minutos.

**Status:** PENDENTE — aguardando ação do dono

---

### [2026-09-26] D-003: Fase 1.3 — Influenciadores PAGO POR RESULTADO (decisão de negócio)

**Contexto:**
Fase 1.3 do roadmap: programa de influenciadores pagos por cadastro válido, com selos Parceiro/Embaixador/Hall da Fama. A infraestrutura de referral (Fase 0.2) já existe nos PRs. O que falta é a decisão de negócio.

**Perguntas que precisam de resposta antes de construir:**

1. **Quanto pagar por cadastro válido?** Ex: $1, $2, $5 por usuário que confirmou email e fez ≥1 ação?
2. **Qual o teto de orçamento mensal?** Ex: $500/mês máximo enquanto valida o canal.
3. **Como pagar?** Stripe Connect (automatizado), PayPal manual, Pix (para influenciadores no Brasil), ou crédito na plataforma?
4. **Quando um cadastro é "válido" para fins de pagamento?** (Isso conecta com D-002 sobre email confirmation — se email não é obrigatório, o critério muda.)
5. **Quem pode ser influenciador?** Qualquer usuário cadastrado? Processo de aprovação?

**Impacto técnico das respostas:**
- Pagar via Stripe Connect → requer setup de conta Connect + aprovação do Stripe (semanas)
- Pagar manualmente → implementação trivial (só rastreamento de clicks + lista para pagar)
- Crédito na plataforma → mais simples, mas menos atrativo para influenciadores

**Recomendação do Claude:**
Comece com rastreamento manual + pagamento manual. Defina: $2/cadastro válido, teto $200/mês, cadastro válido = email confirmado + 1 login nos 7 dias seguintes. Automatize depois que o canal provar ROI. Isso pode ser implementado em 2-3 dias após o deploy.

**Status:** PENDENTE — aguardando decisão do dono

---

### [2026-09-26] D-004: Autenticação — WhatsApp OTP vs Email/Senha

**Contexto:**
O sistema atual autentica via WhatsApp OTP. O ROADMAP Fase 0.1 pede "email confirmado". Há tensão entre o que existe (WhatsApp OTP, funcional, zero fricção) e o que o roadmap pede (email).

**Pergunta:**
Email confirmation deve ser:
- **(A) Obrigatório** para completar cadastro (sem email confirmado = sem acesso)?
- **(B) Opcional** — colete email, confirme para desbloquear features extras, mas permita uso com só WhatsApp?
- **(C) Abandonar** email confirmation — focar 100% em WhatsApp OTP?

**Trade-offs reais:**
- A: Menor fraude, mais segurança, mas aumenta fricção. Para primeiros 1.000 usuários: risco de abandono.
- B: Melhor conversão. Email como canal de marketing (newsletter, retargeting). Recomendado para early-stage.
- C: Mais simples. Problema sério: sem email você não tem canal de reengajamento barato. WhatsApp tem custo por mensagem.

**Recomendação do Claude:** Opção B. Email não obrigatório para usar o app, mas "confirme email e ganhe +100 pontos de reputação". Implementação já está no PR #106. Só precisa da sua decisão sobre qual fluxo usar.

**Status:** PENDENTE — aguardando decisão do dono

---

*Atualizado em: 2026-09-26*
