# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> O Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Decisões Pendentes

### [2026-09-23] D-001 — PARALISIA DE PRs: você precisa agir HOJE

**Contexto:**
Existem 30+ PRs abertos no repositório, nenhum foi mergeado desde que o projeto começou. O código está pronto para lançamento mas não vai para produção porque fica em branches. O Claude abre PRs (é a regra), mas não faz merge — isso é responsabilidade sua.

Situação atual no `main`:
- Cadastro + referral básico: ✅ funcionam
- Confirmação de e-mail (0.1): ❌ não implementado ainda — está no PR #106
- URL `/i/{code}` de referral (0.2): ❌ só `?ref=code` — está no PR #100 ou #102
- Analytics básico (0.3): ❌ está no PR #100
- Cadastro válido + anti-fraude (0.4): ❌ está no PR #104
- Testes automatizados: ❌ está no PR #103

**Pergunta:**
Você quer que eu continue abrindo PRs (estratégia atual) ou prefere uma estratégia diferente — por exemplo, escrever os commits diretamente em uma branch que você revisa de forma consolidada?

**O que você precisa fazer AGORA (30 minutos):**

1. **FECHE estes PRs duplicados/obsoletos** (são desnecessários dado os mais recentes):
   - #107 (triage anterior — substituído por este)
   - #101, #99, #95, #91, #89 (outros triages — obsoletos)
   - #98, #87, #85, #84 (email confirmation duplicados — #106 é o mais limpo)
   - #83, #92 (referral/analytics duplicados — #100 é o consolidado)
   - #82 (plano de merge de setembro — obsoleto)

2. **MERGEJE nesta ordem** (são seguros e complementares):
   1. **PR #106** (`feat/fase-0.1-email-confirm-clean`) — confirmação de e-mail. Adiciona apenas 2 endpoints novos + email_service.py. Sem breaking changes. Requer: adicionar colunas `email_enc`, `email_confirmed` na tabela `members` do Supabase (SQL está no PR) + variáveis `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` no .env.
   2. **PR #102** (`feat/0.2-referral-redirect`) — redirect `/i/{code}`. Adiciona 1 endpoint GET. Sem breaking changes.
   3. **PR #103** (`test/api-endpoints-coverage`) — testes. Não afeta produção.
   4. **PR #104** (`feat/fase-0.4-valid-cadastro`) — cadastro válido. Adiciona lógica de validação.
   5. **PR #100** (`consolidado/fase-0.2-0.3`) — analytics. Opcional se #102 já foi mergeado.

3. Os PRs de fases avançadas (#93, #94, #96, #97, #105) podem aguardar — são Fase 1/2 e ainda não são prioridade.

**Por que isso está aqui e não em código:**
Merge de PR só você faz. Configuração de SMTP (email) requer decisão sua sobre qual provedor usar (SendGrid? SES? Gmail App?). São decisões que bloqueiam o código.

**Opções:**

**Opção A — Mergeje os PRs acima (recomendado)**
- Pros: mantém histórico limpo, cada PR tem seu contexto
- Contras: requer ~30min de sua atenção hoje

**Opção B — Estratégia consolidada**
- O Claude para de abrir PRs individuais e escreve tudo em um branch único `dev` que você revisa 1x/semana
- Pros: menos overhead de revisão
- Contras: commits menores desaparecem no histórico

**Opção C — Deploy imediato do que está no main**
- O site atual (main) já funciona com OTP WhatsApp. Você pode lançar AGORA sem confirmação de email.
- O email pode ser adicionado depois do lançamento.
- Pros: lança hoje, valida com usuários reais
- Contras: sem email confirmation (impacta anti-fraude, mas é aceitável para primeiros 100 usuários)

**Recomendação do Claude:**
**Opção C + A em paralelo.** Lança o que está no main HOJE (o produto já funciona). Mergeja os PRs ao longo desta semana. Email confirmation é um nice-to-have para os primeiros 1.000 usuários — a autenticação por WhatsApp já prova o telefone, que é mais forte que email.

**Status:** PENDENTE — aguardando sua decisão

---

### [2026-09-23] D-002 — SMTP para confirmação de e-mail

**Contexto:**
PR #106 implementa confirmação de e-mail mas precisa de um servidor SMTP configurado. Sem isso, o endpoint existe mas não consegue enviar e-mails.

**Pergunta:**
Qual provedor de e-mail transacional você quer usar?

**Opções:**

| Provedor | Custo (início) | Limite gratuito | Recomendação |
|----------|---------------|-----------------|--------------|
| **Resend** | $0 | 3.000/mês | ✅ Melhor DX, API simples |
| **SendGrid** | $0 | 100/dia | Bom mas API mais complexa |
| **AWS SES** | $0.10/1.000 | 62.000/mês se no EC2 | Barato mas configuração trabalhosa |
| **Gmail SMTP** | $0 | 500/dia | Só para testes, não para produção |

**Recomendação:** Resend — cria conta em resend.com, gera API key, coloca como `RESEND_API_KEY` no .env do Render.

**Status:** PENDENTE — depende da D-001

---

*Atualizado em: 2026-09-23*
