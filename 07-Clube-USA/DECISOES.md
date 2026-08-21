# Clube USA — Decisoes e Bloqueadores

> Atualizado: 2026-08-21

---

## BLOQUEADOR CRITICO #1 — Sistema A vs Sistema B

**Status: AGUARDANDO DECISAO DO DONO**

Existem dois sistemas backend paralelos:

- **Sistema A** (branch `main`): autenticacao via WhatsApp OTP (Z-API). Este e o sistema que esta sendo desenvolvido neste PR e em todos os PRs de feature.
- **Sistema B** (PR #46, nunca mergeado): autenticacao via email/senha. Criado em algum momento, mas nunca integrado.

**Recomendacao tecnica:** Manter Sistema A (WhatsApp OTP). Razoes:
1. Alinhado com o produto (Clube USA e distribuido via WhatsApp)
2. Menor fricao para o usuario (sem senha para lembrar)
3. Ja esta em `main` e e a base de todos os outros PRs abertos
4. PR #46 nunca foi mergeado — indica que o proprio dono preferiu nao mesclar

**Acao necessaria:** Dono confirma que Sistema A e o correto → fechar PR #46 como obsoleto.

---

## BLOQUEADOR #2 — 21+ PRs Sem Merge (Divida Organizacional)

**Status: URGENTE**

Existem 21+ PRs abertos com 0 merges no repositorio. Isso significa:
- Todo o codigo de feature esta em branches nao integradas
- `main` esta desatualizado em relacao ao que foi desenvolvido
- Risco de conflitos crescendo a cada novo PR

**Recomendacao:** Revisar e mergear PRs em ordem de dependencia:
1. Este PR (`feat/consolida-0.2-0.3-seguranca`) — consolida 0.2 + 0.3 + seguranca, sem conflitos com main
2. Fechar PR #46 (Sistema B — obsoleto)
3. Avaliar demais PRs um a um

---

## BLOQUEADOR #3 — Variaveis de Ambiente Nao Configuradas

**Status: BLOQUEANTE PARA PRODUCAO**

O backend System A requer estas variaveis para funcionar em producao:

```
SUPABASE_URL=           # URL do projeto Supabase
SUPABASE_SERVICE_KEY=   # Chave service_role do Supabase (nunca expor no client)
SECRET_KEY=             # Chave JWT (gerar com: python -c "import secrets; print(secrets.token_hex(32))")
ZAPI_INSTANCE=          # ID da instancia Z-API
ZAPI_TOKEN=             # Token da instancia Z-API
ZAPI_CLIENT_TOKEN=      # Client-token para verificacao de webhook Z-API
STRIPE_SECRET_KEY=      # Chave secreta Stripe (sk_live_...)
STRIPE_WEBHOOK_SECRET=  # Segredo do webhook Stripe (whsec_...)
STRIPE_VIP_PRICE_ID=    # ID do preco VIP no Stripe (price_...)
APP_URL=                # URL publica do app (ex: https://clubeusa.com)
```

**Acao necessaria:** Configurar estas variaveis no ambiente de deploy (Railway, Fly.io, VPS, etc).

---

## BLOQUEADOR #4 — Ambiente de Deploy Nao Definido

**Status: PENDENTE**

Nao foi definido onde o backend sera hospedado. Opcoes avaliadas:

| Opcao | Custo | Complexidade | Recomendacao |
|-------|-------|-------------|-------------|
| Railway | $5-20/mes | Baixa | **Recomendado para MVP** |
| Fly.io | $3-15/mes | Media | Boa alternativa |
| VPS (DigitalOcean/Hetzner) | $6-12/mes | Alta | Para escala futura |
| Render | $7/mes | Baixa | Alternativa Railway |

**Recomendacao para MVP:** Railway — deploy com um comando, variaveis de ambiente na UI, sem configurar Nginx/Docker manualmente.

---

## DECISOES JA TOMADAS

| Data | Decisao | Motivo |
|------|---------|--------|
| 2026-08-21 | Consolidar PRs 0.2 + 0.3 + seguranca em 1 PR | Reduzir carga de revisao do dono |
| 2026-08-21 | Manter System A (WhatsApp OTP) como canonical | Alinhado com produto e ja em main |
| 2026-08-21 | Referral link formato `/i/{code}` (redirect server-side) | SEO friendly, codigo nao exposto na URL final |
| 2026-08-21 | Analytics usa tabelas existentes (audit_logs, members, referrals, clicks) | Sem migrations destrutivas |
| 2026-08-21 | Webhook Z-API: verificar client-token, retornar 200 mesmo em rejeicao | Evitar retry storm da Z-API |
