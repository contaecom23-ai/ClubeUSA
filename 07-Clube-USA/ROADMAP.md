# ROADMAP — Clube USA

> Fonte da verdade do projeto. Marque `[x]` nas tarefas concluidas.

---

## FASE 0 — PRE-LANCAMENTO (base invisivel)

- [x] **0.1** Cadastro + perfil minimo + email confirmado
  - Migration: `db/email_confirmation_migration.sql` (coluna `email_confirmed_at` + tabela `email_tokens`)
  - Service: `services/email_service.py` (SMTP / Resend / dev-console)
  - Router: `api/routers/auth_email.py` — `POST /auth/email/request-confirmation`, `GET /auth/email/confirm/{token}`, `GET /auth/email/status`
  - Wiring em `main.py`: incluir router + trigger pos-cadastro quando email fornecido
  - Tests: `tests/test_auth_email.py` (service + endpoints + isolamento multi-tenant)
  - **Pendente:** configurar provedor de email em producao (ver DECISOES.md)
- [ ] **0.2** Sistema de REFERRAL rastreavel (link unico por pessoa ex: clubeusa.com/i/joao + atribuicao de qual cadastro veio de qual link)
- [ ] **0.3** Analytics basico
- [ ] **0.4** Definicao de "cadastro valido" verificavel (email confirmado + >=1 acao real) + anti-fraude

---

## FASE 1 — TRACAO (foco em UM produto)

- [ ] **1.1** PROMOCOES/ACHADOS = carro-chefe (curadoria, urgencia)
- [ ] **1.2** Busca por ZIP + raio 1-5 milhas
- [ ] **1.3** Programa de influenciadores PAGO POR RESULTADO (pagar por cadastro valido para todos, com teto de orcamento; selos Parceiro 50 / Embaixador 250 / Hall da Fama 1000; opcional bonus mensal pro 1 lugar)
- [ ] **1.4** Empregos (seed manual nas 1as semanas)
- [ ] **1.5** Moradia (quartos/roommates/casas, filtro por ZIP - seed manual)
- [x] **1.6** Rastreador de preco de produto — membro cola o link de um produto (Amazon/Walmart/BestBuy), ve o historico de preco e ofertas cruzadas nos outros marketplaces, cupons verificados automaticamente (Playwright) com selo confirmado/nao confirmado, e recebe alerta quando o preco cai (recheck a cada 6h)

---

## FASE 2 — RECEITA RAPIDA

- [ ] **2.1** Assinatura de empresas locais $10-30/mes (free->premium)
- [ ] **2.2** Diretorio de empresas
- [ ] **2.3** Publicidade local por regiao
- [ ] **2.4** Leilao de destaque por categoria/ZIP

---

## FASE 3 — CONFIANCA E REDE

- [ ] **3.1** Reviews/reputacao
- [ ] **3.2** Ranking comunitario
- [ ] **3.3** Conteudo da comunidade (Q&A, recomendacoes)
- [ ] **3.4** Gamificacao (Contributor, Trusted Member, Community Guide, Verified Helper)

---

## FASE 4 — INTELIGENCIA

- [ ] **4.1** IA CONCIERGE (entende intencao, conecta com empresas)
- [ ] **4.2** Sistema de INTENCAO (mudanca de cidade, seguro, emprego, moradia) = motor de lucro
- [ ] **4.3** Personalizacao nao-sensivel

---

## FASE 5 — MONETIZACAO PESADA

- [ ] **5.1** LEADS (seguros, advogados, dentistas, contractors; lead premium verificado via concierge)
- [ ] **5.2** Servicos financeiros = margem alta (corretagem de seguros, remessas - preferir COMISSAO)
- [ ] **5.3** Produtos proprios

---

## FASE 6 — B2B

- [ ] **6.1** Dados agregados
- [ ] **6.2** Painel de insights por ZIP
- [ ] **6.3** Clientes B2B (seguradoras, bancos, remessas, imobiliarias)

---

*Atualizado em: 2026-08-30*
