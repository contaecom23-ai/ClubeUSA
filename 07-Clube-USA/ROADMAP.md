# Clube USA — ROADMAP

> Atualizado: 2026-08-21  
> Legenda: [x] concluido · [~] parcialmente implementado · [ ] pendente

---

## FASE 0 — FUNDACAO (MVP OPERACIONAL)

### 0.1 — Auth WhatsApp OTP
- [~] Registro de membro (nome, telefone, email, idioma, estado, categorias)
- [~] OTP de 6 digitos enviado via Z-API com TTL de 10 minutos
- [~] JWT de 7 dias retornado apos verificacao
- [~] PII criptografado em repouso (phone_hash, phone_enc, email_enc, name_enc)
- [ ] Teste de integracao end-to-end com Z-API real

> Status real: Sistema A (WhatsApp OTP) implementado em `main` e funcional em codigo.
> Pendente: variáveis de ambiente reais (ZAPI_INSTANCE, ZAPI_TOKEN, SUPABASE_URL)
> e deploy em servidor para validação end-to-end.

### 0.2 — Referral Rastreavel
- [x] Codigo unico de indicacao por membro (referral_code)
- [x] Link `/i/{code}` que redireciona para `/?ref={code}` (este PR)
- [x] Frontend captura `?ref=` e passa ao cadastro
- [x] Credito automatico de pontos apos cadastro da indicacao
- [x] Historico de indicacoes via GET /member/referral

### 0.3 — Analytics Basico
- [x] GET /admin/analytics com funil de conversao (este PR)
- [x] Crescimento de membros nos ultimos 30 dias
- [x] Top 10 indicadores por referral_count
- [x] Metricas de engajamento (logins, cliques, indicacoes por periodo)
- [x] Indice em audit_logs para performance das queries
- [ ] Dashboard visual no admin.html consumindo /admin/analytics

---

## FASE 1 — CRESCIMENTO

### 1.1 — Grupos WhatsApp Dinamicos
- [~] GET /public/groups mostra 2 grupos ativos
- [~] Webhook Z-API `/webhook/group` atualiza member_count em tempo real
- [x] client-token verification no webhook (segurança, este PR)
- [ ] Auto-criacao de novo grupo quando todos estao cheios
- [ ] Rotacao automatica de grupos por idioma

### 1.2 — Deal Scanner v2
- [ ] Scanner Amazon com score inteligente
- [ ] Aprovacao de deals pelo admin
- [ ] Envio de deals aprovados para grupos WhatsApp

### 1.3 — Plano VIP (Stripe)
- [ ] Checkout Stripe integrado
- [ ] Webhook de confirmacao de pagamento
- [ ] Ativacao automatica do plano VIP
- [ ] Portal de cancelamento Stripe

---

## FASE 2 — RETENCAO

### 2.1 — Alertas de Preco
- [ ] Alerta por ASIN ou URL Amazon
- [ ] Verificacao periodica de preco
- [ ] Notificacao WhatsApp quando preco atinge meta

### 2.2 — Sorteio VIP
- [ ] Sorteio mensal automatico para membros VIP
- [ ] Notificacao do vencedor via WhatsApp

---

## DECISOES TECNICAS PENDENTES

Ver DECISOES.md para bloqueadores criticos que precisam de resposta do dono.

### Proximo passo sugerido (apos este PR ser mergeado):
1. Merge este PR (`feat/consolida-0.2-0.3-seguranca`) para `main`
2. Configurar variaveis de ambiente reais (SUPABASE_URL, ZAPI_*, STRIPE_*)
3. Deploy em Railway/Fly.io/VPS
4. Testar fluxo end-to-end: cadastro → OTP → login → link de indicacao → analytics
