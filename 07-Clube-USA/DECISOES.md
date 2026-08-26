# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Claude NÃO age em itens desta lista sem sua aprovação explícita.
> Revise e responda 1x/dia para desbloquear o trabalho.

---

## Como usar

Formato:
```
### [DATA] #ID Título
**Contexto:** ...
**Pergunta:** ...
**Opções:** A / B / C com prós e contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## Decisões Pendentes

### [2026-08-26] #001 — 30 PRs abertas sem merge: o que fazer?

**Contexto:** Há 30 PRs abertas (PRs #3 a #70) que nunca foram mergeadas. Você tem commitado diretamente na main, então essas PRs estão baseadas em versões mais antigas do código e provavelmente têm conflitos. Isso é um débito operacional crescente.

**Pergunta:** O que fazer com o acúmulo de PRs abertas?

**Opções:**
- **A) Fechar todas as PRs antigas, mergear apenas as recentes válidas:** Identificar quais PRs (#70, #61 no mínimo) têm conteúdo relevante que ainda não está no main, resolver conflitos e mergear. Fechar o resto. → Mantém o workflow de PR, limpa a bagunça.
- **B) Fechar todas as PRs e continuar commitando direto na main:** Abandona o modelo de revisão por PR. Mais rápido no curto prazo, mas perde histórico organizado e controle de qualidade.
- **C) Deixar como está:** Acúmulo continua, as PRs viram ruído e perdem valor de documentação.

**Recomendação do Claude:** Opção A. **Mergear imediatamente PR #61** (fix de segurança no webhook Z-API — sem verificação de client-token é uma vulnerabilidade real) e **PR #70** (completa Fase 0.2 referral redirect + Fase 0.3 analytics). Fechar as PRs mais antigas (pré-agosto) que estão baseadas na main antiga. O agente pode ajudar a fechar as antigas se você aprovar.

**Status:** PENDENTE

---

### [2026-08-26] #002 — Auth por WhatsApp vs Email: Fase 0.1 está \"pronta\"?

**Contexto:** O ROADMAP da Fase 0.1 exige \"email confirmado\". Mas a implementação atual usa 100% OTP via WhatsApp (Z-API). Email é coletado mas não verificado. Isso é uma decisão de produto, não técnica.

**Pergunta:** A Fase 0.1 deve ser considerada \"pronta\" com WhatsApp OTP como método de verificação? Ou quer adicionar email também?

**Opções:**
- **A) Manter WhatsApp OTP only (como está):** Mais simples, zero dependência de SMTP/email. Contras: exige que o membro tenha WhatsApp e que Z-API esteja funcionando. Ideal se seu público-alvo é 100% no WhatsApp.
- **B) Adicionar email confirmation via SMTP/Resend:** Mais robusto, funciona sem WhatsApp. Custo de $0-20/mês (Resend tem free tier de 3000 emails/mês). Complexidade adicional de +2 endpoints e template de email.
- **C) Email como fallback:** WhatsApp primeiro, email como opção secundária.

**Recomendação do Claude:** Opção A por agora. Brasileiros imigrantes nos EUA estão 100% no WhatsApp. O risco de Z-API ficar offline é real, mas isso é problema de infra, não de produto. Marcar Fase 0.1 como ✅ com a nota de que \"email confirmado\" virou \"WhatsApp OTP verificado\". Reavaliar se chegar a 1k usuários com reclamações.

**Status:** PENDENTE

---

### [2026-08-26] #003 — Segurança: webhook Z-API sem verificação de token

**Contexto:** O endpoint `POST /webhook/group` recebe eventos de entrada/saída de grupos WhatsApp mas NÃO verifica o `Client-Token` da Z-API. Qualquer pessoa que descobrir a URL pode enviar eventos falsos e manipular `member_count` dos grupos.

**Pergunta:** Autoriza mergear PR #61 (fix de segurança que adiciona verificação do client-token)?

**Opções:**
- **A) Mergear PR #61:** Adiciona verificação `Client-Token` no webhook. Fix cirúrgico, sem impacto funcional se o token estiver configurado no env.
- **B) Ignorar por ora:** Risco baixo no curto prazo (URL não é pública), mas cresce com a visibilidade da plataforma.

**Recomendação do Claude:** Mergear PR #61 imediatamente. É um fix de segurança com risco zero de regressão. A única dependência é ter `ZAPI_CLIENT_TOKEN` no env (que já deve estar se o envio de OTP funciona).

**Status:** PENDENTE

---

*Atualizado em: 2026-08-26 pelo agente autônomo*
