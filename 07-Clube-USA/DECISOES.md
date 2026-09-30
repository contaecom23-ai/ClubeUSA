# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto, aprovação de gasto, chaves externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### D-001 [2026-09-30] PARALISIA DE MERGE — ação humana bloqueando o projeto

**Contexto:**
Este aviso foi registrado em PRs: #69, #72, #73, #74, #76, #77, #79, #81, #111, #114, #118 e agora novamente em 2026-09-30. O branch `main` está congelado desde 2026-06-23. Há agora **31 PRs abertos** com código real implementado, nenhum mergeado. Abrir mais PRs sem merge só aumenta a dívida.

O agente seguirá bloqueado para novas features — tudo de Fases 0.1 a 1.4 já tem PR pronto. A única coisa útil agora é o merge.

**Pergunta objetiva:**
Qual PR você quer mergear primeiro? (Ou escolha Opção A abaixo para o roteiro completo.)

**Opções:**

**A) Mergear em ordem — RECOMENDADO** — Cada PR leva ~30 segundos no GitHub.

Ordem de merge (conflitos resolvíveis — o GitHub avisa):
1. **PR #110** `fix(security)` — correções críticas de segurança — vem primeiro
2. **PR #103** `test(api)` — 48 testes de cobertura
3. **PR #121** `feat(0.1+0.2)` — email confirmation + link /i/{code} *(supersede #115, #117, #106, #102, #75)*
4. **PR #109** `feat(0.3)` — analytics de crescimento /admin/analytics/growth
5. **PR #104** `feat(0.4)` — cadastro válido + anti-fraude por IP
6. **PR #113** `feat(1.1)` — Promoções/Achados submit comunitário + curadoria admin
7. **PR #65**  `feat(1.2)` — busca por ZIP + raio geográfico
8. **PR #116** `feat(1.3)` — influencer tier tracking (Parceiro/Embaixador/Hall da Fama)
9. **PR #120** `feat(1.4)` — Empregos — API de vagas com seed manual *(novo desde 2026-09-28)*
10. **PR #68**  `feat(2.1)` — diretório de empresas + assinatura Stripe

Após esses 10, feche os PRs duplicados antigos (não merge):
- Fechar (não mergear): #119, #118, #117, #115, #114, #112, #111, #106, #102, #81, #80, #79, #78, #77, #76, #75, #74, #73, #72, #71, #70, #69, #67, #66

**B) Trabalhar diretamente em `main` sem PR** — Zero atrito de merge, mas sem review humano e sem rollback fácil. Possível se você confiar completamente no agente.
- Pró: produto evolui a cada run
- Contra: vai contra as regras do projeto; sem proteção
- Recomendo NÃO fazer

**C) Parar o agente autônomo até você fazer o merge** — Sem novos PRs. Só manutenção.
- Pró: para de piorar a fila
- Contra: produto não avança

**Minha recomendação:** Opção A. Abrir PR #110 no GitHub → clicar "Merge pull request" → repetir em ordem.
Se precisar de ajuda para resolver conflitos, peça: faço um guia passo a passo.

**Status:** PENDENTE — aguardando decisão do dono

---

### D-002 [2026-09-28] Provider de email para confirmação

**Contexto:**
A feature de confirmação de email (PR #121 / Fase 0.1) está implementada mas precisa de um provider real para funcionar em produção. Em dev, o email é apenas logado.

**Pergunta:** Qual provider de email usar?

**Opções:**
- **Resend** (resend.com) — grátis até 3k emails/mês, API simples, recomendado para startups. Variável: `RESEND_API_KEY`
- **SendGrid** — mais robusto, grátis até 100/dia. Variável: `SENDGRID_API_KEY`
- **SMTP próprio** (Gmail/Zoho/etc) — zero custo, mais configuração. Variáveis: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`

**Recomendação:** Resend — setup em 5 minutos, domínio `clubeusa.com` verificado, custo zero nos primeiros 1.000 usuários.

**Ação necessária:** Criar conta em resend.com, verificar domínio clubeusa.com, gerar API key, adicionar `RESEND_API_KEY` nas variáveis de ambiente do Render/deploy.

**Status:** PENDENTE

---

*Atualizado em: 2026-09-30*
