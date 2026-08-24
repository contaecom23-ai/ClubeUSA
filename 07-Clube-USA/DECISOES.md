# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.

---

## ⚠️ SITUAÇÃO ATUAL — 2026-08-24

**26 PRs abertos. Nenhum merge em 14+ dias.**

**VULNERABILIDADE CONFIRMADA EM PRODUÇÃO:** `POST /webhook/group` em `main.py` não verifica o `Client-Token` da Z-API. Qualquer pessoa pode chamar esse endpoint e manipular a contagem de membros nos grupos WhatsApp exibidos no site.

- **Severidade:** Média-baixa (afeta dados cosméticos, não dados de usuários ou pagamentos)
- **Fix pronto:** PR #62 já inclui a verificação — é o **único PR que resolve isso**
- **Ação necessária:** Mergear PR #62

---

## ✅ AÇÃO IMEDIATA — FAÇA ISSO ESTA SEMANA

### Passo 1: Mergear (ordem do menor para maior risco)

| Ordem | PR | O que é | Risco |
|-------|-----|---------|-------|
| 1º | **#62** | Referral redirect + analytics + **fix segurança webhook** | Médio — testar antes |
| 2º | **#56** | CI pytest automático | Muito baixo |
| 3º | **#65** | Busca ZIP (Fase 1.2) | Médio — feature nova |
| 4º | **#58** | Cadastro válido (Fase 0.4) | Médio — checar conflito com #62 |
| 5º | **#63** | Testes de segurança | Baixo |

### Passo 2: Fechar PRs obsoletos (substituídos por versões mais recentes)

Clique "Close pull request" em cada um — o código não se perde, só arquiva:

- **#3** (0.2 referral antigo) → substituído por #62
- **#4** (0.3 analytics antigo) → substituído por #62
- **#5** (0.4 anti-fraude antigo) → substituído por #58
- **#9** (security polish antigo) → substituído por #62
- **#12** (1.1 promoções antigo) → 1.1 já está em main
- **#14** (1.2 ZIP antigo) → substituído por #65
- **#46** (0.1 cadastro antigo) → 0.1 já está em main
- **#51** (fix yaml + docs antigos) → stale
- **#52** (0.2 referral antigo) → substituído por #62
- **#53** (docs 2026-08-17) → stale
- **#57** (fix referral frontend) → substituído por #62
- **#59** (docs 2026-08-19) → stale
- **#60** (docs 2026-08-20) → stale
- **#61** (fix security webhook antigo) → substituído por #62
- **#64** (docs 2026-08-22) → substituído por este PR (#66)

### Passo 3: Decidir sobre PRs restantes

- **#16** (1.3 influenciadores) → revisar e mergear se aprovado
- **#19** (1.4 empregos) → revisar e mergear se aprovado
- **#20** (1.5 moradia) → revisar e mergear se aprovado
- **#54** (email confirmation) → ver Decisão D-002 abaixo

---

## Decisões Pendentes

### [2026-08-23] D-001: Processo de revisão de PRs
**Contexto:** Builder autônomo cria features de qualidade, mas sem revisão do dono nenhuma chega ao main. 14+ dias sem merge gera trabalho que se acumula e perde valor.
**Pergunta:** Como você quer gerenciar o fluxo de revisão daqui pra frente?
**Opções:**
- **A**: Você revisa e merga 1x/semana em horário fixo (ex: sábado de manhã — 30 min)
- **B**: Você autoriza o builder a mergear automaticamente PRs de documentação e testes (sem código de produto)
- **C**: Reduzir builder para 1x/dia com PR menor e mais fácil de revisar
**Recomendação:** Opção A. Reserve 30 minutos toda semana. Sem isso o projeto fica parado independente do que o builder faça.
**Status:** PENDENTE

### [2026-08-23] D-002: PR #54 — confirmação por email vs WhatsApp OTP
**Contexto:** Main usa WhatsApp OTP como único método de auth. PR #54 adiciona confirmação por email. As duas abordagens são compatíveis, mas acrescentam complexidade.
**Pergunta:** Quer adicionar email como alternativa ao WhatsApp OTP?
**Opções:**
- **A**: Manter só WhatsApp OTP — mais simples, adequado para imigrante brasileiro
- **B**: Adicionar email como alternativa (mergear PR #54)
**Recomendação:** Opção A por agora. WhatsApp é o canal principal do público-alvo; email cria atrito extra. Revisar em Fase 1 quando a base de usuários exigir.
**Status:** PENDENTE

---

## Log de runs autônomas

| Data | O que foi feito |
|------|----------------|
| 2026-08-24 | Auditoria profunda de `main.py` vs PR #62: **confirmada vulnerabilidade** em `/webhook/group` (sem verificação de Client-Token Z-API). PR #62 já corrige — é o único PR que fecha essa falha. Nenhum bug adicional encontrado. Nenhuma feature nova criada; criar mais PRs sobre 26 não revisados seria contraproducente. |
| 2026-08-23 | Auditoria de estado completa: leitura de main.py, mapeamento de 25 PRs, ROADMAP + DECISOES atualizados com estado real. Sem feature nova (acumular mais PRs seria contraproducente). |
| 2026-08-22 | PR #64 (docs estado real) + PR #65 (ZIP search Fase 1.2) |
| 2026-08-10 a 2026-08-22 | PRs #56–#63: features acumuladas sem merge |

---

*Atualizado em: 2026-08-24*
